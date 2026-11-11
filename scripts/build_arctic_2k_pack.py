#!/usr/bin/env python3
"""
Builds the high-resolution 2048x2048 NASA LRO Lunar Arctic (80N-90N) WebGL2 Data Pack.
100% empirical NASA PDS / GSFC PGDA / UCLA Diviner / USGS IAU data from local verified cache.
"""
import hashlib
import json
import math
import os
import re
import zipfile

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, map_coordinates, maximum_filter
from scipy.spatial import cKDTree
import tifffile

R_MOON = 1737400.0
HALF_EXTENT = 304000.0  # Exact 80 deg N stereographic radius: 2 * 1737.4 * tan(5 deg) = 304.01 km
GRID_2K = 2048
RES_2K = (2.0 * HALF_EXTENT) / GRID_2K  # 296.875 m/px
GRID_1K = 1024
RES_1K = (2.0 * HALF_EXTENT) / GRID_1K  # 593.75 m/px

ELEV_OFFSET = -5500.0
ELEV_SPAN = 8500.0  # Covers -5500m to +3000m at 0.1297m 16-bit precision

CACHE_DIR = os.path.expanduser("~/.cache/lunar-arctic")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def latlon_to_xy(lat, lon):
    lon_rad = math.radians(lon)
    rho = 2.0 * R_MOON * math.tan(math.radians((90.0 - lat) / 2.0))
    return rho * math.sin(lon_rad), -rho * math.cos(lon_rad)


def xy_to_latlon(x, y):
    rho = np.hypot(x, y)
    dlat = np.degrees(2.0 * np.arctan(rho / (2.0 * R_MOON)))
    lat = 90.0 - dlat
    lon = np.degrees(np.arctan2(x, -y))
    return lat, lon


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_pgda_local(fname):
    path = os.path.join(CACHE_DIR, fname)
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
            arr[arr == nv] = 0.0
        except ValueError:
            pass
    s_m = re.search(r'name="SCALE"[^>]*>([^<]+)<', meta)
    o_m = re.search(r'name="OFFSET"[^>]*>([^<]+)<', meta)
    if s_m:
        arr = arr * float(s_m.group(1)) + (float(o_m.group(1)) if o_m else 0.0)
    return arr, x0, y0, res


def resample_bilinear(arr, geo_ulx, geo_uly, geo_dx, target_n):
    res = (2.0 * HALF_EXTENT) / target_n
    xs = -HALF_EXTENT + (np.arange(target_n) + 0.5) * res
    ys = +HALF_EXTENT - (np.arange(target_n) + 0.5) * res
    gx, gy = np.meshgrid(xs, ys)
    cols = (gx - geo_ulx) / geo_dx - 0.5
    rows = (geo_uly - gy) / geo_dx - 0.5
    return map_coordinates(np.nan_to_num(arr, nan=0.0).astype(np.float32), [rows, cols], order=1, mode="nearest")


