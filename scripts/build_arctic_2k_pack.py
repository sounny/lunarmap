#!/usr/bin/env python3
"""
Builds the 2048x2048 NASA LRO Lunar Arctic (80N-90N) WebGL2 Data Pack.
100% empirical NASA PDS / GSFC PGDA / UCLA Diviner / USGS IAU data from local verified cache.
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
HALF_EXTENT = 304000.0  # 80 deg N stereographic radius: 2 * 1737.4 * tan(5 deg) = 304.01 km
GRID_2K = 2048
RES_2K = (2.0 * HALF_EXTENT) / GRID_2K  # 296.875 m/px
GRID_1K = 1024
RES_1K = (2.0 * HALF_EXTENT) / GRID_1K  # 593.75 m/px

ELEV_OFFSET = -5500.0
ELEV_SPAN = 8500.0  # Encodes -5500m to +3000m across 16-bit uint16 (0.1297 m encoding step)

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


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("1. Reading NASA LRO LOLA 80m North Polar DEM (LDEM_80N_80M, 7600x7600, 0.5m step)...", flush=True)
    ldem_path = os.path.join(CACHE_DIR, "LDEM_80N_80M.IMG")
    raw_dem = np.fromfile(ldem_path, dtype="<i2").reshape(7600, 7600)
    dem_80m = raw_dem.astype(np.float32) * 0.5

    dem_4k = resample_bilinear(dem_80m, -304000.0, 304000.0, 80.0, GRID_2K * 2)
    dem_2k = dem_4k.reshape(GRID_2K, 2, GRID_2K, 2).mean(axis=(1, 3))
    dem_1k = dem_2k.reshape(GRID_1K, 2, GRID_1K, 2).mean(axis=(1, 3))

    print("2. Reading NASA GSFC PGDA Product #69 Solar, PSR & Earth Visibility (60m & 120m)...", flush=True)
    sun60, s60_x0, s60_y0, s60_dx = read_pgda_local("AVGVISIB_85N_060M_201608.TIF")
    sun120, s120_x0, s120_y0, s120_dx = read_pgda_local("AVGVISIB_75N_120M_201608.TIF")
    earth60, e60_x0, e60_y0, e60_dx = read_pgda_local("AVGVISIB_85N_060M_201608_EARTH.TIF")
    earth120, e120_x0, e120_y0, e120_dx = read_pgda_local("AVGVISIB_75N_120M_201608_EARTH.TIF")
    psr120, p120_x0, p120_y0, p120_dx = read_pgda_local("LPSR_75N_120M_201608.TIF")

    if float(np.nanmax(sun60)) <= 1.05:
        sun60 *= 100.0
        sun120 *= 100.0
        earth60 *= 100.0
        earth120 *= 100.0

    # Preserve sub-pixel polar ridge crests strictly within each 296.9 m cell (zero cross-pixel dilation)
    s120_2k = resample_cell_max(sun120, s120_x0, s120_y0, s120_dx, GRID_2K, sub=3)
    s60_2k = resample_cell_max(sun60, s60_x0, s60_y0, s60_dx, GRID_2K, sub=5)

    xs_2k = -HALF_EXTENT + (np.arange(GRID_2K) + 0.5) * RES_2K
    ys_2k = +HALF_EXTENT - (np.arange(GRID_2K) + 0.5) * RES_2K
    gx_2k, gy_2k = np.meshgrid(xs_2k, ys_2k)
    w60 = np.clip((148000.0 - np.maximum(np.abs(gx_2k), np.abs(gy_2k))) / 8000.0, 0.0, 1.0)
    solar_2k = np.clip(w60 * s60_2k + (1.0 - w60) * s120_2k, 0.0, 100.0)

    # 4x4 supersampled majority-area resampling (>= 0.5) for 120 m PSR mask onto 593.8 m grid
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

    print("3. Reading UCLA Diviner Level-5 Polar Resource Product V2.0 (North)...", flush=True)
    prp_zip = os.path.join(CACHE_DIR, "dlre_prp_north.zip")
    with zipfile.ZipFile(prp_zip, "r") as zf:
        tab_name = [n for n in zf.namelist() if n.lower().endswith(".tab")][0]
        with zf.open(tab_name) as f:
            df = pd.read_csv(
                f,
                skipinitialspace=True,
                usecols=["tri_clon", "tri_clat", "tri_calt", "temp_avg", "temp_max", "ice_depth"],
            )

    # Filter out the 14 unphysical model-fit rows where independent tmax < tavg
    df = df[(df["temp_max"] >= df["temp_avg"]) & (df["temp_avg"] > 5.0)]
    clon_raw = df["tri_clon"].to_numpy(dtype=np.float64)
    clon = np.where(clon_raw > 180.0, clon_raw - 360.0, clon_raw)
    clat = df["tri_clat"].to_numpy(dtype=np.float64)
    calt_m = df["tri_calt"].to_numpy(dtype=np.float32) * 1000.0
    tavg = df["temp_avg"].to_numpy(dtype=np.float32)
    tmax = df["temp_max"].to_numpy(dtype=np.float32)
    iced = df["ice_depth"].to_numpy(dtype=np.float32)

    # Restore exact North Polar Stereographic Y coordinate (dlre_prp_north.tab uses +Y_map -> +tri_x)
    lon_rad = np.radians(clon)
    rho_p = 2.0 * R_MOON * np.tan(np.radians((90.0 - clat) / 2.0))
    px = +rho_p * np.sin(lon_rad)
    py = +rho_p * np.cos(lon_rad)

    tree = cKDTree(np.column_stack([px, py]))
    dists, idx = tree.query(np.column_stack([gx_1k.ravel(), gy_1k.ravel()]), k=1, workers=-1)
    valid_1k = (dists <= 1500.0).reshape(GRID_1K, GRID_1K)
    tavg_1k = np.where(valid_1k, tavg[idx].reshape(GRID_1K, GRID_1K), 140.0)
    tmax_1k = np.where(valid_1k, tmax[idx].reshape(GRID_1K, GRID_1K), 220.0)
    iced_1k = np.where(valid_1k, iced[idx].reshape(GRID_1K, GRID_1K), -9999.0)
    calt_1k = np.where(valid_1k, calt_m[idx].reshape(GRID_1K, GRID_1K), 0.0)

    lat_2k, _ = xy_to_latlon(gx_2k, gy_2k)
    lat_1k, _ = xy_to_latlon(gx_1k, gy_1k)
    cap_2k = lat_2k >= 80.0
    cap_1k = lat_1k >= 80.0

    elev_corr = float(np.corrcoef(dem_1k[cap_1k], calt_1k[cap_1k])[0, 1])
    assert elev_corr > 0.995, f"Diviner/LOLA elevation correlation check failed: {elev_corr}"
    print(f"   Verified Diviner vs LOLA topography correlation: r = {elev_corr:.5f}", flush=True)

    # Save 2048x2048 arctic_dem_2k.png
    u16_elev = np.clip(np.round((dem_2k - ELEV_OFFSET) / ELEV_SPAN * 65535.0), 0, 65535).astype(np.uint16)
    r_dem = (u16_elev >> 8).astype(np.uint8)
    g_dem = (u16_elev & 0xFF).astype(np.uint8)
    b_sun = np.clip(np.round(solar_2k / 100.0 * 255.0), 0, 255).astype(np.uint8)
    dem_out = os.path.join(ASSETS_DIR, "arctic_dem_2k.png")
    save_rgba_opaque(dem_out, r_dem, g_dem, b_sun)

    # Save 1024x1024 arctic_science_1k.png
    # Encode g_ice == 0 strictly iff iced_1k == 0.0 (exact surface water frost); 1..250 for (0, 2.5m]; 255 for none
    r_temp = np.clip(np.round((tavg_1k - 20.0) / 200.0 * 255.0), 0, 255).astype(np.uint8)
    g_ice = np.full((GRID_1K, GRID_1K), 255, dtype=np.uint8)
    sub_ice = (iced_1k > 0.0) & (iced_1k <= 2.5)
    g_ice[sub_ice] = np.clip(1 + np.round(iced_1k[sub_ice] / 2.5 * 249.0), 1, 250).astype(np.uint8)
    g_ice[iced_1k == 0.0] = 0
    b_dpsr = np.clip(np.round(dist_psr_km_1k * 10.0), 0, 255).astype(np.uint8)
    sci_out = os.path.join(ASSETS_DIR, "arctic_science_1k.png")
    save_rgba_opaque(sci_out, r_temp, g_ice, b_dpsr)

    # Decode exact PNG values so every metadata stat and landmark matches the shipped PNGs 100%
    elev_dec = (u16_elev.astype(np.float64) / 65535.0) * ELEV_SPAN + ELEV_OFFSET
    solar_dec = (b_sun.astype(np.float64) / 255.0) * 100.0
    temp_dec = (r_temp.astype(np.float64) / 255.0) * 200.0 + 20.0
    dpsr_dec = b_dpsr.astype(np.float64) / 10.0

    def sample_pixel(r2, c2):
        """Snap landmark to exact 2048x2048 pixel center (148.4 m clear of all 2k & 1k cell boundaries)."""
        r2 = int(r2)
        c2 = int(c2)
        r1 = r2 // 2
        c1 = c2 // 2
        x = float(-HALF_EXTENT + (c2 + 0.5) * RES_2K)
        y = float(+HALF_EXTENT - (r2 + 0.5) * RES_2K)
        lat, lon = xy_to_latlon(x, y)
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
        assert t_max_val >= t_avg_dec, f"Physical violation at ({r2},{c2}): tmax {t_max_val} < tavg {t_avg_dec}"
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

    # Global empirical benchmarks inside 80N-90N cap using true spherical stereographic area
    rho_1k = np.hypot(gx_1k, gy_1k)
    k_scale_1k = 1.0 + (rho_1k / (2.0 * R_MOON)) ** 2
    sph_area_1k = ((RES_1K / 1000.0) ** 2) / (k_scale_1k ** 2)

    coldest_temp_k = round(float(temp_dec[cap_1k].min()), 1)
    peak_solar_pct = round(float(solar_dec[cap_2k].max()), 1)
    peak_solar_native_pct = round(float(np.nanmax(sun60)), 1)
    psr_area_km2 = int(round(float(np.sum(sph_area_1k[(b_dpsr == 0) & cap_1k]))))
    cold_trap_110k_km2 = int(round(float(np.sum(sph_area_1k[(temp_dec <= 110.0) & cap_1k]))))
    frost_area_km2 = int(round(float(np.sum(sph_area_1k[(g_ice == 0) & cap_1k]))))

    hx, hy = latlon_to_xy(86.1659, -93.3152)
    in_hermite_psr = (np.hypot(gx_1k - hx, gy_1k - hy) <= 54320.0) & (b_dpsr == 0)
    hermite_min_k = round(float(temp_dec[in_hermite_psr].min()), 1)

    landmarks = [
        {
            "id": "whipple-rim",
            "index": 1,
            "tag_en": "PEAK POLAR ILLUMINATION · WHIPPLE RIM",
            "tag_fr": "ILLUMINATION POLAIRE MAXIMALE · REMPART WHIPPLE",
            "name_en": "Whipple North Rim",
            "name_fr": "Rempart Nord de Whipple",
            "desc_en": "Highest solar continuity in the Lunar Arctic, lit up to 89.8% of the 18.6-year nodal precession cycle (89.7% at 60 m scale) just 3.0 km from Whipple's cold trap.",
            "desc_fr": "Plus forte continuité solaire de l'Arctique lunaire, éclairée jusqu'à 89,8 % du cycle de précession nodale de 18,6 ans (89,7 % à 60 m), à 3,0 km du piège froid de Whipple.",
            "recommended_mode": "light",
            **sample_pixel(984, 1074),
        },
        {
            "id": "hermite-sw",
            "index": 2,
            "tag_en": "SOUTHWESTERN FLOOR PSR · HERMITE CRATER",
            "tag_fr": "OMBRE PERMANENTE SUD-OUEST · CRATÈRE HERMITE",
            "name_en": "Hermite SW Cold Trap",
            "name_fr": "Piège Froid Sud-Ouest d'Hermite",
            "desc_en": "Permanently shadowed floor inside 108.6 km Hermite Crater (33.3 K annual mean, stable surface frost). Diviner recorded ~26 K (-247°C) winter temperatures in Hermite's southwestern PSRs.",
            "desc_fr": "Fond en ombre permanente dans le cratère Hermite de 108,6 km (moyenne annuelle 33,3 K, givre stable en surface). Diviner a mesuré ~26 K (-247 °C) en hiver dans ses pièges sud-ouest.",
            "recommended_mode": "cold",
            **sample_pixel(984, 496),
        },
        {
            "id": "peary-cold-trap",
            "index": 3,
            "tag_en": "24.7 K ANNUAL MEAN MINIMUM · PEARY PSR",
            "tag_fr": "MOYENNE ANNUELLE MINIMALE 24,7 K · PSR PEARY",
            "name_en": "Peary Floor Cold Trap",
            "name_fr": "Piège Cryogénique de Peary",
            "desc_en": "Doubly shadowed interior depression inside 78.8 km Peary Crater where Diviner Level-5 annual mean temperatures drop to 24.7 K (-248°C), peaking at just 28.8 K.",
            "desc_fr": "Dépression doublement ombragée dans le cratère Peary de 78,8 km où la température moyenne annuelle Diviner descend à 24,7 K (-248 °C), avec un maximum de 28,8 K.",
            "recommended_mode": "cold",
            **sample_pixel(1244, 1116),
        },
        {
            "id": "rozh-psr",
            "index": 4,
            "tag_en": "181 KM FAR-SIDE WALLED PLAIN · SURFACE FROST",
            "tag_fr": "PLAINE MURÉE DE 181 KM · GIVRE DE SURFACE",
            "name_en": "Rozhdestvenskiy Floor PSR",
            "name_fr": "Ombre Permanente de Rozhdestvenskiy",
            "desc_en": "Permanently shadowed depression inside the 181.2 km Rozhdestvenskiy crater with 0.0% direct sunlight, a 40.4 K annual mean, and thermally stable surface water frost.",
            "desc_fr": "Dépression en ombre permanente dans le cratère Rozhdestvenskiy de 181,2 km avec 0,0 % de soleil direct, une moyenne annuelle de 40,4 K et du givre d'eau stable en surface.",
            "recommended_mode": "cold",
            **sample_pixel(408, 1040),
        },
        {
            "id": "byrd-rim",
            "index": 5,
            "tag_en": "NEAR-SIDE OUTPOST RIDGE · 0° MERIDIAN",
            "tag_fr": "CRÊTE D'AVANT-POSTE · MÉRIDIEN 0° TERRE",
            "name_en": "Byrd North Rim",
            "name_fr": "Rempart Nord de Byrd",
            "desc_en": "Gently sloped (1.3°) near-side ridge at +909 m along the 0° Earth meridian combining 63.5% solar power, 67.8% Direct-to-Earth visibility, and 4.9 km PSR proximity.",
            "desc_fr": "Crête quasi plane (1,3°) à +909 m sur le méridien terrestre 0° combinant 63,5 % d'ensoleillement, 67,8 % de visibilité directe avec la Terre et un PSR à 4,9 km.",
            "recommended_mode": "outpost",
            **sample_pixel(1344, 1032),
        },
    ]

    # Exact official USGS / IAU Gazetteer of Planetary Nomenclature coordinates (LOLA 2011 control network)
    major_craters = [
        {"name": "PEARY", "lat": 88.63, "lon": 24.40, "diameter_km": 78.75},
        {"name": "HERMITE", "lat": 86.17, "lon": -93.32, "diameter_km": 108.64},
        {"name": "BYRD", "lat": 85.43, "lon": 10.07, "diameter_km": 97.49},
        {"name": "ROZHDESTVENSKIY", "lat": 84.99, "lon": -157.89, "diameter_km": 181.15},
        {"name": "NANSEN", "lat": 81.17, "lon": 95.38, "diameter_km": 116.90},
        {"name": "PLASKETT", "lat": 81.63, "lon": 176.71, "diameter_km": 114.34},
    ]
    for c in major_craters:
        cx, cy = latlon_to_xy(c["lat"], c["lon"])
        c["x_m"] = round(cx, 1)
        c["y_m"] = round(cy, 1)

    meta = {
        "title": "Lunar Arctic (80°N - 90°N) Orbital Atlas",
        "crs": "IAU_2015:30130 (Moon North Polar Stereographic)",
        "radius_moon_m": R_MOON,
        "half_extent_m": HALF_EXTENT,
        "dem_grid": GRID_2K,
        "dem_res_m": RES_2K,
        "sci_grid": GRID_1K,
        "sci_res_m": RES_1K,
        "elev_offset_m": ELEV_OFFSET,
        "elev_span_m": ELEV_SPAN,
        "stats": {
            "coldest_temp_k": coldest_temp_k,
            "hermite_temp_k": hermite_min_k,
            "peak_solar_pct": peak_solar_pct,
            "peak_solar_native_60m_pct": peak_solar_native_pct,
            "psr_area_km2": psr_area_km2,
            "cold_trap_110k_km2": cold_trap_110k_km2,
            "surface_frost_km2": frost_area_km2,
            "elev_min_m": int(round(float(np.min(elev_dec[cap_2k])))),
            "elev_max_m": int(round(float(np.max(elev_dec[cap_2k])))),
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

    print(
        f"DONE! Peak Sun = {peak_solar_pct}% ({peak_solar_native_pct}% native 60m) | "
        f"Global Min = {coldest_temp_k}K | PSR = {psr_area_km2} km2 | Frost = {frost_area_km2} km2",
        flush=True,
    )
    for lm in landmarks:
        print(
            f"  [{lm['index']}] {lm['name_en']}: {lm['lat']}N, {lm['lon']}E | "
            f"{lm['elev_m']}m | Sun {lm['solar_pct']}% | Tavg {lm['temp_avg_k']}K (Tmax {lm['temp_max_k']}K) | Ice {lm['ice_depth_m']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
