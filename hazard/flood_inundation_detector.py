"""
Multi-Temporal Sentinel-2 Flood Inundation & Hazard Change Detection Module.
Member 2 - Agricultural Land Parcel & Crop Identification (Ambasamudram & Cheranmahadevi).

Detects flood inundation and surface waterlogging by comparing pre-hazard and post-hazard
Sentinel-2 Level-2A imagery:
- Baseline (Before): 2026-04-22 (or 2026-03-20)
- Event (After)    : 2026-09-09 (Post-monsoon / heavy inundation event)

Uses spectral change detection:
- Delta NDWI (Normalized Difference Water Index increase)
- LSWI (Land Surface Water Index)
- Delta NDVI (Vegetation vigor suppression)
- Permanent water baseline exclusion (Thamirabarani river & perennial tanks are preserved as water bodies, NOT counted as crop damage).

Exports:
- results/hazard/hazard_affected_area.geojson
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.validation import make_valid


def load_thresholds(config_path: Path = Path("config/damage_thresholds.json")) -> dict:
    """Load configurable spectral and damage thresholds."""
    if not config_path.exists():
        return {
            "spectral_thresholds": {
                "flood_inundation": {
                    "ndwi_threshold": 0.0,
                    "delta_ndwi_min": 0.15,
                    "lswi_threshold": 0.12,
                    "delta_ndvi_drop": -0.10,
                }
            }
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_lswi(b08: np.ndarray, b11: np.ndarray) -> np.ndarray:
    """Land Surface Water Index: (B08 - B11) / (B08 + B11)"""
    with np.errstate(divide="ignore", invalid="ignore"):
        denom = b08 + b11
        lswi = np.where(denom > 0, (b08 - b11) / denom, np.nan)
    return lswi


def run_flood_inundation_detection(
    before_date: str = "2026-04-22",
    after_date: str = "2026-09-09",
    indices_dir: Path = Path("data/processed/indices"),
    cloud_masked_dir: Path = Path("data/processed/cloud_masked"),
    aoi_path: Path = Path("data/aoi/study_area.geojson"),
    output_geojson_path: Path = Path("results/hazard/hazard_affected_area.geojson"),
    target_crs: str = "EPSG:32643",
    nodata_val: float = -9999.0,
) -> Tuple[gpd.GeoDataFrame, np.ndarray, dict]:
    """
    Execute temporal change detection to delineate flood inundation areas.
    """
    output_geojson_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_thresholds()
    st = cfg.get("spectral_thresholds", {}).get("flood_inundation", {})
    delta_ndwi_min = st.get("delta_ndwi_min", 0.15)
    ndwi_threshold = st.get("ndwi_threshold", 0.0)
    lswi_thresh = st.get("lswi_threshold", 0.12)
    delta_ndvi_drop = st.get("delta_ndvi_drop", -0.10)

    print(f"\n[HAZARD ANALYSIS] Comparing Before ({before_date}) vs After ({after_date})...")

    # 1. Read Before Indices and Bands
    p_ndvi_pre = indices_dir / before_date / "NDVI.tif"
    p_ndwi_pre = indices_dir / before_date / "NDWI.tif"
    p_b08_pre = cloud_masked_dir / before_date / "B08.tif"
    p_b03_pre = cloud_masked_dir / before_date / "B03.tif"

    with rasterio.open(p_ndvi_pre) as s:
        meta = s.profile.copy()
        transform = s.transform
        ndvi_pre = s.read(1).astype(np.float32)
        ndvi_pre = np.where(ndvi_pre == nodata_val, np.nan, ndvi_pre)

    with rasterio.open(p_ndwi_pre) as s:
        ndwi_pre = s.read(1).astype(np.float32)
        ndwi_pre = np.where(ndwi_pre == nodata_val, np.nan, ndwi_pre)

    with rasterio.open(p_b08_pre) as s:
        b08_pre = s.read(1).astype(np.float32)
        if np.nanmax(b08_pre) > 2.0:
            b08_pre = b08_pre / 10000.0

    with rasterio.open(p_b03_pre) as s:
        b03_pre = s.read(1).astype(np.float32)
        if np.nanmax(b03_pre) > 2.0:
            b03_pre = b03_pre / 10000.0

    # 2. Read After Indices and Bands
    p_ndvi_post = indices_dir / after_date / "NDVI.tif"
    p_ndwi_post = indices_dir / after_date / "NDWI.tif"
    p_b08_post = cloud_masked_dir / after_date / "B08.tif"
    p_b11_post = cloud_masked_dir / after_date / "B11.tif"
    p_b03_post = cloud_masked_dir / after_date / "B03.tif"

    with rasterio.open(p_ndvi_post) as s:
        ndvi_post = s.read(1).astype(np.float32)
        ndvi_post = np.where(ndvi_post == nodata_val, np.nan, ndvi_post)

    with rasterio.open(p_ndwi_post) as s:
        ndwi_post = s.read(1).astype(np.float32)
        ndwi_post = np.where(ndwi_post == nodata_val, np.nan, ndwi_post)

    with rasterio.open(p_b08_post) as s:
        b08_post = s.read(1).astype(np.float32)
        if np.nanmax(b08_post) > 2.0:
            b08_post = b08_post / 10000.0

    with rasterio.open(p_b11_post) as s:
        b11_post = s.read(1).astype(np.float32)
        if np.nanmax(b11_post) > 2.0:
            b11_post = b11_post / 10000.0

    with rasterio.open(p_b03_post) as s:
        b03_post = s.read(1).astype(np.float32)
        if np.nanmax(b03_post) > 2.0:
            b03_post = b03_post / 10000.0

    # 3. Compute Spectral Deltas
    with np.errstate(divide="ignore", invalid="ignore"):
        delta_ndwi = ndwi_post - ndwi_pre
        delta_ndvi = ndvi_post - ndvi_pre
        lswi_post = compute_lswi(b08_post, b11_post)

    # 4. Permanent Water Body Mask (BASELINE - MUST NOT BE COUNTED AS CROP DAMAGE)
    # Permanent water has high NDWI in baseline, low NIR reflectance, and green > NIR
    permanent_water = (ndwi_pre > -0.05) & (b08_pre < 0.12) & (b03_pre > (b08_pre - 0.02))

    # 5. Flood / Inundation Infiltration Detection Logic:
    # A pixel is flagged as flood inundated if:
    # 1. Post-event NDWI is positive (open standing water) OR
    # 2. Significant moisture surge (Delta NDWI >= 0.15) OR
    # 3. High surface water index (LSWI >= 0.12) accompanied by vegetation drop (Delta NDVI < -0.10)
    # AND the pixel was NOT already permanent water.
    inundation_condition = (
        (ndwi_post > ndwi_threshold) |
        (delta_ndwi >= delta_ndwi_min) |
        ((lswi_post >= lswi_thresh) & (delta_ndvi <= delta_ndvi_drop))
    ) & (~permanent_water) & (~np.isnan(ndwi_post)) & (b08_post < 0.28)

    inundation_mask = np.nan_to_num(inundation_condition, nan=False).astype(np.uint8)

    # 6. Vectorize Inundation Polygons
    geom_list = []
    val_list = []

    for geom_dict, val in shapes(inundation_mask, mask=(inundation_mask == 1), transform=transform):
        if val == 1:
            poly = shape(geom_dict)
            if poly.is_valid and poly.area >= 100.0:  # Filter noise < 100 m² (1 pixel)
                geom_list.append(poly)
                val_list.append(1)

    if geom_list:
        gdf_hazard = gpd.GeoDataFrame(
            {
                "hazard_id": [f"HAZARD_FL_{i+1:04d}" for i in range(len(geom_list))],
                "hazard_type": ["Flood / Heavy Rainfall Inundation"] * len(geom_list),
                "observation_before": [before_date] * len(geom_list),
                "observation_after": [after_date] * len(geom_list),
                "source": ["Sentinel-2 Level-2A Multi-Temporal Change Detection"] * len(geom_list),
                "area_sq_m": [g.area for g in geom_list],
                "area_ha": [round(g.area / 10000.0, 4) for g in geom_list],
                "geometry": geom_list,
            },
            crs=target_crs,
        )
    else:
        # Fallback empty geodataframe
        gdf_hazard = gpd.GeoDataFrame(columns=["hazard_id", "hazard_type", "geometry"], crs=target_crs)

    # Reproject to EPSG:4326 for GeoJSON web standard
    gdf_hazard_wgs84 = gdf_hazard.to_crs("EPSG:4326")
    gdf_hazard_wgs84.to_file(output_geojson_path, driver="GeoJSON")

    # Also synchronize to member3-fullstack/inputs/
    m3_out = Path("member3-fullstack/inputs/hazard_affected_area.geojson")
    if m3_out.parent.exists():
        gdf_hazard_wgs84.to_file(m3_out, driver="GeoJSON")

    total_inundated_ha = gdf_hazard["area_ha"].sum() if not gdf_hazard.empty else 0.0
    print(f"  [OK] Inundation Polygons Extracted : {len(gdf_hazard)} polygons")
    print(f"  [OK] Total Inundated Surface Area : {total_inundated_ha:.2f} ha ({total_inundated_ha*2.47105:.2f} acres)")
    print(f"  [OK] Saved Hazard GeoJSON Deliverable: {output_geojson_path.resolve()}")

    return gdf_hazard, inundation_mask, meta


if __name__ == "__main__":
    run_flood_inundation_detection()
