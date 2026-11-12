#!/usr/bin/env python3
"""
Builds the Dual-Pole (North 80N-90N & South 80S-90S) NASA LRO Lunar Polar Atlas WebGL2 Data Pack.
100% empirical NASA PDS LOLA, NASA GSFC PGDA Product #69, UCLA Diviner Level-5 PRP V2.0, and USGS/IAU Gazetteer data.
"""
import hashlib
import json
import math
import os
import re
import zipfile

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import distance_transform_edt, map_coordinates
from scipy.spatial import cKDTree
import tifffile

R_MOON = 1737400.0
HALF_EXTENT = 304000.0  # 80 deg polar stereographic radius: 2 * 1737.4 * tan(5 deg) = 304.005 km
GRID_2K = 2048
RES_2K = (2.0 * HALF_EXTENT) / GRID_2K  # 296.875 m/px
GRID_1K = 1024
RES_1K = (2.0 * HALF_EXTENT) / GRID_1K  # 593.75 m/px

CACHE_N = os.path.expanduser("~/.cache/lunar-arctic")
CACHE_S = os.path.expanduser("~/.cache/jsmars-lunar")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def latlon_to_xy(lat, lon, hemi):
    """
    hemi = +1 for North Polar Stereographic (IAU_2015:30130: 0E at -Y bottom, 90E at +X right)
    hemi = -1 for South Polar Stereographic (IAU_2015:30135: 0E at +Y top,    90E at +X right)
    """
    lon_rad = math.radians(lon)
    rho = 2.0 * R_MOON * math.tan(math.radians((90.0 - hemi * lat) / 2.0))
    return rho * math.sin(lon_rad), -hemi * rho * math.cos(lon_rad)


def xy_to_latlon(x, y, hemi):
    rho = np.hypot(x, y)
    dlat = np.degrees(2.0 * np.arctan(rho / (2.0 * R_MOON)))
    lat = hemi * (90.0 - dlat)
    lon = np.degrees(np.arctan2(x, -hemi * y))
    return lat, lon


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_pgda_tif(path):
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


def resample_cell_max(arr, geo_ulx, geo_uly, geo_dx, target_n, sub=5):
    """Exact sub-pixel maximum strictly inside each target pixel footprint (zero cross-pixel halo)."""
    res = (2.0 * HALF_EXTENT) / target_n
    offs = (np.arange(sub) + 0.5) / sub - 0.5
    xs_base = -HALF_EXTENT + (np.arange(target_n) + 0.5) * res
    ys_base = +HALF_EXTENT - (np.arange(target_n) + 0.5) * res
    out = np.full((target_n, target_n), -1e9, dtype=np.float32)
    clean = np.nan_to_num(arr, nan=0.0).astype(np.float32)
    h, w = clean.shape
    for oy in offs:
        rows = np.clip(np.floor((geo_uly - (ys_base + oy * res)) / geo_dx).astype(np.int32), 0, h - 1)
        for ox in offs:
            cols = np.clip(np.floor(((xs_base + ox * res) - geo_ulx) / geo_dx).astype(np.int32), 0, w - 1)
            out = np.maximum(out, clean[np.ix_(rows, cols)])
    return out


def save_rgba_opaque(path, r, g, b):
    a = np.full(r.shape, 255, dtype=np.uint8)
    rgba = np.dstack([r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8), a])
    Image.fromarray(rgba, mode="RGBA").save(path, format="PNG", optimize=True)


