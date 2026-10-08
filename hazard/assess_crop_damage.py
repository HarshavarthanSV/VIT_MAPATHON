"""
Crop Parcel Hazard Impact & Damage Assessment Module.
Member 2 - Agricultural Land Parcel & Crop Identification (Ambasamudram & Cheranmahadevi).

Performs rigorous geometric intersection between validated agricultural parcels and
Sentinel-2 multi-temporal hazard inundation polygons:
- Calculates exact affected area in hectares and acres in EPSG:32643
- Computes percentage damage per parcel: (affected_area / parcel_area) * 100
- Classifies damage severity based on config/damage_thresholds.json:
  * Low Damage (0-20%)
  * Moderate Damage (20-50%)
  * High Damage (50-75%)
  * Severe Damage (75-100%)
- Samples pre/post NDVI to evaluate vegetative vigor impact
- Generates:
  * results/damage/crop_damage_assessment.geojson
  * results/damage/crop_damage_summary.csv
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.validation import make_valid
from shapely.ops import unary_union


def load_damage_thresholds(config_path: Path = Path("config/damage_thresholds.json")) -> dict:
    if not config_path.exists():
        return {
            "damage_severity_levels": {
                "low": {"min_percentage": 0.0, "max_percentage": 20.0, "label": "Low Damage"},
                "moderate": {"min_percentage": 20.0, "max_percentage": 50.0, "label": "Moderate Damage"},
                "high": {"min_percentage": 50.0, "max_percentage": 75.0, "label": "High Damage"},
                "severe": {"min_percentage": 75.0, "max_percentage": 100.0, "label": "Severe Damage"},
            }
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def assign_severity_level(damage_pct: float, cfg: dict) -> Tuple[str, float]:
    """Assigns damage severity label and numerical score (0.0 - 1.0)."""
    levels = cfg.get("damage_severity_levels", {})
    if damage_pct <= 0.01:
        return "No Damage / Unaffected", 0.0
    elif damage_pct <= levels.get("low", {}).get("max_percentage", 20.0):
        return "Low Damage", 0.25
    elif damage_pct <= levels.get("moderate", {}).get("max_percentage", 50.0):
        return "Moderate Damage", 0.50
    elif damage_pct <= levels.get("high", {}).get("max_percentage", 75.0):
        return "High Damage", 0.75
    else:
        return "Severe Damage", 1.0


def run_crop_damage_assessment(
    classified_parcels_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    hazard_geojson_path: Path = Path("results/hazard/hazard_affected_area.geojson"),
    indices_dir: Path = Path("data/processed/indices"),
    before_date: str = "2026-04-22",
    after_date: str = "2026-09-09",
    output_damage_geojson_path: Path = Path("results/damage/crop_damage_assessment.geojson"),
    output_summary_csv_path: Path = Path("results/damage/crop_damage_summary.csv"),
    target_crs: str = "EPSG:32643",
) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Perform parcel-level hazard intersection and damage assessment.
    """
    output_damage_geojson_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_damage_thresholds()

    # 1. Load Data
    parcels_gdf = gpd.read_file(classified_parcels_path)
    hazard_gdf = gpd.read_file(hazard_geojson_path)

    # Standardize to UTM Zone 43N for metric calculations
    parcels_utm = parcels_gdf.to_crs(target_crs) if parcels_gdf.crs.to_string().upper() != target_crs.upper() else parcels_gdf.copy()
    hazard_utm = hazard_gdf.to_crs(target_crs) if hazard_gdf.crs.to_string().upper() != target_crs.upper() else hazard_gdf.copy()

    # Build spatial index of hazard polygons
    hazard_union = hazard_utm.union_all() if hasattr(hazard_utm, "union_all") else hazard_utm.unary_union

    # 2. Read NDVI Rasters for Zonal Impact Analysis
    p_ndvi_pre = indices_dir / before_date / "NDVI.tif"
    p_ndvi_post = indices_dir / after_date / "NDVI.tif"

    with rasterio.open(p_ndvi_pre) as s_pre, rasterio.open(p_ndvi_post) as s_post:
        ndvi_pre_arr = s_pre.read(1)
        ndvi_post_arr = s_post.read(1)
        transform = s_pre.transform

    print(f"\n[DAMAGE ASSESSMENT] Intersecting {len(parcels_utm)} parcels with flood inundation footprint...")

    damage_records = []
    crop_col = "predicted_crop" if "predicted_crop" in parcels_utm.columns else "crop_name"

    for idx, row in parcels_utm.iterrows():
        p_id = row["parcel_id"]
        crop = row.get(crop_col, "Unknown")
        taluk = row.get("taluk", "Ambasamudram")
        geom = row.geometry
        p_area_sq_m = geom.area
        p_area_ha = p_area_sq_m / 10000.0
        p_area_acres = p_area_sq_m / 4046.8564224

        # Calculate exact geometric intersection with inundation footprint
        affected_sq_m = 0.0
        if geom.intersects(hazard_union):
            inter_geom = geom.intersection(hazard_union)
            if not inter_geom.is_empty:
                affected_sq_m = inter_geom.area

        affected_ha = affected_sq_m / 10000.0
        affected_acres = affected_sq_m / 4046.8564224
        damage_pct = min(100.0, round((affected_sq_m / p_area_sq_m) * 100.0, 2)) if p_area_sq_m > 0 else 0.0

        # Sample pre/post NDVI within parcel
        try:
            p_mask = geometry_mask([geom], out_shape=ndvi_pre_arr.shape, transform=transform, invert=True)
            pre_vals = ndvi_pre_arr[p_mask]
            post_vals = ndvi_post_arr[p_mask]
            pre_vals = pre_vals[(pre_vals > -1.0) & (pre_vals <= 1.0)]
            post_vals = post_vals[(post_vals > -1.0) & (post_vals <= 1.0)]
            mean_ndvi_pre = float(np.nanmean(pre_vals)) if len(pre_vals) > 0 else 0.0
            mean_ndvi_post = float(np.nanmean(post_vals)) if len(post_vals) > 0 else 0.0
            delta_ndvi = round(mean_ndvi_post - mean_ndvi_pre, 4)
        except Exception:
            mean_ndvi_pre = 0.0
            mean_ndvi_post = 0.0
            delta_ndvi = 0.0

        severity_label, sev_score = assign_severity_level(damage_pct, cfg)

        damage_records.append({
            "parcel_id": p_id,
            "crop": crop,
            "taluk": taluk,
            "parcel_area_ha": round(p_area_ha, 4),
            "parcel_area_acres": round(p_area_acres, 4),
            "affected_area_ha": round(affected_ha, 4),
            "affected_area_acres": round(affected_acres, 4),
            "damage_percentage": damage_pct,
            "severity": severity_label,
            "severity_score": sev_score,
            "ndvi_before": round(mean_ndvi_pre, 4),
            "ndvi_after": round(mean_ndvi_post, 4),
            "delta_ndvi": delta_ndvi,
            "hazard_type": "Flood / Inundation",
            "observation_before": before_date,
            "observation_after": after_date,
            "confidence": float(row.get("confidence", 0.85)),
        })

    df_damage = pd.DataFrame(damage_records)

    # Attach attributes to GeoDataFrame
    for col in df_damage.columns:
        if col not in ["parcel_id"]:
            parcels_utm[col] = df_damage[col].values

    # Export GeoJSON deliverable (reprojected to EPSG:4326 for web clients)
    parcels_wgs84 = parcels_utm.to_crs("EPSG:4326")
    parcels_wgs84.to_file(output_damage_geojson_path, driver="GeoJSON")

    # Also synchronize to member3-fullstack/inputs/
    m3_damage_geojson = Path("member3-fullstack/inputs/crop_damage_assessment.geojson")
    if m3_damage_geojson.parent.exists():
        parcels_wgs84.to_file(m3_damage_geojson, driver="GeoJSON")

    # 3. Crop-Wise Damage Summary Table
    crop_summaries = []
    total_study_area_ha = df_damage["parcel_area_ha"].sum()
    total_study_affected_ha = df_damage["affected_area_ha"].sum()

    for c_name, grp in df_damage.groupby("crop"):
        p_count = len(grp)
        t_ha = grp["parcel_area_ha"].sum()
        t_ac = grp["parcel_area_acres"].sum()
        aff_ha = grp["affected_area_ha"].sum()
        aff_ac = grp["affected_area_acres"].sum()
        aff_parcels = int((grp["affected_area_ha"] > 0.001).sum())
        mean_dmg_pct = (aff_ha / t_ha) * 100.0 if t_ha > 0 else 0.0

        low_ha = grp[grp["severity"] == "Low Damage"]["affected_area_ha"].sum()
        mod_ha = grp[grp["severity"] == "Moderate Damage"]["affected_area_ha"].sum()
        high_ha = grp[grp["severity"] == "High Damage"]["affected_area_ha"].sum()
        sev_ha = grp[grp["severity"] == "Severe Damage"]["affected_area_ha"].sum()

        crop_summaries.append({
            "Crop": c_name,
            "Total_Parcels": p_count,
            "Affected_Parcels": aff_parcels,
            "Total_Area_Ha": round(t_ha, 2),
            "Total_Area_Acres": round(t_ac, 2),
            "Affected_Area_Ha": round(aff_ha, 2),
            "Affected_Area_Acres": round(aff_ac, 2),
            "Crop_Damage_Percentage": round(mean_dmg_pct, 2),
            "Low_Damage_Ha": round(low_ha, 2),
            "Moderate_Damage_Ha": round(mod_ha, 2),
            "High_Damage_Ha": round(high_ha, 2),
            "Severe_Damage_Ha": round(sev_ha, 2),
            "Share_of_Total_Damage_Pct": round((aff_ha / total_study_affected_ha) * 100.0, 2) if total_study_affected_ha > 0 else 0.0
        })

    df_summary = pd.DataFrame(crop_summaries)
    df_summary.sort_values(by="Affected_Area_Ha", ascending=False, inplace=True)
    df_summary.to_csv(output_summary_csv_path, index=False)

    # Export JSON version for FastAPI/React
    json_path = Path("member3-fullstack/inputs/crop_damage_summary.json")
    if json_path.parent.exists():
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "hazard_event": "Monsoon Flood / Inundation",
                "observation_before": before_date,
                "observation_after": after_date,
                "total_study_area_ha": round(total_study_area_ha, 2),
                "total_affected_area_ha": round(total_study_affected_ha, 2),
                "total_affected_parcels": int((df_damage['affected_area_ha'] > 0.001).sum()),
                "crop_damage_breakdown": crop_summaries,
                "severity_counts": df_damage["severity"].value_counts().to_dict()
            }, f, indent=2)

    print("\n[CROP DAMAGE SUMMARY]")
    print(df_summary.to_string(index=False))
    print(f"\n  [OK] Saved Crop Damage GeoJSON: {output_damage_geojson_path.resolve()}")
    print(f"  [OK] Saved Crop Damage Summary: {output_summary_csv_path.resolve()}")

    return parcels_utm, df_summary


if __name__ == "__main__":
    run_crop_damage_assessment()
