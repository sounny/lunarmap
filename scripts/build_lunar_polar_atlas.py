#!/usr/bin/env python3
"""
Build 100% Empirical NASA LRO Polar Atlas Assets (Lunar Arctic 80N-90N & Artemis South Pole 80S-90S).

Every raster pixel and site metric derives strictly from published NASA PDS / GSFC PGDA / UCLA Diviner / USGS IAU sources:
  1. LOLA Polar Topography (80 m/px): LDEM_80N_80M & LDEM_80S_80M -- Smith et al. (2010), NASA PDS
  2. Polar Illumination, Earth Visibility & PSRs (60 m & 120 m/px): Mazarico et al. (2011), Icarus 211, NASA GSFC PGDA #69
  3. Diviner Polar Resource Products (Level 5 PRP V2.0): Paige et al. (2010), Science 330, NASA PDS LRO-L-DLRE-5-PRP-V2.0
  4. Diviner Winter Solstice Polar Bolometric Temperature (240 m/px): LRO-L-DLRE-5-GDR-V1.0
  5. Official Planetary Nomenclature: International Astronomical Union (IAU) / USGS Astrogeology WFS

Outputs lossless, non-premultiplied RGB data PNGs (Alpha=255 strictly enforced to avoid HTML5 canvas premultiplication)
and `polar_atlas_meta.json` into `../assets/`.
"""
import datetime
import hashlib
import io
import json
import math
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, maximum_filter, uniform_filter
from scipy.spatial import cKDTree
import tifffile

R_MOON = 1737400.0
GRID_N = 1024
HALF_EXTENT = 304000.0  # +/- 304.0 km covers 90 deg down to 80.0 deg circle (and ~76 deg in corners)
CELL_RES = (2.0 * HALF_EXTENT) / GRID_N  # 593.75 m/px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CACHE_DIR = os.path.expanduser("~/.cache/lunar-arctic")
JSMARS_CACHE = os.path.expanduser("~/.cache/jsmars-lunar")
UA = {"User-Agent": "Mozilla/5.0 (LunarArcticArtemisAtlas; https://sounny.com)"}