def build_pole(
    pole_key,
    hemi,
    crs_label,
    elev_offset,
    elev_span,
    ldem_path,
    sun60_path,
    sun120_path,
    earth60_path,
    earth120_path,
    psr120_path,
    prp_zip_path,
    landmark_defs,
    crater_defs,
):
    print(f"\n=== Building {pole_key.upper()} Pole ({crs_label}) ===", flush=True)
    raw_dem = np.fromfile(ldem_path, dtype="<i2").reshape(7600, 7600)
    dem_80m = raw_dem.astype(np.float32) * 0.5

    dem_4k = resample_bilinear(dem_80m, -304000.0, 304000.0, 80.0, GRID_2K * 2)
    dem_2k = dem_4k.reshape(GRID_2K, 2, GRID_2K, 2).mean(axis=(1, 3))
    dem_1k = dem_2k.reshape(GRID_1K, 2, GRID_1K, 2).mean(axis=(1, 3))

    # Verify zero elevation clipping
    assert dem_2k.min() > elev_offset + 50.0, f"{pole_key} min elev {dem_2k.min()} clips {elev_offset}"
    assert dem_2k.max() < elev_offset + elev_span - 50.0, f"{pole_key} max elev {dem_2k.max()} clips {elev_offset + elev_span}"

    sun60, s60_x0, s60_y0, s60_dx = read_pgda_tif(sun60_path)
    sun120, s120_x0, s120_y0, s120_dx = read_pgda_tif(sun120_path)
    earth60, e60_x0, e60_y0, e60_dx = read_pgda_tif(earth60_path)
    earth120, e120_x0, e120_y0, e120_dx = read_pgda_tif(earth120_path)
    psr120, p120_x0, p120_y0, p120_dx = read_pgda_tif(psr120_path)

    if float(np.nanmax(sun60)) <= 1.05:
        sun60 *= 100.0
        sun120 *= 100.0
        earth60 *= 100.0
        earth120 *= 100.0

    s120_2k = resample_cell_max(sun120, s120_x0, s120_y0, s120_dx, GRID_2K, sub=3)
    s60_2k = resample_cell_max(sun60, s60_x0, s60_y0, s60_dx, GRID_2K, sub=5)

    xs_2k = -HALF_EXTENT + (np.arange(GRID_2K) + 0.5) * RES_2K
    ys_2k = +HALF_EXTENT - (np.arange(GRID_2K) + 0.5) * RES_2K
    gx_2k, gy_2k = np.meshgrid(xs_2k, ys_2k)
    w60 = np.clip((148000.0 - np.maximum(np.abs(gx_2k), np.abs(gy_2k))) / 8000.0, 0.0, 1.0)
    solar_2k = np.clip(w60 * s60_2k + (1.0 - w60) * s120_2k, 0.0, 100.0)

    psr_4k = resample_bilinear((psr120 > 0.5).astype(np.float32), p120_x0, p120_y0, p120_dx, GRID_1K * 4)
    psr_1k = psr_4k.reshape(GRID_1K, 4, GRID_1K, 4).mean(axis=(1, 3)) >= 0.5
    dist_psr_km_1k = distance_transform_edt(~psr_1k) * (RES_1K / 1000.0)

    e120_1k = resample_bilinear(earth120, e120_x0, e120_y0, e120_dx, GRID_1K)
    e60_1k = resample_bilinear(earth60, e60_x0, e60_y0, e60_dx, GRID_1K)
    xs_1k = -HALF_EXTENT + (np.arange(GRID_1K) + 0.5) * RES_1K
    ys_1k = +HALF_EXTENT - (np.arange(GRID_1K) + 0.5) * RES_1K
    gx_1k, gy_1k = np.meshgrid(xs_1k, ys_1k)
    w60_1k = np.clip((148000.0 - np.maximum(np.abs(gx_1k), np.abs(gy_1k))) / 8000.0, 0.0, 1.0)
    earth_1k = np.clip(w60_1k * e60_1k + (1.0 - w60_1k) * e120_1k, 0.0, 100.0)

    with zipfile.ZipFile(prp_zip_path, "r") as zf:
        tab_name = [n for n in zf.namelist() if n.lower().endswith(".tab")][0]
        with zf.open(tab_name) as f:
            df = pd.read_csv(
                f,
                skipinitialspace=True,
                usecols=["tri_clon", "tri_clat", "tri_calt", "temp_avg", "temp_max", "ice_depth"],
            )

    df = df[(df["temp_max"] >= df["temp_avg"]) & (df["temp_avg"] > 5.0)]
    clon_raw = df["tri_clon"].to_numpy(dtype=np.float64)
    clon = np.where(clon_raw > 180.0, clon_raw - 360.0, clon_raw)
    clat = df["tri_clat"].to_numpy(dtype=np.float64)
    calt_m = df["tri_calt"].to_numpy(dtype=np.float32) * 1000.0
    tavg = df["temp_avg"].to_numpy(dtype=np.float32)
    tmax = df["temp_max"].to_numpy(dtype=np.float32)
    iced = df["ice_depth"].to_numpy(dtype=np.float32)

    # Note: In BOTH dlre_prp_north.tab and dlre_prp_south.tab, +Y_map aligns with +rho * cos(lon) (verified r > 0.9989)
    lon_rad = np.radians(clon)
    rho_p = 2.0 * R_MOON * np.tan(np.radians((90.0 - hemi * clat) / 2.0))
    px = +rho_p * np.sin(lon_rad)
    py = +rho_p * np.cos(lon_rad)

    tree = cKDTree(np.column_stack([px, py]))
    dists, idx = tree.query(np.column_stack([gx_1k.ravel(), gy_1k.ravel()]), k=1, workers=-1)
    valid_1k = (dists <= 1500.0).reshape(GRID_1K, GRID_1K)
    tavg_1k = np.where(valid_1k, tavg[idx].reshape(GRID_1K, GRID_1K), 140.0)
    tmax_1k = np.where(valid_1k, tmax[idx].reshape(GRID_1K, GRID_1K), 220.0)
    iced_1k = np.where(valid_1k, iced[idx].reshape(GRID_1K, GRID_1K), -9999.0)
    calt_1k = np.where(valid_1k, calt_m[idx].reshape(GRID_1K, GRID_1K), 0.0)

    lat_2k, _ = xy_to_latlon(gx_2k, gy_2k, hemi)
    lat_1k, _ = xy_to_latlon(gx_1k, gy_1k, hemi)
    cap_2k = (hemi * lat_2k) >= 80.0
    cap_1k = (hemi * lat_1k) >= 80.0

    elev_corr = float(np.corrcoef(dem_1k[cap_1k], calt_1k[cap_1k])[0, 1])
    assert elev_corr > 0.995, f"{pole_key} Diviner/LOLA elevation correlation check failed: {elev_corr}"
    print(f"   Verified Diviner vs LOLA topography correlation: r = {elev_corr:.5f}", flush=True)

    # Save 2048x2048 <pole>_dem_2k.png
    u16_elev = np.clip(np.round((dem_2k - elev_offset) / elev_span * 65535.0), 0, 65535).astype(np.uint16)
    r_dem = (u16_elev >> 8).astype(np.uint8)
    g_dem = (u16_elev & 0xFF).astype(np.uint8)
    b_sun = np.clip(np.round(solar_2k / 100.0 * 255.0), 0, 255).astype(np.uint8)
    dem_fname = f"{pole_key}_dem_2k.png"
    dem_out = os.path.join(ASSETS_DIR, dem_fname)
    save_rgba_opaque(dem_out, r_dem, g_dem, b_sun)

    # Save 1024x1024 <pole>_science_1k.png
    r_temp = np.clip(np.round((tavg_1k - 20.0) / 200.0 * 255.0), 0, 255).astype(np.uint8)
    g_ice = np.full((GRID_1K, GRID_1K), 255, dtype=np.uint8)
    sub_ice = (iced_1k > 0.0) & (iced_1k <= 2.5)
    g_ice[sub_ice] = np.clip(1 + np.round(iced_1k[sub_ice] / 2.5 * 249.0), 1, 250).astype(np.uint8)
    g_ice[iced_1k == 0.0] = 0
    b_dpsr = np.clip(np.round(dist_psr_km_1k * 10.0), 0, 255).astype(np.uint8)
    sci_fname = f"{pole_key}_science_1k.png"
    sci_out = os.path.join(ASSETS_DIR, sci_fname)
    save_rgba_opaque(sci_out, r_temp, g_ice, b_dpsr)

    # Decode exact PNG values so metadata stats & pins match shipped PNGs 100%
    elev_dec = (u16_elev.astype(np.float64) / 65535.0) * elev_span + elev_offset
    solar_dec = (b_sun.astype(np.float64) / 255.0) * 100.0
    temp_dec = (r_temp.astype(np.float64) / 255.0) * 200.0 + 20.0
    dpsr_dec = b_dpsr.astype(np.float64) / 10.0

    def sample_pixel(r2, c2):
        r2 = int(r2)
        c2 = int(c2)
        r1 = r2 // 2
        c1 = c2 // 2
        x = float(-HALF_EXTENT + (c2 + 0.5) * RES_2K)
        y = float(+HALF_EXTENT - (r2 + 0.5) * RES_2K)
        lat, lon = xy_to_latlon(x, y, hemi)
        r2m, r2p = max(0, r2 - 1), min(GRID_2K - 1, r2 + 1)
        c2m, c2p = max(0, c2 - 1), min(GRID_2K - 1, c2 + 1)
        dzdx = (elev_dec[r2, c2p] - elev_dec[r2, c2m]) / (2.0 * RES_2K)
        dzdy = (elev_dec[r2m, c2] - elev_dec[r2p, c2]) / (2.0 * RES_2K)
        slope_deg = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        ice_g_val = int(g_ice[r1, c1])
        if ice_g_val == 0:
            ice_m = 0.0
        elif ice_g_val <= 250:
            ice_m = round((ice_g_val - 1) / 249.0 * 2.5, 2)
        else:
            ice_m = None
        t_avg_dec = round(float(temp_dec[r1, c1]), 1)
        t_max_val = round(float(tmax_1k[r1, c1]), 1)
        assert t_max_val >= t_avg_dec, f"Physical violation at {pole_key} ({r2},{c2}): tmax {t_max_val} < tavg {t_avg_dec}"
        return {
            "lat": round(float(lat), 3),
            "lon": round(float(lon), 3),
            "x_m": round(x, 1),
            "y_m": round(y, 1),
            "elev_m": int(round(float(elev_dec[r2, c2]))),
            "solar_pct": round(float(solar_dec[r2, c2]), 1),
            "temp_avg_k": t_avg_dec,
            "temp_max_k": t_max_val,
            "slope_deg": round(slope_deg, 1),
            "earth_pct": round(float(earth_1k[r1, c1]), 1),
            "psr_dist_km": round(float(dpsr_dec[r1, c1]), 1),
            "ice_depth_m": ice_m,
        }

    # Spherical stereographic area inside |lat| >= 80 deg
    rho_1k = np.hypot(gx_1k, gy_1k)
    k_scale_1k = 1.0 + (rho_1k / (2.0 * R_MOON)) ** 2
    sph_area_1k = ((RES_1K / 1000.0) ** 2) / (k_scale_1k ** 2)

    # Native 120 m PSR area inside |lat| >= 80 deg
    xs_p = p120_x0 + (np.arange(psr120.shape[1]) + 0.5) * p120_dx
    ys_p = p120_y0 - (np.arange(psr120.shape[0]) + 0.5) * p120_dx
    gxp, gyp = np.meshgrid(xs_p, ys_p)
    rhop = np.hypot(gxp, gyp)
    dlatp = np.degrees(2.0 * np.arctan(rhop / (2.0 * R_MOON)))
    kp = 1.0 + (rhop / (2.0 * R_MOON)) ** 2
    psr_native_km2 = int(round(float(np.sum(((p120_dx / 1000.0) ** 2 / (kp ** 2))[(psr120 > 0.5) & (dlatp <= 10.0)]))))

    coldest_temp_k = round(float(temp_dec[cap_1k].min()), 1)
    coldest_raw_k = round(float(tavg_1k[cap_1k].min()), 2)
    peak_solar_pct = round(float(solar_dec[cap_2k].max()), 1)
    peak_solar_native_pct = round(float(np.nanmax(sun60)), 1)
    psr_area_km2 = int(round(float(np.sum(sph_area_1k[(b_dpsr == 0) & cap_1k]))))
    cold_trap_110k_km2 = int(round(float(np.sum(sph_area_1k[(temp_dec <= 110.0) & cap_1k]))))
    frost_area_km2 = int(round(float(np.sum(sph_area_1k[(g_ice == 0) & cap_1k]))))

    landmarks = []
    for lm in landmark_defs:
        entry = {k: v for k, v in lm.items() if k not in ("r2", "c2")}
        entry.update(sample_pixel(lm["r2"], lm["c2"]))
        landmarks.append(entry)

    major_craters = []
    for c in crater_defs:
        cx, cy = latlon_to_xy(c["lat"], c["lon"], hemi)
        major_craters.append({
            **c,
            "x_m": round(cx, 1),
            "y_m": round(cy, 1),
        })

    return {
        "pole": pole_key,
        "hemi": hemi,
        "crs": crs_label,
        "crs_short": crs_label.split(" ")[0],
        "lat_band": "80°N - 90°N" if hemi > 0 else "80°S - 90°S",
        "summer_subsolar_lat_deg": 1.54 if hemi > 0 else -1.54,
        "default_sun_lon_deg": 132.0 if hemi > 0 else -52.0,
        "elev_offset_m": elev_offset,
        "elev_span_m": elev_span,
        "dem_encoding_step_m": round(elev_span / 65535.0, 4),
        "assets": {
            "dem_2k": f"assets/{dem_fname}",
            "science_1k": f"assets/{sci_fname}",
        },
        "stats": {
            "coldest_temp_k": coldest_temp_k,
            "coldest_raw_facet_k": coldest_raw_k,
            "peak_solar_pct": peak_solar_pct,
            "peak_solar_native_60m_pct": peak_solar_native_pct,
            "psr_area_km2": psr_area_km2,
            "psr_native_120m_km2": psr_native_km2,
            "cold_trap_110k_km2": cold_trap_110k_km2,
            "surface_frost_km2": frost_area_km2,
            "elev_min_m": int(round(float(elev_dec[cap_2k].min()))),
            "elev_max_m": int(round(float(elev_dec[cap_2k].max()))),
            "diviner_lola_elev_corr": round(elev_corr, 5),
        },
        "landmarks": landmarks,
        "major_craters": major_craters,
        "provenance": {
            "dem_sha256": sha256_file(dem_out),
            "sci_sha256": sha256_file(sci_out),
        },
    }


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    north_landmarks = [
        {
            "id": "whipple-rim",
            "index": 1,
            "r2": 984,
            "c2": 1074,
            "tag_en": "PEAK POLAR ILLUMINATION · WHIPPLE RIM",
            "tag_fr": "ILLUMINATION POLAIRE MAXIMALE · REMPART WHIPPLE",
            "name_en": "Whipple North Rim",
            "name_fr": "Rempart Nord de Whipple",
            "desc_en": "Highest solar continuity in the Lunar Arctic, lit up to 89.8% of the 18.6-year nodal precession cycle (89.7% at 60 m scale) just 3.0 km from Whipple's cold trap.",
            "desc_fr": "Plus forte continuité solaire de l'Arctique lunaire, éclairée jusqu'à 89,8 % du cycle de précession nodale de 18,6 ans (89,7 % à 60 m), à 3,0 km du piège froid de Whipple.",
            "recommended_mode": "light",
        },
        {
            "id": "hermite-sw",
            "index": 2,
            "r2": 984,
            "c2": 496,
            "tag_en": "SOUTHWESTERN FLOOR PSR · HERMITE CRATER",
            "tag_fr": "OMBRE PERMANENTE SUD-OUEST · CRATÈRE HERMITE",
            "name_en": "Hermite SW Cold Trap",
            "name_fr": "Piège Froid Sud-Ouest d'Hermite",
            "desc_en": "Permanently shadowed floor inside 108.6 km Hermite Crater (33.3 K annual mean, stable surface frost). Diviner recorded ~26 K (-247°C) winter temperatures in Hermite's southwestern PSRs.",
            "desc_fr": "Fond en ombre permanente dans le cratère Hermite de 108,6 km (moyenne annuelle 33,3 K, givre stable en surface). Diviner a mesuré ~26 K (-247 °C) en hiver dans ses pièges sud-ouest.",
            "recommended_mode": "cold",
        },
        {
            "id": "peary-cold-trap",
            "index": 3,
            "r2": 1244,
            "c2": 1116,
            "tag_en": "24.7 K ANNUAL MEAN MINIMUM · PEARY PSR",
            "tag_fr": "MOYENNE ANNUELLE MINIMALE 24,7 K · PSR PEARY",
            "name_en": "Peary Floor Cold Trap",
            "name_fr": "Piège Cryogénique de Peary",
            "desc_en": "Doubly shadowed interior depression inside 78.8 km Peary Crater where Diviner Level-5 annual mean temperatures drop to 24.7 K (-248°C), peaking at just 28.8 K.",
            "desc_fr": "Dépression doublement ombragée dans le cratère Peary de 78,8 km où la température moyenne annuelle Diviner descend à 24,7 K (-248 °C), avec un maximum de 28,8 K.",
            "recommended_mode": "cold",
        },
        {
            "id": "rozh-psr",
            "index": 4,
            "r2": 408,
            "c2": 1040,
            "tag_en": "181 KM FAR-SIDE WALLED PLAIN · SURFACE FROST",
            "tag_fr": "PLAINE MURÉE DE 181 KM · GIVRE DE SURFACE",
            "name_en": "Rozhdestvenskiy Floor PSR",
            "name_fr": "Ombre Permanente de Rozhdestvenskiy",
            "desc_en": "Permanently shadowed depression inside the 181.2 km Rozhdestvenskiy crater with 0.0% direct sunlight, a 40.4 K annual mean, and thermally stable surface water frost.",
            "desc_fr": "Dépression en ombre permanente dans le cratère Rozhdestvenskiy de 181,2 km avec 0,0 % de soleil direct, une moyenne annuelle de 40,4 K et du givre d'eau stable en surface.",
            "recommended_mode": "cold",
        },
        {
            "id": "byrd-rim",
            "index": 5,
            "r2": 1344,
            "c2": 1032,
            "tag_en": "EARTH-FACING POLAR HIGHLAND · 0° MERIDIAN",
            "tag_fr": "HAUTE TERRE FACE À LA TERRE · MÉRIDIEN 0°",
            "name_en": "Byrd North Rim",
            "name_fr": "Rempart Nord de Byrd",
            "desc_en": "Gently sloped (1.3°) near-side highland crest at +909 m along the 0° Earth meridian combining 63.5% solar illumination, 67.8% Direct-to-Earth visibility, and a PSR 4.9 km away.",
            "desc_fr": "Crête quasi plane (1,3°) à +909 m sur le méridien terrestre 0° combinant 63,5 % d'ensoleillement, 67,8 % de visibilité directe avec la Terre et un PSR à 4,9 km.",
            "recommended_mode": "shadow",
        },
    ]

    north_craters = [
        {"name": "PEARY", "lat": 88.63, "lon": 24.40, "diameter_km": 78.75},
        {"name": "HERMITE", "lat": 86.17, "lon": -93.32, "diameter_km": 108.64},
        {"name": "BYRD", "lat": 85.43, "lon": 10.07, "diameter_km": 97.49},
        {"name": "ROZHDESTVENSKIY", "lat": 84.99, "lon": -157.89, "diameter_km": 181.15},
        {"name": "NANSEN", "lat": 81.17, "lon": 95.38, "diameter_km": 116.90},
        {"name": "PLASKETT", "lat": 81.63, "lon": 176.71, "diameter_km": 114.34},
    ]

    south_landmarks = [
        {
            "id": "connecting-ridge",
            "index": 1,
            "r2": 1063,
            "c2": 987,
            "tag_en": "PEAK SOUTH POLAR SUNLIGHT · CONNECTING RIDGE",
            "tag_fr": "PIC D'ENSOLEILLEMENT AUSTRAL · CRÊTE DE LIAISON",
            "name_en": "Shackleton-de Gerlache Ridge",
            "name_fr": "Crête Shackleton-de Gerlache",
            "desc_en": "Highest solar continuity at the Lunar South Pole, bathed in sunlight for 88.6% of the 18.6-year nodal cycle (88.4% at 60 m scale) at +1,942 m between Shackleton and de Gerlache.",
            "desc_fr": "Plus forte continuité solaire du pôle Sud lunaire, éclairée 88,6 % du cycle nodal de 18,6 ans (88,4 % à 60 m) à +1 942 m entre les cratères Shackleton et de Gerlache.",
            "recommended_mode": "light",
        },
        {
            "id": "shackleton-psr",
            "index": 2,
            "r2": 1038,
            "c2": 1046,
            "tag_en": "SOUTH POLE INTERIOR COLD TRAP · 89.7°S",
            "tag_fr": "PIÈGE FROID DU PÔLE SUD · 89,7°S",
            "name_en": "Shackleton Crater Floor",
            "name_fr": "Fond du Cratère Shackleton",
            "desc_en": "Flat (4.9°) permanently shadowed floor 2,804 m below the reference sphere inside 20.9 km Shackleton Crater, maintaining a 45.9 K annual mean right at the lunar spin axis.",
            "desc_fr": "Fond plat (4,9°) en ombre permanente à -2 804 m dans le cratère Shackleton (20,9 km), maintenant une moyenne annuelle de 45,9 K tout près de l'axe de rotation lunaire.",
            "recommended_mode": "cold",
        },
        {
            "id": "haworth-cold-trap",
            "index": 3,
            "r2": 773,
            "c2": 968,
            "tag_en": "26.3 K ULTRA-COLD BASIN · HAWORTH PSR",
            "tag_fr": "BASSIN ULTRA-FROID 26,3 K · PSR HAWORTH",
            "name_en": "Haworth Floor Cold Trap",
            "name_fr": "Piège Cryogénique de Haworth",
            "desc_en": "Doubly shadowed floor at -4,007 m inside 51.4 km Haworth Crater averaging 26.3 K (-247°C, 26.8 K max); nearby doubly shadowed pits reach the 25.5 K South Polar mean minimum.",
            "desc_fr": "Fond doublement ombragé à -4 007 m dans le cratère Haworth (51,4 km) à 26,3 K de moyenne (-247 °C, max 26,8 K) ; les dépressions voisines atteignent le minimum austral de 25,5 K.",
            "recommended_mode": "cold",
        },
        {
            "id": "cabeus-lcross",
            "index": 4,
            "r2": 683,
            "c2": 661,
            "tag_en": "LCROSS WATER-ICE PLUME BASIN · SURFACE FROST",
            "tag_fr": "BASSIN D'IMPACT LCROSS · GIVRE DE SURFACE",
            "name_en": "Cabeus Floor PSR",
            "name_fr": "Ombre Permanente de Cabeus",
            "desc_en": "Permanently shadowed floor (-4,033 m, 45.1 K mean, stable surface water frost) inside 100.6 km Cabeus Crater, where NASA's 2009 LCROSS impact plume confirmed water ice.",
            "desc_fr": "Fond en ombre permanente (-4 033 m, moyenne 45,1 K, givre d'eau stable en surface) dans le cratère Cabeus (100,6 km), où l'impact LCROSS de la NASA a confirmé la glace d'eau en 2009.",
            "recommended_mode": "cold",
        },
        {
            "id": "mons-malapert",
            "index": 5,
            "r2": 611,
            "c2": 1000,
            "tag_en": "100% EARTH-VISIBLE MASSIF · +4,947 M",
            "tag_fr": "MASSIF 100 % VISIBLE DEPUIS LA TERRE · +4 947 M",
            "name_en": "Mons Malapert Summit",
            "name_fr": "Sommet de Mons Malapert",
            "desc_en": "Towering +4,947 m mountain crest near the 0° meridian enjoying 100.0% Direct-to-Earth visibility and 70.6% solar illumination above the South Polar highlands.",
            "desc_fr": "Crête montagneuse culminant à +4 947 m près du méridien 0°, offrant 100,0 % de visibilité directe avec la Terre et 70,6 % d'ensoleillement au-dessus des hautes terres australes.",
            "recommended_mode": "shadow",
        },
    ]

    south_craters = [
        {"name": "SHOEMAKER", "lat": -88.14, "lon": 45.91, "diameter_km": 51.82},
        {"name": "HAWORTH", "lat": -87.45, "lon": -5.17, "diameter_km": 51.42},
        {"name": "FAUSTINI", "lat": -87.18, "lon": 84.31, "diameter_km": 42.48},
        {"name": "DE GERLACHE", "lat": -88.49, "lon": -88.35, "diameter_km": 32.71},
        {"name": "CABEUS", "lat": -85.33, "lon": -42.13, "diameter_km": 100.58},
        {"name": "AMUNDSEN", "lat": -84.44, "lon": 83.07, "diameter_km": 103.39},
        {"name": "SCOTT", "lat": -82.35, "lon": 48.52, "diameter_km": 107.82},
    ]

    north_meta = build_pole(
        pole_key="north",
        hemi=1,
        crs_label="IAU_2015:30130 (Moon North Polar Stereographic)",
        elev_offset=-5500.0,
        elev_span=8500.0,
        ldem_path=os.path.join(CACHE_N, "LDEM_80N_80M.IMG"),
        sun60_path=os.path.join(CACHE_N, "AVGVISIB_85N_060M_201608.TIF"),
        sun120_path=os.path.join(CACHE_N, "AVGVISIB_75N_120M_201608.TIF"),
        earth60_path=os.path.join(CACHE_N, "AVGVISIB_85N_060M_201608_EARTH.TIF"),
        earth120_path=os.path.join(CACHE_N, "AVGVISIB_75N_120M_201608_EARTH.TIF"),
        psr120_path=os.path.join(CACHE_N, "LPSR_75N_120M_201608.TIF"),
        prp_zip_path=os.path.join(CACHE_N, "dlre_prp_north.zip"),
        landmark_defs=north_landmarks,
        crater_defs=north_craters,
    )

    south_meta = build_pole(
        pole_key="south",
        hemi=-1,
        crs_label="IAU_2015:30135 (Moon South Polar Stereographic)",
        elev_offset=-7500.0,
        elev_span=15000.0,
        ldem_path=os.path.join(CACHE_N, "LDEM_80S_80M.IMG"),
        sun60_path=os.path.join(CACHE_S, "AVGVISIB_85S_060M_201608.TIF"),
        sun120_path=os.path.join(CACHE_N, "AVGVISIB_75S_120M_201608.TIF"),
        earth60_path=os.path.join(CACHE_S, "AVGVISIB_85S_060M_201608_EARTH.TIF"),
        earth120_path=os.path.join(CACHE_N, "AVGVISIB_75S_120M_201608_EARTH.TIF"),
        psr120_path=os.path.join(CACHE_N, "LPSR_75S_120M_201608.TIF"),
        prp_zip_path=os.path.join(CACHE_N, "dlre_prp_south.zip"),
        landmark_defs=south_landmarks,
        crater_defs=south_craters,
    )

    atlas_meta = {
        "title": "Lunar Polar Atlas (North 80°N-90°N & South 80°S-90°S)",
        "radius_moon_m": R_MOON,
        "half_extent_m": HALF_EXTENT,
        "dem_grid": GRID_2K,
        "dem_res_m": RES_2K,
        "dem_source_res_m": 80.0,
        "dem_source_step_m": 0.5,
        "sci_grid": GRID_1K,
        "sci_res_m": RES_1K,
        "temp_offset_k": 20.0,
        "temp_span_k": 200.0,
        "poles": {
            "north": north_meta,
            "south": south_meta,
        },
    }

    meta_out = os.path.join(ASSETS_DIR, "polar_atlas_meta.json")
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(atlas_meta, f, indent=2)

    # Remove legacy single-pole asset files if present
    for old_f in ["arctic_dem_2k.png", "arctic_science_1k.png", "arctic_meta.json"]:
        old_p = os.path.join(ASSETS_DIR, old_f)
        if os.path.exists(old_p):
            os.remove(old_p)

    print("\nDONE! Summary:", flush=True)
    for pk in ("north", "south"):
        print(pk.upper(), json.dumps(atlas_meta["poles"][pk]["stats"], indent=2), flush=True)


if __name__ == "__main__":
    main()