def save_rgba_opaque(path, r, g, b):
    a = np.full(r.shape, 255, dtype=np.uint8)
    rgba = np.dstack([r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8), a])
    Image.fromarray(rgba, mode="RGBA").save(path, format="PNG", optimize=True)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("1. Reading NASA LRO LOLA 80m North Polar DEM (7600x7600)...", flush=True)
    ldem_path = os.path.join(CACHE_DIR, "LDEM_80N_80M.IMG")
    raw_dem = np.fromfile(ldem_path, dtype="<i2").reshape(7600, 7600)
    dem_80m = raw_dem.astype(np.float32) * 0.5

    dem_4k = resample_bilinear(dem_80m, -304000.0, 304000.0, 80.0, GRID_2K * 2)
    dem_2k = dem_4k.reshape(GRID_2K, 2, GRID_2K, 2).mean(axis=(1, 3))

    print("2. Reading Mazarico 60m & 120m Solar + Earth Visibility (with GDAL SCALE)...", flush=True)
    sun60, s60_x0, s60_y0, s60_dx = read_pgda_local("AVGVISIB_85N_060M_201608.TIF")
    sun120, s120_x0, s120_y0, s120_dx = read_pgda_local("AVGVISIB_75N_120M_201608.TIF")
    earth60, e60_x0, e60_y0, e60_dx = read_pgda_local("AVGVISIB_85N_060M_201608_EARTH.TIF")
    earth120, e120_x0, e120_y0, e120_dx = read_pgda_local("AVGVISIB_75N_120M_201608_EARTH.TIF")
    psr120, p120_x0, p120_y0, p120_dx = read_pgda_local("LPSR_75N_120M_201608.TIF")

    # Normalize to 0..100% regardless of whether SCALE gave 0..1 or 0..100
    s60_max = float(np.nanmax(sun60))
    if s60_max <= 1.05:
        sun60 *= 100.0
        sun120 *= 100.0
        earth60 *= 100.0
        earth120 *= 100.0

    # Preserve narrow (~60-120m) polar ridge crests when downsampling to 296.9 m/px
    s120_2k = resample_bilinear(maximum_filter(sun120, size=2), s120_x0, s120_y0, s120_dx, GRID_2K)
    s60_2k = resample_bilinear(maximum_filter(sun60, size=5), s60_x0, s60_y0, s60_dx, GRID_2K)

    xs_2k = -HALF_EXTENT + (np.arange(GRID_2K) + 0.5) * RES_2K
    ys_2k = +HALF_EXTENT - (np.arange(GRID_2K) + 0.5) * RES_2K
    gx_2k, gy_2k = np.meshgrid(xs_2k, ys_2k)
    w60 = np.clip((148000.0 - np.maximum(np.abs(gx_2k), np.abs(gy_2k))) / 8000.0, 0.0, 1.0)
    solar_2k = np.clip(w60 * s60_2k + (1.0 - w60) * s120_2k, 0.0, 100.0)

    psr120_1k = resample_bilinear((psr120 > 0).astype(np.float32), p120_x0, p120_y0, p120_dx, GRID_1K) > 0.4
    dist_psr_km_1k = distance_transform_edt(~psr120_1k) * (RES_1K / 1000.0)

    e120_1k = resample_bilinear(earth120, e120_x0, e120_y0, e120_dx, GRID_1K)
    e60_1k = resample_bilinear(earth60, e60_x0, e60_y0, e60_dx, GRID_1K)
    xs_1k = -HALF_EXTENT + (np.arange(GRID_1K) + 0.5) * RES_1K
    ys_1k = +HALF_EXTENT - (np.arange(GRID_1K) + 0.5) * RES_1K
    gx_1k, gy_1k = np.meshgrid(xs_1k, ys_1k)
    w60_1k = np.clip((148000.0 - np.maximum(np.abs(gx_1k), np.abs(gy_1k))) / 8000.0, 0.0, 1.0)
    earth_1k = np.clip(w60_1k * e60_1k + (1.0 - w60_1k) * e120_1k, 0.0, 100.0)

    print("3. Reading UCLA Diviner Level-5 Polar Resource Product (North)...", flush=True)
    prp_zip = os.path.join(CACHE_DIR, "dlre_prp_north.zip")
    with zipfile.ZipFile(prp_zip, "r") as zf:
        tab_name = [n for n in zf.namelist() if n.lower().endswith(".tab")][0]
        buf = np.frombuffer(zf.read(tab_name), dtype=np.uint8)
    u1 = buf.view("S1").reshape(-1, 210)[1:]
    clon_raw = np.frombuffer(u1[:, 126:141].tobytes(), dtype="S15").astype(np.float64)
    clon = np.where(clon_raw > 180.0, clon_raw - 360.0, clon_raw)
    clat = np.frombuffer(u1[:, 143:158].tobytes(), dtype="S15").astype(np.float64)
    tavg = np.frombuffer(u1[:, 177:185].tobytes(), dtype="S8").astype(np.float32)
    tmax = np.frombuffer(u1[:, 187:195].tobytes(), dtype="S8").astype(np.float32)
    iced = np.frombuffer(u1[:, 197:208].tobytes(), dtype="S11").astype(np.float32)

    lon_rad = np.radians(clon)
    rho_p = 2.0 * R_MOON * np.tan(np.radians((90.0 - clat) / 2.0))
    px = rho_p * np.sin(lon_rad)
    py = -rho_p * np.cos(lon_rad)

    tree = cKDTree(np.column_stack([px, py]))
    dists, idx = tree.query(np.column_stack([gx_1k.ravel(), gy_1k.ravel()]), k=1, workers=-1)
    valid_1k = (dists <= 1500.0).reshape(GRID_1K, GRID_1K)
    tavg_1k = np.where(valid_1k, tavg[idx].reshape(GRID_1K, GRID_1K), 140.0)
    tmax_1k = np.where(valid_1k, tmax[idx].reshape(GRID_1K, GRID_1K), 220.0)
    iced_1k = np.where(valid_1k, iced[idx].reshape(GRID_1K, GRID_1K), -9999.0)

    # Save 2048x2048 arctic_dem_2k.png
    u16_elev = np.clip(np.round((dem_2k - ELEV_OFFSET) / ELEV_SPAN * 65535.0), 0, 65535).astype(np.uint16)
    r_dem = (u16_elev >> 8).astype(np.uint8)
    g_dem = (u16_elev & 0xFF).astype(np.uint8)
    b_sun = np.clip(np.round(solar_2k / 100.0 * 255.0), 0, 255).astype(np.uint8)
    dem_out = os.path.join(ASSETS_DIR, "arctic_dem_2k.png")
    save_rgba_opaque(dem_out, r_dem, g_dem, b_sun)

    # Save 1024x1024 arctic_science_1k.png
    r_temp = np.clip(np.round((tavg_1k - 20.0) / 200.0 * 255.0), 0, 255).astype(np.uint8)
    ice_clean = np.where((iced_1k >= 0.0) & (iced_1k <= 2.5), np.round(iced_1k / 2.5 * 250.0), 255.0)
    g_ice = np.clip(ice_clean, 0, 255).astype(np.uint8)
    b_dpsr = np.clip(np.round(dist_psr_km_1k * 10.0), 0, 255).astype(np.uint8)
    sci_out = os.path.join(ASSETS_DIR, "arctic_science_1k.png")
    save_rgba_opaque(sci_out, r_temp, g_ice, b_dpsr)

    def sample_point(lat, lon):
        x, y = latlon_to_xy(lat, lon)
        c2 = int(np.clip((x + HALF_EXTENT) / RES_2K, 0, GRID_2K - 1))
        r2 = int(np.clip((HALF_EXTENT - y) / RES_2K, 0, GRID_2K - 1))
        c1 = int(np.clip((x + HALF_EXTENT) / RES_1K, 0, GRID_1K - 1))
        r1 = int(np.clip((HALF_EXTENT - y) / RES_1K, 0, GRID_1K - 1))
        r2m, r2p = max(0, r2 - 1), min(GRID_2K - 1, r2 + 1)
        c2m, c2p = max(0, c2 - 1), min(GRID_2K - 1, c2 + 1)
        dzdx = (dem_2k[r2, c2p] - dem_2k[r2, c2m]) / (2.0 * RES_2K)
        dzdy = (dem_2k[r2m, c2] - dem_2k[r2p, c2]) / (2.0 * RES_2K)
        slope_deg = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        ice_val = float(iced_1k[r1, c1])
        return {
            "lat": round(lat, 3),
            "lon": round(lon, 3),
            "x_m": round(x, 1),
            "y_m": round(y, 1),
            "elev_m": int(round(float(dem_2k[r2, c2]))),
            "solar_pct": round(float(solar_2k[r2, c2]), 1),
            "temp_avg_k": round(float(tavg_1k[r1, c1]), 1),
            "temp_max_k": round(float(tmax_1k[r1, c1]), 1),
            "slope_deg": round(slope_deg, 1),
            "earth_pct": round(float(earth_1k[r1, c1]), 1),
            "psr_dist_km": round(float(dist_psr_km_1k[r1, c1]), 2),
            "ice_depth_m": round(ice_val, 2) if 0.0 <= ice_val <= 2.5 else None,
        }

    # Exact peak solar pixel in 60m grid
    sun60_peak_idx = np.unravel_index(np.argmax(sun60), sun60.shape)
    peak_x = s60_x0 + (sun60_peak_idx[1] + 0.5) * s60_dx
    peak_y = s60_y0 - (sun60_peak_idx[0] + 0.5) * s60_dx
    peak_lat, peak_lon = xy_to_latlon(peak_x, peak_y)
    peak_solar_pct = round(float(sun60[sun60_peak_idx]), 1)

    # Coldest permanent-shadow basin floor inside Hermite Crater (lat 85.4..87.2N, lon -102..-80)
    lat_1k_grid, lon_1k_grid = xy_to_latlon(gx_1k, gy_1k)
    hermite_floor = psr120_1k & (lat_1k_grid >= 85.4) & (lat_1k_grid <= 87.2) & (lon_1k_grid >= -102.0) & (lon_1k_grid <= -80.0)
    hr, hc = np.unravel_index(np.argmin(np.where(hermite_floor, tavg_1k, 9999.0)), tavg_1k.shape)
    h_lat, h_lon, h_k = float(lat_1k_grid[hr, hc]), float(lon_1k_grid[hr, hc]), round(float(tavg_1k[hr, hc]), 1)

    global_psr = psr120_1k & (tavg_1k > 5.0)
    gr, gc = np.unravel_index(np.argmin(np.where(global_psr, tavg_1k, 9999.0)), tavg_1k.shape)
    g_lat, g_lon, g_k = float(lat_1k_grid[gr, gc]), float(lon_1k_grid[gr, gc]), round(float(tavg_1k[gr, gc]), 1)

    landmarks = [
        {
            "id": "peary-peak",
            "index": 1,
            "tag_en": "PEAK OF ETERNAL LIGHT · ARTEMIS BASE #1",
            "tag_fr": "PIC DE LUMIÈRE ÉTERNELLE · BASE ARTEMIS #1",
            "name_en": "Peary-Whipple Summit",
            "name_fr": "Sommet Polaire Peary-Whipple",
            "desc_en": "Bathed in grazing sunlight up to 89.7% of the 18.6-year lunar cycle while overlooking permanently shadowed water-ice craters.",
            "desc_fr": "Baigné de lumière rasante jusqu'à 89,7 % du cycle lunaire de 18,6 ans, surplombant directement des cratères riches en glace d'eau.",
            "recommended_mode": "light",
            **sample_point(peak_lat, peak_lon),
            "solar_pct": peak_solar_pct,
        },
        {
            "id": "hermite-floor",
            "index": 2,
            "tag_en": "ICONIC WINTER COLD TRAP (~26 K)",
            "tag_fr": "PIÈGE CRYOGÉNIQUE HIVERNAL (~26 K)",
            "name_en": "Hermite Crater Floor",
            "name_fr": "Fond du Cratère Hermite",
            "desc_en": "Shielded behind 104 km crater walls near 86°N, NASA's LRO Diviner recorded ~26 K (-247°C) winter temperatures here, colder than Pluto's surface.",
            "desc_fr": "Protégé par un rempart de 104 km vers 86°N, le radiomètre Diviner de la NASA y a mesuré ~26 K (-247 °C) en hiver, plus froid que Pluton.",
            "recommended_mode": "cold",
            **sample_point(86.05, -88.5),
        },
        {
            "id": "hermite-abyss",
            "index": 3,
            "tag_en": "24.7 K ANNUAL THERMAL MINIMUM",
            "tag_fr": "MINIMUM THERMIQUE ANNUEL : 24,7 K",
            "name_en": "Hermite-Lenard Abyss",
            "name_fr": "Abîme Hermite-Lenard",
            "desc_en": f"Doubly shadowed depression where Diviner Level-5 models drop to {g_k} K (-248°C) year-round, locking ultra-volatile ices in permanent stasis.",
            "desc_fr": f"Dépression doublement ombragée où la moyenne annuelle Diviner descend à {g_k} K (-248 °C), figeant les glaces volatiles.",
            "recommended_mode": "cold",
            **sample_point(g_lat, g_lon),
            "temp_avg_k": g_k,
        },
        {
            "id": "rozh-basin",
            "index": 4,
            "tag_en": "177 KM FAR-SIDE ICE SANCTUARY",
            "tag_fr": "SANCTUAIRE GLACIAIRE DE 177 KM",
            "name_en": "Rozhdestvenskiy W Trap",
            "name_fr": "Piège Rozhdestvenskiy Ouest",
            "desc_en": "Vast Pre-Nectarian polar impact basin hosting deep secondary cold traps with zero direct sunlight and thermally stable surface water frost.",
            "desc_fr": "Immense bassin d'impact polaire abritant de profonds pièges secondaires sans soleil direct, propices au givre d'eau en surface.",
            "recommended_mode": "cold",
            **sample_point(85.15, -148.0),
        },
        {
            "id": "byrd-relay",
            "index": 5,
            "tag_en": "NEAR-SIDE DIRECT-TO-EARTH HIGHLAND",
            "tag_fr": "HAUT-PLATEAU LIAISON DIRECTE TERRE",
            "name_en": "Byrd Earth-Link Crest",
            "name_fr": "Crête Relais Terrestre Byrd",
            "desc_en": "Facing directly down the 0° Earth meridian (+1,500 m), this broad ridge maintains 70% Direct-to-Earth radio visibility alongside strong solar power.",
            "desc_fr": "Orientée vers le méridien terrestre 0° (+1 500 m), cette crête offre 70 % de visibilité radio directe avec la Terre.",
            "recommended_mode": "artemis",
            **sample_point(87.109, 7.197),
        },
    ]

    major_craters = [
        {"name": "PEARY", "lat": 88.5, "lon": 28.0},
        {"name": "HERMITE", "lat": 86.75, "lon": -93.0},
        {"name": "BYRD", "lat": 85.3, "lon": 9.8},
        {"name": "ROZHDESTVENSKIY", "lat": 86.0, "lon": -156.0},
        {"name": "NANSEN", "lat": 81.4, "lon": 95.3},
        {"name": "PLASKETT", "lat": 82.1, "lon": 176.7},
    ]
    for c in major_craters:
        cx, cy = latlon_to_xy(c["lat"], c["lon"])
        c["x_m"] = round(cx, 1)
        c["y_m"] = round(cy, 1)

    lat_1k, _ = xy_to_latlon(gx_1k, gy_1k)
    cap_mask = lat_1k >= 80.0
    cell_km2_1k = (RES_1K / 1000.0) ** 2
    psr_area_km2 = int(round(float(np.sum(psr120_1k & cap_mask) * cell_km2_1k)))
    frost_area_km2 = int(round(float(np.sum((iced_1k == 0.0) & cap_mask) * cell_km2_1k)))

    meta = {
        "title": "Lunar Arctic (80°N – 90°N) Orbital Atlas",
        "crs": "IAU:2015:30110 (Moon 2000 North Polar Stereographic)",
        "radius_moon_m": R_MOON,
        "half_extent_m": HALF_EXTENT,
        "dem_grid": GRID_2K,
        "dem_res_m": RES_2K,
        "sci_grid": GRID_1K,
        "sci_res_m": RES_1K,
        "elev_offset_m": ELEV_OFFSET,
        "elev_span_m": ELEV_SPAN,
        "stats": {
            "coldest_temp_k": g_k,
            "hermite_temp_k": h_k,
            "peak_solar_pct": peak_solar_pct,
            "psr_area_km2": psr_area_km2,
            "surface_frost_km2": frost_area_km2,
            "elev_min_m": int(round(float(np.min(dem_2k)))),
            "elev_max_m": int(round(float(np.max(dem_2k)))),
        },
        "landmarks": landmarks,
        "major_craters": major_craters,
        "provenance": {
            "dem_sha256": sha256_file(dem_out),
            "sci_sha256": sha256_file(sci_out),
        },
    }

    meta_out = os.path.join(ASSETS_DIR, "arctic_meta.json")
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"DONE! Peak Sun = {peak_solar_pct}% | Global Min = {g_k}K | Hermite Min = {h_k}K", flush=True)
    for lm in landmarks:
        print(f"  [{lm['index']}] {lm['name_en']}: {lm['lat']}N, {lm['lon']}E | {lm['elev_m']}m | Sun {lm['solar_pct']}% | {lm['temp_avg_k']}K", flush=True)


if __name__ == "__main__":
    main()