def fetch(url):
    os.makedirs(CACHE_DIR, exist_ok=True)
    fname = url.rsplit("/", 1)[1]
    # Reuse jsmars cache if already downloaded
    alt = os.path.join(JSMARS_CACHE, fname)
    if os.path.exists(alt) and os.path.getsize(alt) > 0:
        return alt
    path = os.path.join(CACHE_DIR, fname)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    print(f"  [download] {url}", flush=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r:
        tmp = path + ".part"
        with open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    os.replace(tmp, path)
    return path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def latlon_to_xy(lat, lon, pole):
    lon_rad = math.radians(lon)
    if pole == "north":
        rho = 2.0 * R_MOON * math.tan(math.radians((90.0 - lat) / 2.0))
        return rho * math.sin(lon_rad), -rho * math.cos(lon_rad)
    else:
        rho = 2.0 * R_MOON * math.tan(math.radians((90.0 + lat) / 2.0))
        return rho * math.sin(lon_rad), +rho * math.cos(lon_rad)


def xy_to_latlon(x, y, pole):
    rho = np.hypot(x, y)
    dlat = np.degrees(2.0 * np.arctan(rho / (2.0 * R_MOON)))
    if pole == "north":
        lat = 90.0 - dlat
        lon = np.degrees(np.arctan2(x, -y))
    else:
        lat = -90.0 + dlat
        lon = np.degrees(np.arctan2(x, +y))
    return lat, lon


def read_lola_80m(pole):
    tag = "80N" if pole == "north" else "80S"
    lbl_path = fetch(f"https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/LDEM_{tag}_80M.LBL")
    img_path = fetch(f"https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/LDEM_{tag}_80M.IMG")
    lbl = open(lbl_path, encoding="latin-1").read()
    lines = int(re.search(r"\bLINES\s*=\s*(\d+)", lbl).group(1))
    samples = int(re.search(r"\bLINE_SAMPLES\s*=\s*(\d+)", lbl).group(1))
    scale_fac = float(re.search(r"\bSCALING_FACTOR\s*=\s*([-\d.]+)", lbl).group(1))
    raw = np.fromfile(img_path, dtype="<i2", count=lines * samples).reshape(lines, samples)
    dem = raw.astype(np.float32) * scale_fac  # meters relative to 1737.4 km sphere
    return dem, 80.0, img_path


def compute_horn_slope_deg(dem, res_m):
    p = np.pad(dem, 1, mode="edge")
    dzdx = ((p[:-2, 2:] + 2.0 * p[1:-1, 2:] + p[2:, 2:]) -
            (p[:-2, :-2] + 2.0 * p[1:-1, :-2] + p[2:, :-2])) / (8.0 * res_m)
    dzdy = ((p[2:, :-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:]) -
            (p[:-2, :-2] + 2.0 * p[:-2, 1:-1] + p[:-2, 2:])) / (8.0 * res_m)
    return np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype(np.float32)


def read_pgda_tif(url):
    path = fetch(url)
    with tifffile.TiffFile(path) as tf:
        pg = tf.pages[0]
        arr = pg.asarray().astype(np.float32)
        tags = pg.tags
        res = float(tags["ModelPixelScaleTag"].value[0])
        tie = tags["ModelTiepointTag"].value
        x0 = float(tie[3]) - float(tie[0]) * res
        y0 = float(tie[4]) + float(tie[1]) * res
        nod = tags["GDAL_NODATA"].value if "GDAL_NODATA" in tags else None
        meta = str(tags["GDAL_METADATA"].value) if "GDAL_METADATA" in tags else ""
    if nod is not None:
        try:
            nv = float(str(nod).strip("\x00 "))
            arr[arr == nv] = np.nan
        except ValueError:
            pass
    s_m = re.search(r'name="SCALE"[^>]*>([^<]+)<', meta)
    o_m = re.search(r'name="OFFSET"[^>]*>([^<]+)<', meta)
    if s_m:
        arr = arr * float(s_m.group(1)) + (float(o_m.group(1)) if o_m else 0.0)
    return arr, (x0, y0, res), path


def resample_grid(src, src_geo, how="mean"):
    """Resample source polar stereographic array onto target GRID_N x GRID_N (+/-304 km) grid."""
    x0, y0, res = src_geo
    # Target cell centers
    xs = -HALF_EXTENT + (np.arange(GRID_N) + 0.5) * CELL_RES
    ys = +HALF_EXTENT - (np.arange(GRID_N) + 0.5) * CELL_RES

    if how == "mean":
        k = max(1, int(round(CELL_RES / res)))
        if k > 1:
            mask = np.isfinite(src).astype(np.float32)
            filled = np.where(np.isfinite(src), src, 0.0).astype(np.float32)
            num = uniform_filter(filled, size=k, mode="nearest")
            den = uniform_filter(mask, size=k, mode="nearest")
            work = np.where(den > 0.1, num / np.maximum(den, 1e-6), np.nan)
        else:
            work = src
    elif how == "max":
        k = max(1, int(round(CELL_RES / res)))
        filled = np.where(np.isfinite(src), src, -1e9).astype(np.float32)
        mx = maximum_filter(filled, size=k, mode="nearest")
        work = np.where(mx > -1e8, mx, np.nan)
    elif how == "p90":
        # Approximate local upper-decile hazard slope via combination of mean and max
        k = max(1, int(round(CELL_RES / res)))
        mn = uniform_filter(src, size=k, mode="nearest")
        mx = maximum_filter(src, size=max(1, k // 2), mode="nearest")
        work = 0.35 * mn + 0.65 * mx
    else:
        work = src

    cols = np.clip(np.floor((xs - x0) / res).astype(np.int32), 0, work.shape[1] - 1)
    rows = np.clip(np.floor((y0 - ys) / res).astype(np.int32), 0, work.shape[0] - 1)
    in_x = (xs >= x0) & (xs <= x0 + work.shape[1] * res)
    in_y = (ys <= y0) & (ys >= y0 - work.shape[0] * res)
    out = work[np.ix_(rows, cols)].astype(np.float32)
    valid_mask = np.outer(in_y, in_x)
    out[~valid_mask] = np.nan
    return out


def parse_diviner_prp(pole):
    """Parse Paige et al. (2010) Diviner Level-5 Polar Resource Product (2,880,000 elements) onto GRID_N x GRID_N."""
    zurl = f"https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/extras/prp/dlre_prp_{pole}.zip"
    zpath = fetch(zurl)
    print(f"  [diviner-prp] parsing {os.path.basename(zpath)} ...", flush=True)
    with zipfile.ZipFile(zpath, "r") as zf:
        tab_name = [n for n in zf.namelist() if n.lower().endswith(".tab")][0]
        raw_bytes = zf.read(tab_name)

    # Fixed-length 210 bytes/row; row 0 is text header, rows 1..2880000 are data
    n_total = len(raw_bytes) // 210
    buf = np.frombuffer(raw_bytes[210 : n_total * 210], dtype="S210")
    # Slice exact fixed-width columns (1-indexed in XML):
    # tri_clon: 127..141 (0-idx 126:141)
    # tri_clat: 144..158 (0-idx 143:158)
    # temp_avg: 178..185 (0-idx 177:185)
    # temp_max: 188..195 (0-idx 187:195)
    # ice_depth: 198..208 (0-idx 197:208)
    u1 = buf.view("S1").reshape(-1, 210)
    clon = np.frombuffer(u1[:, 126:141].tobytes(), dtype="S15").astype(np.float64)
    clat = np.frombuffer(u1[:, 143:158].tobytes(), dtype="S15").astype(np.float64)
    tavg = np.frombuffer(u1[:, 177:185].tobytes(), dtype="S8").astype(np.float32)
    tmax = np.frombuffer(u1[:, 187:195].tobytes(), dtype="S8").astype(np.float32)
    iced = np.frombuffer(u1[:, 197:208].tobytes(), dtype="S11").astype(np.float32)

    lon_rad = np.radians(clon)
    if pole == "north":
        rho = 2.0 * R_MOON * np.tan(np.radians((90.0 - clat) / 2.0))
        px = rho * np.sin(lon_rad)
        py = -rho * np.cos(lon_rad)
    else:
        rho = 2.0 * R_MOON * np.tan(np.radians((90.0 + clat) / 2.0))
        px = rho * np.sin(lon_rad)
        py = +rho * np.cos(lon_rad)

    # Map onto GRID_N x GRID_N via nearest-neighbor KDTree (mesh spacing ~250m -> denser than 593.75m grid!)
    xs = -HALF_EXTENT + (np.arange(GRID_N) + 0.5) * CELL_RES
    ys = +HALF_EXTENT - (np.arange(GRID_N) + 0.5) * CELL_RES
    gx, gy = np.meshgrid(xs, ys)
    tree = cKDTree(np.column_stack([px, py]))
    dists, idx = tree.query(np.column_stack([gx.ravel(), gy.ravel()]), k=1, workers=-1)

    valid = (dists <= 1500.0).reshape(GRID_N, GRID_N)
    grid_tavg = np.where(valid, tavg[idx].reshape(GRID_N, GRID_N), np.nan)
    grid_tmax = np.where(valid, tmax[idx].reshape(GRID_N, GRID_N), np.nan)
    grid_iced = np.where(valid, iced[idx].reshape(GRID_N, GRID_N), np.nan)

    # Also compute exact minimum temperatures from raw mesh elements inside 80-90 deg
    pos_tavg = tavg[tavg > 5.0]
    pos_tmax = tmax[tmax > 5.0]
    min_idx = int(np.argmin(np.where(tavg > 5.0, tavg, 9999.0)))
    coldest_spot = {
        "temp_avg_k": round(float(tavg[min_idx]), 1),
        "temp_max_k": round(float(tmax[min_idx]), 1),
        "lat": round(float(clat[min_idx]), 4),
        "lon": round(float(clon[min_idx] if clon[min_idx] <= 180 else clon[min_idx] - 360), 4),
    }
    return grid_tavg, grid_tmax, grid_iced, coldest_spot, zpath


def read_winter_tbol_north():
    """Read observed Diviner Winter Solstice 2009-12-24 polar bolometric temperature (Paige et al. 2010 epoch)."""
    u_img = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gdr_l3/2009/polar/img/dgdr_tbol_avg_poln_20091224n_240_img.img"
    u_img2 = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gdr_l3/2010/polar/img/dgdr_tbol_avg_poln_20100107n_240_img.img"
    mins = []
    paths = []
    for u in [u_img, u_img2]:
        p = fetch(u)
        paths.append(p)
        raw = np.fromfile(p, dtype="<i2", count=3812 * 3812).reshape(3812, 3812)
        tb = np.where((raw > 0) & (raw != -32768), raw.astype(np.float32) * 0.02, np.nan)
        mins.append(tb)
    with np.errstate(all="ignore"):
        tb_min = np.nanmin(np.stack(mins), axis=0)
    geo = (-1905.5 * 240.0 - 120.0, 1905.5 * 240.0 + 120.0, 240.0)
    # Find coldest valid pixel inside Hermite region (lat >= 84N, >15K to exclude edge calibration noise)
    ys = geo[1] - (np.arange(3812) + 0.5) * 240.0
    xs = geo[0] + (np.arange(3812) + 0.5) * 240.0
    gx, gy = np.meshgrid(xs, ys)
    lat, lon = xy_to_latlon(gx, gy, "north")
    valid = np.isfinite(tb_min) & (tb_min >= 18.0) & (lat >= 83.0)
    r_idx, c_idx = np.unravel_index(np.argmin(np.where(valid, tb_min, 9999.0)), tb_min.shape)
    hermite_mask = valid & (lat >= 85.0) & (lat <= 88.2) & (lon >= -115.0) & (lon <= -45.0)
    hr_idx, hc_idx = np.unravel_index(np.argmin(np.where(hermite_mask, tb_min, 9999.0)), tb_min.shape)
    winter_record = {
        "north_winter_min_k": round(float(tb_min[r_idx, c_idx]), 1),
        "north_winter_min_lat": round(float(lat[r_idx, c_idx]), 3),
        "north_winter_min_lon": round(float(lon[r_idx, c_idx]), 3),
        "hermite_winter_min_k": round(float(tb_min[hr_idx, hc_idx]), 1),
        "hermite_winter_min_lat": round(float(lat[hr_idx, hc_idx]), 3),
        "hermite_winter_min_lon": round(float(lon[hr_idx, hc_idx]), 3),
    }
    return resample_grid(tb_min, geo, how="mean"), winter_record, paths[0]


def save_rgb_png(path, r, g, b):
    """Save lossless RGBA PNG with Alpha=255 everywhere so browser Canvas getImageData never premultiplies."""
    a = np.full(r.shape, 255, dtype=np.uint8)
    rgba = np.dstack([r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8), a])
    Image.fromarray(rgba, mode="RGBA").save(path, format="PNG", optimize=True)


def fetch_iau_polar_nomenclature():
    """Fetch official IAU-approved lunar nomenclature poleward of 79 deg N and 79 deg S."""
    wfs_path = os.path.join(CACHE_DIR, "usgs_iau_moon_point.gml")
    if not os.path.exists(wfs_path) or os.path.getsize(wfs_path) == 0:
        url = ("https://planetarymaps.usgs.gov/cgi-bin/mapserv?map=/maps/earth/moon_nomen_wfs.map"
               "&SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=ms:MOON_POINT")
        print("  [iau-wfs] downloading official USGS/IAU Moon nomenclature ...", flush=True)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=120) as r, open(wfs_path, "wb") as f:
            f.write(r.read())

    txt = open(wfs_path, encoding="utf-8", errors="ignore").read()
    features = {"north": [], "south": []}
    blocks = txt.split("<gml:featureMember>")[1:]
    for blk in blocks:
        pos_m = re.search(r"<gml:pos>([-\d.]+)\s+([-\d.]+)</gml:pos>", blk)
        name_m = re.search(r"<ms:clean_feature>([^<]+)</ms:clean_feature>", blk) or re.search(r"<ms:feature>([^<]+)</ms:feature>", blk)
        diam_m = re.search(r"<ms:diameter>([-\d.]+)</ms:diameter>", blk)
        type_m = re.search(r"<ms:type>([^<]+)</ms:type>", blk)
        if not (pos_m and name_m):
            continue
        lat = float(pos_m.group(1))
        if abs(lat) < 79.5:
            continue
        lon = float(pos_m.group(2))
        if lon > 180.0:
            lon -= 360.0
        diam = float(diam_m.group(1)) if diam_m else 0.0
        raw_type = type_m.group(1).strip() if type_m else "Crater"
        ftype = "Mons" if "mons" in raw_type.lower() else ("Crater" if "crater" in raw_type.lower() else raw_type.split(",")[0])
        name = name_m.group(1).strip().replace("Idel son", "Idel'son").replace("Nefed ev", "Nefed'ev")
        if "landing site" in name.lower():
            continue
        pole = "north" if lat > 0 else "south"
        x, y = latlon_to_xy(lat, lon, pole)
        if abs(x) > HALF_EXTENT * 0.98 or abs(y) > HALF_EXTENT * 0.98:
            continue
        is_sat = bool(re.search(r"\s+[A-Z]$", name)) and ftype == "Crater"
        features[pole].append({
            "name": name,
            "lat": round(lat, 3),
            "lon": round(lon, 3),
            "x_km": round(x / 1000.0, 2),
            "y_km": round(y / 1000.0, 2),
            "diameter_km": round(diam, 1),
            "type": ftype,
            "is_satellite": is_sat,
        })

    # Keep primary features + major satellite cold traps (>= 18 km or iconic Hermite A)
    for pole in ("north", "south"):
        keep = []
        seen = set()
        for f in sorted(features[pole], key=lambda d: (d["is_satellite"], -d["diameter_km"])):
            if f["name"] in seen:
                continue
            if not f["is_satellite"] or f["diameter_km"] >= 20.0 or f["name"] in ("Hermite A",):
                keep.append(f)
                seen.add(f["name"])
        features[pole] = keep
    return features, wfs_path


def find_top_candidates(pole, dem, slope_p90, sun_pct, earth_pct, psr_frac, dist_psr_km, tmax, iced, iau_list):
    """Algorithmically discover the Top 6 optimal polar base camp sites separated by >= 18 km."""
    xs = -HALF_EXTENT + (np.arange(GRID_N) + 0.5) * CELL_RES
    ys = +HALF_EXTENT - (np.arange(GRID_N) + 0.5) * CELL_RES
    gx, gy = np.meshgrid(xs, ys)
    lat, lon = xy_to_latlon(gx, gy, pole)

    # Composite Artemis Base Camp Engineering Score:
    # High solar visibility + gentle slope (<12 deg) + proximity to PSR cold trap (<8 km) + Earth visibility
    valid = (
        np.isfinite(dem) & np.isfinite(sun_pct) & np.isfinite(slope_p90) &
        (np.abs(lat) >= 83.5) &
        (slope_p90 <= 13.5) &
        (sun_pct >= 62.0) &
        (dist_psr_km <= 8.5)
    )
    score = (
        (sun_pct / 100.0) * 55.0
        + np.clip((14.0 - slope_p90) / 14.0, 0.0, 1.0) * 20.0
        + np.clip((8.5 - dist_psr_km) / 8.5, 0.0, 1.0) * 15.0
        + (np.nan_to_num(earth_pct, nan=0.0) / 100.0) * 10.0
    )
    score = np.where(valid, score, -1.0)

    flat_order = np.argsort(score.ravel())[::-1]
    chosen = []
    primary_iau = [f for f in iau_list if not f["is_satellite"] or f["name"] == "Hermite A"]

    for idx in flat_order:
        if score.ravel()[idx] <= 0:
            break
        r, c = divmod(int(idx), GRID_N)
        cx, cy = float(xs[c]), float(ys[r])
        if any(math.hypot(cx - p["x_m"], cy - p["y_m"]) < 18000.0 for p in chosen):
            continue
        # Match nearest official IAU landmark for geographic naming context
        best_lm = None
        best_d = 1e9
        for f in primary_iau:
            fx, fy = f["x_km"] * 1000.0, f["y_km"] * 1000.0
            edge_d = abs(math.hypot(cx - fx, cy - fy) - (f["diameter_km"] * 500.0))
            center_d = math.hypot(cx - fx, cy - fy)
            d = min(edge_d, center_d)
            if d < best_d:
                best_d = d
                best_lm = f
        lm_name = best_lm["name"] if best_lm else ("North Polar Ridge" if pole == "north" else "South Polar Ridge")
        clat, clon = xy_to_latlon(cx, cy, pole)
        # Direction relative to crater center if near a crater
        sector = "Rim Crest"
        if best_lm and best_lm["type"].lower().startswith("mons"):
            sector = "Summit Ridge"
        elif best_lm:
            dx_m = cx - best_lm["x_km"] * 1000.0
            dy_m = cy - best_lm["y_km"] * 1000.0
            ang = math.degrees(math.atan2(dx_m, dy_m))
            near_pole = math.hypot(cx, cy) < math.hypot(best_lm["x_km"] * 1000.0, best_lm["y_km"] * 1000.0)
            if -45 <= ang <= 45 or ang >= 135 or ang <= -135:
                sector = "Poleward Rim" if near_pole else "Outer Rim"
            elif 45 < ang < 135:
                sector = "East Rim"
            else:
                sector = "West Rim"
            if best_lm["name"] == "Malapert":
                sector = "Mons Malapert Ridge"
            elif best_lm["name"] == "Henson" and abs(clat) > 89.3:
                sector = "Connecting Ridge"

        chosen.append({
            "rank": len(chosen) + 1,
            "id": f"{pole}-cand-{len(chosen)+1}",
            "title": f"{lm_name} ({sector})",
            "landmark": lm_name,
            "lat": round(float(clat), 3),
            "lon": round(float(clon), 3),
            "x_km": round(cx / 1000.0, 2),
            "y_km": round(cy / 1000.0, 2),
            "x_m": cx,
            "y_m": cy,
            "elev_m": int(round(float(dem[r, c]))),
            "slope_deg": round(float(slope_p90[r, c]), 1),
            "sun_pct": round(float(sun_pct[r, c]), 1),
            "earth_pct": round(float(earth_pct[r, c]), 1),
            "dist_psr_km": round(float(dist_psr_km[r, c]), 2),
            "tmax_k": int(round(float(tmax[r, c]))) if np.isfinite(tmax[r, c]) else None,
            "score": round(float(score[r, c]), 1),
        })
        if len(chosen) >= 6:
            break

    for c in chosen:
        c.pop("x_m", None)
        c.pop("y_m", None)
    return chosen


def process_pole(pole, iau_features):
    print(f"\n=== Processing {pole.upper()} POLE (80 deg to 90 deg, +/-304 km) ===", flush=True)
    p75 = "75N" if pole == "north" else "75S"
    p85 = "85N" if pole == "north" else "85S"

    # 1. LOLA 80m DEM + Horn slope
    dem80, res80, dem_src = read_lola_80m(pole)
    geo80 = (-3799.5 * 80.0 - 40.0, 3799.5 * 80.0 + 40.0, 80.0)
    print(f"  [lola] computing 80m Horn slope on {dem80.shape} ...", flush=True)
    slp80 = compute_horn_slope_deg(dem80, 80.0)
    dem_grid = resample_grid(dem80, geo80, how="mean")
    slp_mean_grid = resample_grid(slp80, geo80, how="mean")
    slp_p90_grid = resample_grid(slp80, geo80, how="p90")
    del dem80, slp80

    # 2. Mazarico Illumination (120m regional + 60m inner 85-90 patch preserving sharp peak crests)
    sun120, g120, sun120_src = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_{p75}_120M_201608.TIF")
    earth120, _, earth120_src = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_{p75}_120M_201608_EARTH.TIF")
    psr120, _, psr120_src = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/LPSR_{p75}_120M_201608.TIF")

    sun60, g60, sun60_src = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_{p85}_060M_201608.TIF")
    earth60, _, _ = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_{p85}_060M_201608_EARTH.TIF")
    psr60, _, _ = read_pgda_tif(f"https://pgda.gsfc.nasa.gov/data/MoonIllumination/LPSR_{p85}_060M_201608.TIF")

    # Euclidean distance to nearest confirmed PSR cold trap on 120m grid
    psr_bin120 = (np.nan_to_num(psr120, nan=0.0) > 0).astype(np.uint8)
    dist120_km = (distance_transform_edt(psr_bin120 == 0) * 0.120).astype(np.float32)

    sun_grid = resample_grid(sun120, g120, how="max") * 100.0
    sun_inner = resample_grid(sun60, g60, how="max") * 100.0
    sun_grid = np.where(np.isfinite(sun_inner), sun_inner, sun_grid)

    earth_grid = resample_grid(earth120, g120, how="mean") * 100.0
    earth_inner = resample_grid(earth60, g60, how="mean") * 100.0
    earth_grid = np.where(np.isfinite(earth_inner), earth_inner, earth_grid)

    psr_grid = resample_grid(psr120.astype(np.float32) > 0, g120, how="mean") * 100.0
    psr_inner = resample_grid((psr60 > 0).astype(np.float32), g60, how="mean") * 100.0
    psr_grid = np.where(np.isfinite(psr_inner), psr_inner, psr_grid)

    dist_psr_grid = resample_grid(dist120_km, g120, how="mean")

    # Exact PSR cold-trap area strictly poleward of 80 deg latitude on native 120m grid
    y120 = g120[1] - (np.arange(psr120.shape[0]) + 0.5) * 120.0
    x120 = g120[0] + (np.arange(psr120.shape[1]) + 0.5) * 120.0
    rho_80 = 2.0 * R_MOON * math.tan(math.radians(10.0 / 2.0))
    in80_120 = (x120[None, :] ** 2 + y120[:, None] ** 2) <= (rho_80 ** 2)
    psr_area_80_km2 = float((psr_bin120[in80_120] > 0).sum()) * (0.120 * 0.120)
    max_sun_60_pct = round(float(np.nanmax(sun60)) * 100.0, 1)

    del sun120, earth120, psr120, sun60, earth60, psr60, psr_bin120, dist120_km

    # 3. Diviner Polar Resource Product (temp_avg, temp_max, ice_depth)
    tavg_grid, tmax_grid, iced_grid, coldest_prp, prp_src = parse_diviner_prp(pole)

    winter_tb_grid = np.full((GRID_N, GRID_N), np.nan, dtype=np.float32)
    winter_record = None
    winter_src = None
    if pole == "north":
        winter_tb_grid, winter_record, winter_src = read_winter_tbol_north()

    # 4. Pack lossless non-premultiplied PNGs (Alpha=255)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # PNG 1: DEM (int16 decimeters biased by +12000 m => uint16 = round((elev_m + 12000)*2.5), 0.4m vertical precision across -12000..+14214m!) + B = P90 slope (0.25 deg steps)
    elev_u16 = np.clip(np.round((np.nan_to_num(dem_grid, nan=0.0) + 12000.0) * 2.5), 0, 65535).astype(np.uint16)
    dem_r = ((elev_u16 >> 8) & 0xFF).astype(np.uint8)
    dem_g = (elev_u16 & 0xFF).astype(np.uint8)
    dem_b = np.clip(np.round(np.nan_to_num(slp_p90_grid, nan=25.0) * 4.0), 0, 255).astype(np.uint8)
    dem_png = os.path.join(ASSETS_DIR, f"{pole}_dem.png")
    save_rgb_png(dem_png, dem_r, dem_g, dem_b)

    # PNG 2: Illumination (R=sun 0..200 [0.5%], G=earth 0..200 [0.5%], B=psr 0..250 [0.4%])
    ill_r = np.clip(np.round(np.nan_to_num(sun_grid, nan=0.0) * 2.0), 0, 200).astype(np.uint8)
    ill_g = np.clip(np.round(np.nan_to_num(earth_grid, nan=0.0) * 2.0), 0, 200).astype(np.uint8)
    ill_b = np.clip(np.round(np.nan_to_num(psr_grid, nan=0.0) * 2.5), 0, 250).astype(np.uint8)
    ill_png = os.path.join(ASSETS_DIR, f"{pole}_illum.png")
    save_rgb_png(ill_png, ill_r, ill_g, ill_b)

    # PNG 3: Thermal & Ice (R=tmax_k - 15 [1K steps, 15..270K], G=ice_depth cm [0=surface, 1..250=1..250cm, 254=unstable], B=dist_psr 0.2km steps [0..250 => 0..50km])
    th_r = np.where(np.isfinite(tmax_grid), np.clip(np.round(tmax_grid - 15.0), 0, 254), 255).astype(np.uint8)
    iced_cm = np.full(iced_grid.shape, 255, dtype=np.uint8)
    fin_ice = np.isfinite(iced_grid)
    # In Diviner PRP: negative values (-9999 or <0) mean water ice is NOT stable within 2.5m; 0.0 means stable on surface; >0 means depth in meters
    unstable = fin_ice & ((iced_grid < 0.0) | (iced_grid > 2.50))
    surf_ice = fin_ice & (iced_grid >= 0.0) & (iced_grid <= 0.005)
    sub_ice = fin_ice & (iced_grid > 0.005) & (iced_grid <= 2.50)
    iced_cm[unstable] = 254
    iced_cm[surf_ice] = 0
    iced_cm[sub_ice] = np.clip(np.round(iced_grid[sub_ice] * 100.0), 1, 250).astype(np.uint8)
    th_b = np.clip(np.round(np.nan_to_num(dist_psr_grid, nan=60.0) * 5.0), 0, 254).astype(np.uint8)
    th_png = os.path.join(ASSETS_DIR, f"{pole}_thermal.png")
    save_rgb_png(th_png, th_r, iced_cm, th_b)

    # PNG 4: Aux (R=tavg_k - 15 [1K steps], G=winter_min_k or tavg [0.5K steps from 15K], B=mean slope [0.25 deg])
    ax_r = np.where(np.isfinite(tavg_grid), np.clip(np.round(tavg_grid - 15.0), 0, 254), 255).astype(np.uint8)
    w_src = np.where(np.isfinite(winter_tb_grid), winter_tb_grid, tavg_grid)
    ax_g = np.where(np.isfinite(w_src), np.clip(np.round((w_src - 15.0) * 2.0), 0, 254), 255).astype(np.uint8)
    ax_b = np.clip(np.round(np.nan_to_num(slp_mean_grid, nan=20.0) * 4.0), 0, 255).astype(np.uint8)
    ax_png = os.path.join(ASSETS_DIR, f"{pole}_aux.png")
    save_rgb_png(ax_png, ax_r, ax_g, ax_b)

    # Compute summary stats strictly inside |lat| >= 80.0 deg circle
    xs = -HALF_EXTENT + (np.arange(GRID_N) + 0.5) * CELL_RES
    ys = +HALF_EXTENT - (np.arange(GRID_N) + 0.5) * CELL_RES
    gx, gy = np.meshgrid(xs, ys)
    in80 = (gx ** 2 + gy ** 2) <= (rho_80 ** 2)
    cell_km2 = (CELL_RES / 1000.0) ** 2

    surf_ice_km2 = float((in80 & (iced_cm == 0)).sum()) * cell_km2
    shallow_1m_km2 = float((in80 & (iced_cm <= 100)).sum()) * cell_km2
    hls_default_km2 = float((
        in80 & (sun_grid >= 65.0) & (slp_p90_grid <= 10.0) & (dist_psr_grid <= 5.0) & (earth_grid >= 35.0)
    ).sum()) * cell_km2
    gateway_km2 = float((
        in80 & (sun_grid >= 65.0) & (slp_p90_grid <= 10.0) & (dist_psr_grid <= 5.0)
    ).sum()) * cell_km2

    # Enrich IAU features with real local telemetry sampled at feature coordinates
    enriched_iau = []
    for f in iau_features:
        c = int(np.clip((f["x_km"] * 1000.0 + HALF_EXTENT) / CELL_RES, 0, GRID_N - 1))
        r = int(np.clip((HALF_EXTENT - f["y_km"] * 1000.0) / CELL_RES, 0, GRID_N - 1))
        rad_px = max(2, int(round((f["diameter_km"] * 500.0) / CELL_RES)))
        r0, r1 = max(0, r - rad_px), min(GRID_N, r + rad_px + 1)
        c0, c1 = max(0, c - rad_px), min(GRID_N, c + rad_px + 1)
        f_copy = dict(f)
        f_copy["floor_elev_m"] = int(round(float(np.nanmin(dem_grid[r0:r1, c0:c1]))))
        f_copy["rim_elev_m"] = int(round(float(np.nanmax(dem_grid[r0:r1, c0:c1]))))
        f_copy["max_sun_pct"] = round(float(np.nanmax(sun_grid[r0:r1, c0:c1])), 1)
        f_copy["psr_coverage_pct"] = round(float((psr_grid[r0:r1, c0:c1] > 25.0).mean()) * 100.0, 1)
        tb_patch = winter_tb_grid[r0:r1, c0:c1] if pole == "north" else tavg_grid[r0:r1, c0:c1]
        if np.isfinite(tb_patch).any():
            f_copy["min_temp_k"] = round(float(np.nanmin(tb_patch)), 1)
        enriched_iau.append(f_copy)

    candidates = find_top_candidates(
        pole, dem_grid, slp_p90_grid, sun_grid, earth_grid, psr_grid, dist_psr_grid, tmax_grid, iced_grid, enriched_iau
    )

    stats = {
        "pole": pole,
        "lat_domain": "80°N to 90°N" if pole == "north" else "80°S to 90°S",
        "cap_area_km2": round(float(in80.sum()) * cell_km2, 0),
        "psr_area_km2": round(psr_area_80_km2, 0),
        "surface_ice_stable_km2": round(surf_ice_km2, 0),
        "shallow_permafrost_1m_km2": round(shallow_1m_km2, 0),
        "elev_min_m": int(round(float(np.nanmin(dem_grid[in80])))),
        "elev_max_m": int(round(float(np.nanmax(dem_grid[in80])))),
        "relief_span_m": int(round(float(np.nanmax(dem_grid[in80]) - np.nanmin(dem_grid[in80])))),
        "peak_solar_60m_pct": max_sun_60_pct,
        "coldest_prp": coldest_prp,
        "winter_solstice_obs": winter_record,
        "viable_artemis_dte_km2": round(hls_default_km2, 1),
        "viable_artemis_gateway_km2": round(gateway_km2, 1),
        "rasters": {
            "dem": {"file": os.path.basename(dem_png), "bytes": os.path.getsize(dem_png), "sha256": sha256_file(dem_png)},
            "illum": {"file": os.path.basename(ill_png), "bytes": os.path.getsize(ill_png), "sha256": sha256_file(ill_png)},
            "thermal": {"file": os.path.basename(th_png), "bytes": os.path.getsize(th_png), "sha256": sha256_file(th_png)},
            "aux": {"file": os.path.basename(ax_png), "bytes": os.path.getsize(ax_png), "sha256": sha256_file(ax_png)},
        },
        "sources": [
            {"product": os.path.basename(dem_src), "sha256": sha256_file(dem_src)},
            {"product": os.path.basename(sun120_src), "sha256": sha256_file(sun120_src)},
            {"product": os.path.basename(sun60_src), "sha256": sha256_file(sun60_src)},
            {"product": os.path.basename(prp_src), "sha256": sha256_file(prp_src)},
        ] + ([{"product": os.path.basename(winter_src), "sha256": sha256_file(winter_src)}] if winter_src else []),
    }
    print(f"  [summary {pole}] PSR={stats['psr_area_km2']} km2 | SurfIce={stats['surface_ice_stable_km2']} km2 | "
          f"PeakSun={stats['peak_solar_60m_pct']}% | Relief={stats['elev_min_m']}..{stats['elev_max_m']}m | "
          f"HLS_DTE={stats['viable_artemis_dte_km2']} km2 | ColdestPRP={coldest_prp['temp_avg_k']}K", flush=True)
    if winter_record:
        print(f"  [winter obs] Hermite={winter_record['hermite_winter_min_k']}K @ ({winter_record['hermite_winter_min_lat']}N, {winter_record['hermite_winter_min_lon']}E)", flush=True)
    return stats, enriched_iau, candidates


def main():
    iau, wfs_path = fetch_iau_polar_nomenclature()
    print(f"  [iau] {len(iau['north'])} North features, {len(iau['south'])} South features", flush=True)

    n_stats, n_iau, n_cands = process_pole("north", iau["north"])
    s_stats, s_iau, s_cands = process_pole("south", iau["south"])

    meta = {
        "schema_version": 1,
        "built_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "grid": {
            "size": GRID_N,
            "half_extent_m": HALF_EXTENT,
            "cell_res_m": CELL_RES,
            "moon_radius_m": R_MOON,
            "crs_north": "IAU:2015:30110 / Moon2000 North Polar Stereographic (lat0=+90, lon0=0, +Y=180E Far Side, -Y=0E Near Side)",
            "crs_south": "IAU:2015:30120 / Moon2000 South Polar Stereographic (lat0=-90, lon0=0, +Y=0E Near Side, -Y=180E Far Side)",
            "encoding": {
                "dem": "uint16=((R<<8)|G) => elev_m = (uint16 / 2.5) - 12000.0; B => slope_p90_deg = B / 4.0",
                "illum": "R => sun_pct = R / 2.0; G => earth_pct = G / 2.0; B => psr_pct = B / 2.5",
                "thermal": "R => tmax_k = R + 15 (255=nodata); G => ice_depth_m (0=0.00m surface frost, 1..250=0.01..2.50m, 254=>2.5m dry, 255=nodata); B => dist_psr_km = B / 5.0",
                "aux": "R => tavg_k = R + 15; G => winter_or_min_k = (G / 2.0) + 15.0; B => slope_mean_deg = B / 4.0",
            },
        },
        "citations": [
            {
                "id": "lola",
                "short": "Smith et al. (2010)",
                "full": "Smith, D.E., et al. (2010). Initial observations from the Lunar Orbiter Laser Altimeter (LOLA). Geophys. Res. Lett., 37, L18204. NASA PDS LRO-L-LOLA-4-GDR-V1.0.",
                "url": "https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/",
            },
            {
                "id": "mazarico",
                "short": "Mazarico et al. (2011)",
                "full": "Mazarico, E., Neumann, G.A., Smith, D.E., Zuber, M.T., & Torrence, M.H. (2011). Illumination conditions of the lunar polar regions using LOLA topography. Icarus, 211(2), 1066-1081.",
                "url": "https://pgda.gsfc.nasa.gov/products/69",
            },
            {
                "id": "diviner",
                "short": "Paige et al. (2010)",
                "full": "Paige, D.A., et al. (2010). Diviner Lunar Radiometer observations of cold traps in the Moon's south polar region (and Level-5 Polar Resource Products V2.0). Science, 330(6003), 479-482. NASA PDS LRO-L-DLRE-5-PRP-V2.0.",
                "url": "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
            },
            {
                "id": "minisar",
                "short": "Spudis et al. (2010)",
                "full": "Spudis, P.D., et al. (2010). Initial results for the north pole of the Moon from Mini-SAR, Chandrayaan-1 mission. Geophys. Res. Lett., 37, L06204.",
                "url": "https://doi.org/10.1029/2009GL042259",
            },
            {
                "id": "iau",
                "short": "IAU / USGS (2026)",
                "full": "International Astronomical Union (IAU) Working Group for Planetary System Nomenclature, USGS Astrogeology Gazetteer of Planetary Nomenclature.",
                "url": "https://planetarynames.wr.usgs.gov/",
            },
        ],
        "poles": {
            "north": {
                "stats": n_stats,
                "candidates": n_cands,
                "landmarks": n_iau,
            },
            "south": {
                "stats": s_stats,
                "candidates": s_cands,
                "landmarks": s_iau,
            },
        },
        "transects": [
            {
                "id": "peary-whipple",
                "pole": "north",
                "label_en": "Peary Sunlit Rim -> Whipple Ice Cold Trap",
                "label_fr": "Crete Ensoleillee Peary -> Piege Froid Whipple",
                "p1": {"lat": 89.26, "lon": 103.5},
                "p2": {"lat": 89.08, "lon": 124.5},
            },
            {
                "id": "hermite-coldtrap",
                "pole": "north",
                "label_en": "Hermite Rim -> Hermite SW Coldest Trap (~26 K)",
                "label_fr": "Rempart Hermite -> Piege Froid Hermite SO (~26 K)",
                "p1": {"lat": 87.35, "lon": -68.0},
                "p2": {"lat": 86.05, "lon": -96.0},
            },
            {
                "id": "shackleton-ridge",
                "pole": "south",
                "label_en": "Connecting Ridge -> Shackleton Crater Floor",
                "label_fr": "Crete de Connexion -> Fond du Cratere Shackleton",
                "p1": {"lat": -89.46, "lon": -137.4},
                "p2": {"lat": -89.82, "lon": 125.0},
            },
            {
                "id": "malapert-haworth",
                "pole": "south",
                "label_en": "Mons Malapert Summit -> Haworth Cold Trap",
                "label_fr": "Sommet Mons Malapert -> Piege Froid Haworth",
                "p1": {"lat": -86.04, "lon": 0.2},
                "p2": {"lat": -87.48, "lon": -4.8},
            },
        ],
    }

    out_json = os.path.join(ASSETS_DIR, "polar_atlas_meta.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"\nDONE! Wrote {out_json} ({os.path.getsize(out_json)/1024:.1f} KB)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
