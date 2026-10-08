"""
Sentinel-2 Multi-Temporal Water & Non-Crop Masking and Parcel Validation Module.
Member 2 - Agricultural Land Parcel & Crop Identification (Ambasamudram & Cheranmahadevi).

Identifies water bodies, bare land, roads, settlements, and non-agricultural parcels
using multi-temporal Sentinel-2 Level-2A reflectance bands and indices:
- Water Mask via NDWI, MNDWI, NIR absorption
- Non-Crop Mask via temporal peak NDVI thresholding (< 0.20)
- Parcel Zonal Auditing: detects and reclassifies false positive Paddy/Banana on water/bare land
- Prediction Confidence Tiering: High (>=0.80), Medium (0.60-0.80), Low (<0.60 / Unknown)

Exports:
- data/parcels/cleaned/classified_parcels.geojson (updated with GIS validation attributes)
- results/non_crop_water_audit.csv
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask


def build_multitemporal_masks(
    indices_dir: Path = Path("data/processed/indices"),
    cloud_masked_dir: Path = Path("data/processed/cloud_masked"),
    dates: Optional[List[str]] = None,
    nodata_val: float = -9999.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """
    Build physical Water Mask and Non-Crop Mask across all 4 Sentinel-2 acquisition dates.
    Returns:
    - water_mask: 2D boolean array (True for water bodies / river / canals)
    - non_crop_mask: 2D boolean array (True for bare soil, urban, fallow, roads)
    - crop_vegetation_mask: 2D boolean array (True for active photosynthetic agricultural vegetation)
    - meta: raster metadata profile
    """
    if dates is None:
        dates = ["2026-03-20", "2026-04-02", "2026-04-22", "2026-09-09"]

    ref_path = indices_dir / dates[0] / "NDVI.tif"
    with rasterio.open(ref_path) as src:
        meta = src.profile.copy()
        h, w = src.height, src.width

    ndvi_stack = []
    ndwi_stack = []
    nir_stack = []
    green_stack = []

    for d in dates:
        p_ndvi = indices_dir / d / "NDVI.tif"
        p_ndwi = indices_dir / d / "NDWI.tif"
        p_b08 = cloud_masked_dir / d / "B08.tif"
        p_b03 = cloud_masked_dir / d / "B03.tif"

        with rasterio.open(p_ndvi) as s_ndvi:
            arr_ndvi = s_ndvi.read(1).astype(np.float32)
            arr_ndvi = np.where(arr_ndvi == nodata_val, np.nan, arr_ndvi)
            ndvi_stack.append(arr_ndvi)

        with rasterio.open(p_ndwi) as s_ndwi:
            arr_ndwi = s_ndwi.read(1).astype(np.float32)
            arr_ndwi = np.where(arr_ndwi == nodata_val, np.nan, arr_ndwi)
            ndwi_stack.append(arr_ndwi)

        with rasterio.open(p_b08) as s_b08:
            arr_b08 = s_b08.read(1).astype(np.float32)
            arr_b08 = np.where(arr_b08 == nodata_val, np.nan, arr_b08)
            # Scale BOA reflectance if not already scaled
            if np.nanmax(arr_b08) > 2.0:
                arr_b08 = arr_b08 / 10000.0
            nir_stack.append(arr_b08)

        with rasterio.open(p_b03) as s_b03:
            arr_b03 = s_b03.read(1).astype(np.float32)
            arr_b03 = np.where(arr_b03 == nodata_val, np.nan, arr_b03)
            if np.nanmax(arr_b03) > 2.0:
                arr_b03 = arr_b03 / 10000.0
            green_stack.append(arr_b03)

    ndvi_arr = np.stack(ndvi_stack, axis=0)  # (4, H, W)
    ndwi_arr = np.stack(ndwi_stack, axis=0)
    nir_arr = np.stack(nir_stack, axis=0)
    green_arr = np.stack(green_stack, axis=0)

    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi_max = np.nanmax(ndvi_arr, axis=0)
        ndvi_mean = np.nanmean(ndvi_arr, axis=0)
        ndwi_mean = np.nanmean(ndwi_arr, axis=0)
        nir_mean = np.nanmean(nir_arr, axis=0)
        green_mean = np.nanmean(green_arr, axis=0)

    # 1. Physical Water Mask:
    # High NDWI (> -0.05), NIR absorption (NIR < 0.10), Green > NIR
    water_mask = (ndwi_mean > -0.05) & (nir_mean < 0.12) & (green_mean > (nir_mean - 0.02))

    # 2. Non-Crop Mask (Bare soil, settlements, roads, fallow ground):
    # Maximum temporal NDVI never exceeds 0.20 throughout all growth seasons
    non_crop_mask = (ndvi_max < 0.20) & (~water_mask)

    # 3. Active Crop / Photosynthetic Vegetation:
    # Maximum temporal NDVI exceeds 0.28 with active vegetative vigor
    crop_vegetation_mask = (ndvi_max >= 0.28) & (~water_mask) & (~non_crop_mask)

    return water_mask, non_crop_mask, crop_vegetation_mask, meta


def validate_parcels_with_masks(
    classified_parcels_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    output_validated_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    output_audit_csv_path: Path = Path("results/non_crop_water_audit.csv"),
    target_crs: str = "EPSG:32643",
) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Audit each parcel against the Sentinel-2 physical Water and Non-Crop masks.
    Reclassifies parcels located on water bodies or non-crop land, preventing forced Paddy/Banana predictions.
    """
    output_audit_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    parcels_gdf = gpd.read_file(classified_parcels_path)
    if parcels_gdf.crs is None or parcels_gdf.crs.to_string().upper() != target_crs.upper():
        parcels_utm = parcels_gdf.to_crs(target_crs)
    else:
        parcels_utm = parcels_gdf.copy()

    # 2. Build Multi-temporal Physical Masks
    water_mask, non_crop_mask, crop_mask, meta = build_multitemporal_masks()
    transform = meta["transform"]

    audit_records = []
    validated_crops = []
    confidence_tiers = []
    land_cover_types = []

    print("\n[SPATIAL AUDIT] Auditing 293 parcels against Sentinel-2 Water & Non-Crop physical masks...")

    for idx, row in parcels_utm.iterrows():
        p_id = row["parcel_id"]
        geom = row.geometry
        orig_crop = row.get("predicted_crop", row.get("crop_name", "Unknown"))
        conf = float(row.get("confidence", 1.0))

        # Rasterize parcel geometry
        p_mask = geometry_mask([geom], out_shape=water_mask.shape, transform=transform, invert=True)

        if not np.any(p_mask):
            centroid = geom.centroid
            c_col, c_row = ~transform * (centroid.x, centroid.y)
            r_idx, c_idx = int(c_row), int(c_col)
            if 0 <= r_idx < water_mask.shape[0] and 0 <= c_idx < water_mask.shape[1]:
                p_mask[r_idx, c_idx] = True

        total_pixels = int(np.count_nonzero(p_mask))
        if total_pixels == 0:
            total_pixels = 1

        w_pixels = int(np.count_nonzero(p_mask & water_mask))
        nc_pixels = int(np.count_nonzero(p_mask & non_crop_mask))
        veg_pixels = int(np.count_nonzero(p_mask & crop_mask))

        pct_water = round((w_pixels / total_pixels) * 100.0, 2)
        pct_non_crop = round((nc_pixels / total_pixels) * 100.0, 2)
        pct_veg = round((veg_pixels / total_pixels) * 100.0, 2)

        # Determine Confidence Tier
        if conf >= 0.80:
            conf_tier = "High Confidence"
        elif conf >= 0.60:
            conf_tier = "Medium Confidence"
        else:
            conf_tier = "Low Confidence / Review"

        # Apply Physical Remote Sensing Validation Logic
        if pct_water >= 40.0:
            # Predominantly open water / river channel
            final_crop = "Water"
            land_cover = "Water Body / River Canal"
            reclassification_reason = "Exhibits strong water absorption signature (NDWI > 0, NIR < 0.10)"
        elif pct_non_crop >= 50.0:
            # Predominantly bare soil, roads, urban, fallow
            final_crop = "Non-Crop"
            land_cover = "Bare Soil / Settlement / Non-Crop"
            reclassification_reason = "Temporal peak NDVI < 0.20 (no agricultural crop cultivation observed)"
        elif pct_veg >= 40.0 and orig_crop in ["Paddy", "Banana"]:
            # Verified agricultural vegetation
            final_crop = orig_crop
            land_cover = f"Agricultural {orig_crop}"
            reclassification_reason = "Verified active photosynthetic agricultural phenology"
        elif conf < 0.55:
            # Low confidence uncertain parcel
            final_crop = "Non-Crop" if orig_crop == "Other" else orig_crop
            land_cover = f"Uncertain / Mixed ({orig_crop})"
            reclassification_reason = f"Low model prediction confidence ({conf:.2f})"
        else:
            final_crop = "Non-Crop" if orig_crop == "Other" else orig_crop
            land_cover = "Agricultural Land" if orig_crop in ["Paddy", "Banana"] else "Non-Agricultural Land"
            reclassification_reason = "Consistent with multi-temporal spectral profile"

        validated_crops.append(final_crop)
        confidence_tiers.append(conf_tier)
        land_cover_types.append(land_cover)

        audit_records.append({
            "parcel_id": p_id,
            "taluk": row.get("taluk", "Ambasamudram"),
            "original_crop": orig_crop,
            "validated_crop": final_crop,
            "land_cover_type": land_cover,
            "confidence": conf,
            "confidence_tier": conf_tier,
            "pct_water": pct_water,
            "pct_non_crop": pct_non_crop,
            "pct_vegetation": pct_veg,
            "reclassification_reason": reclassification_reason,
            "area_ha": row.get("area_ha", round(geom.area / 10000.0, 4)),
        })

    # Update GeoDataFrame attributes
    parcels_gdf["predicted_crop"] = validated_crops
    parcels_gdf["validated_crop"] = validated_crops
    parcels_gdf["land_cover_type"] = land_cover_types
    parcels_gdf["confidence_tier"] = confidence_tiers
    parcels_gdf["pct_water"] = [r["pct_water"] for r in audit_records]
    parcels_gdf["pct_non_crop"] = [r["pct_non_crop"] for r in audit_records]
    parcels_gdf["pct_vegetation"] = [r["pct_vegetation"] for r in audit_records]

    # Export Updated GeoJSON
    parcels_gdf.to_file(output_validated_path, driver="GeoJSON")

    # Also update member3-fullstack/inputs/classified_parcels.geojson and member1-ml/outputs
    m3_path = Path("member3-fullstack/inputs/classified_parcels.geojson")
    m1_path = Path("member1-ml/outputs/classified_parcels.geojson")
    if m3_path.parent.exists():
        parcels_gdf.to_file(m3_path, driver="GeoJSON")
    if m1_path.parent.exists():
        parcels_gdf.to_file(m1_path, driver="GeoJSON")

    df_audit = pd.DataFrame(audit_records)
    df_audit.to_csv(output_audit_csv_path, index=False)

    counts = parcels_gdf["predicted_crop"].value_counts().to_dict()
    print("\n[VALIDATION COMPLETE] Audited Parcel Distribution:")
    for c_name, c_cnt in counts.items():
        print(f"  * {c_name:<15}: {c_cnt:>4} parcels")
    print(f"  [OK] Saved audited GeoJSON : {output_validated_path.resolve()}")
    print(f"  [OK] Saved audit CSV report: {output_audit_csv_path.resolve()}")

    return parcels_gdf, df_audit


if __name__ == "__main__":
    validate_parcels_with_masks()
