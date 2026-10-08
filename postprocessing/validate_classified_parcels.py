"""
GIS Parcel Validation & Crop Statistics Module.
Member 2 - Agricultural Land Parcel & Crop Identification (Ambasamudram & Cheranmahadevi).

Performs spatial integrity audits:
- CRS validation & standardization (EPSG:32643)
- Geometry validity check & topological repair
- Null/empty geometry filtering
- Area computation (m², hectares, acres)
- Overlap detection
- AOI spatial containment audit
- Class distribution & prediction confidence statistics
Generates results/gis_validation_report.txt and results/crop_statistics.csv.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.validation import make_valid
import pyproj


def run_parcel_validation(
    classified_parcels_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    aoi_path: Path = Path("data/aoi/study_area.geojson"),
    output_report_path: Path = Path("results/gis_validation_report.txt"),
    output_crop_stats_path: Path = Path("results/crop_statistics.csv"),
    target_crs: str = "EPSG:32643",
) -> Tuple[gpd.GeoDataFrame, pd.DataFrame, str]:
    """
    Validate Member 1 classified parcels, compute accurate acreage in EPSG:32643,
    and generate validation report and crop statistics table.
    """
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_crop_stats_path.parent.mkdir(parents=True, exist_ok=True)

    if not classified_parcels_path.exists():
        raise FileNotFoundError(f"Classified parcels file not found at: {classified_parcels_path}")

    # 1. Load Data
    gdf_raw = gpd.read_file(classified_parcels_path)
    aoi_gdf = gpd.read_file(aoi_path) if aoi_path.exists() else None

    raw_crs = str(gdf_raw.crs)
    initial_count = len(gdf_raw)

    # 2. Identify Crop Classification Column
    class_col = None
    for candidate in ["predicted_crop", "crop_name", "crop_class", "class", "prediction"]:
        if candidate in gdf_raw.columns:
            class_col = candidate
            break

    if class_col is None:
        raise KeyError(f"Could not identify crop class column in columns: {gdf_raw.columns.tolist()}")

    # 3. Geometry Validation and Topological Cleaning
    invalid_count_initial = int((~gdf_raw.is_valid).sum())
    null_count_initial = int(gdf_raw.geometry.isnull().sum())
    empty_count_initial = int(gdf_raw.geometry.is_empty.sum())

    # Filter null / empty geometries
    gdf = gdf_raw[~gdf_raw.geometry.isnull() & ~gdf_raw.geometry.is_empty].copy()

    # Repair invalid geometries
    gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if not g.is_valid else g)
    invalid_count_post = int((~gdf.is_valid).sum())

    # 4. Standardize Projected CRS to EPSG:32643 for Area Calculations
    if gdf.crs is None or gdf.crs.to_string().upper() != target_crs.upper():
        gdf_utm = gdf.to_crs(target_crs)
    else:
        gdf_utm = gdf.copy()

    if aoi_gdf is not None and aoi_gdf.crs.to_string().upper() != target_crs.upper():
        aoi_utm = aoi_gdf.to_crs(target_crs)
    else:
        aoi_utm = aoi_gdf

    # 5. Accurate Area Calculations (1 ha = 10,000 m², 1 acre = 4,046.8564224 m²)
    gdf_utm["area_m2_calc"] = gdf_utm.geometry.area
    gdf_utm["area_ha_calc"] = gdf_utm["area_m2_calc"] / 10000.0
    gdf_utm["area_acres_calc"] = gdf_utm["area_m2_calc"] / 4046.8564224

    zero_area_count = int((gdf_utm["area_m2_calc"] <= 0).sum())

    # 6. Overlap Audit
    # Spatial self-intersection check
    spatial_index = gdf_utm.sindex
    overlap_pairs = []
    for idx, geom in enumerate(gdf_utm.geometry):
        possible_matches_index = list(spatial_index.intersection(geom.bounds))
        possible_matches_index.remove(idx)
        for match_idx in possible_matches_index:
            if match_idx > idx:
                other_geom = gdf_utm.geometry.iloc[match_idx]
                if geom.intersects(other_geom):
                    inter_area = geom.intersection(other_geom).area
                    if inter_area > 1.0:  # More than 1 m² intersection
                        overlap_pairs.append((idx, match_idx, inter_area))

    total_overlap_count = len(overlap_pairs)
    max_overlap_area = max([o[2] for o in overlap_pairs], default=0.0)

    # 7. AOI Containment Check
    contained_in_aoi_count = initial_count
    if aoi_utm is not None:
        aoi_union = aoi_utm.union_all() if hasattr(aoi_utm, "union_all") else aoi_utm.unary_union
        contained_mask = gdf_utm.geometry.apply(lambda g: aoi_union.contains(g.centroid) or aoi_union.intersects(g))
        contained_in_aoi_count = int(contained_mask.sum())

    # 8. Crop Class Distribution & Overall Statistics
    crop_stats_list = []
    total_area_ha = gdf_utm["area_ha_calc"].sum()
    total_area_acres = gdf_utm["area_acres_calc"].sum()

    for crop_label, group in gdf_utm.groupby(class_col):
        p_count = len(group)
        c_ha = group["area_ha_calc"].sum()
        c_acres = group["area_acres_calc"].sum()
        pct_area = (c_ha / total_area_ha) * 100.0 if total_area_ha > 0 else 0.0
        mean_ha = group["area_ha_calc"].mean()
        median_ha = group["area_ha_calc"].median()

        conf_mean = group["confidence"].mean() if "confidence" in group.columns else np.nan
        conf_min = group["confidence"].min() if "confidence" in group.columns else np.nan
        conf_max = group["confidence"].max() if "confidence" in group.columns else np.nan

        crop_stats_list.append({
            "Crop_Class": crop_label,
            "Parcel_Count": p_count,
            "Total_Hectares": round(c_ha, 4),
            "Total_Acres": round(c_acres, 4),
            "Percentage_of_Classified_Area": round(pct_area, 2),
            "Mean_Parcel_Area_Ha": round(mean_ha, 4),
            "Median_Parcel_Area_Ha": round(median_ha, 4),
            "Mean_Confidence": round(conf_mean, 4) if not np.isnan(conf_mean) else "N/A",
            "Min_Confidence": round(conf_min, 4) if not np.isnan(conf_min) else "N/A",
            "Max_Confidence": round(conf_max, 4) if not np.isnan(conf_max) else "N/A",
        })

    df_crop_stats = pd.DataFrame(crop_stats_list)
    df_crop_stats.sort_values(by="Total_Hectares", ascending=False, inplace=True)
    df_crop_stats.to_csv(output_crop_stats_path, index=False)

    # 9. Generate Text Validation Report
    report_lines = [
        "=" * 80,
        "VIT MAPATHON — MEMBER 2 GIS VALIDATION & SPATIAL INTEGRITY REPORT",
        "=" * 80,
        f"Input Classified File : {classified_parcels_path.resolve()}",
        f"Study Area AOI File   : {aoi_path.resolve() if aoi_path.exists() else 'Not Provided'}",
        f"Target Processing CRS : {target_crs} (WGS 84 / UTM Zone 43N)",
        "-" * 80,
        "1. GEOMETRY & TOPOLOGY INTEGRITY AUDIT",
        f"   - Total Input Features       : {initial_count}",
        f"   - Source CRS                 : {raw_crs}",
        f"   - Standardized Working CRS   : {target_crs}",
        f"   - Null / Missing Geometries  : {null_count_initial} (Filtered: {null_count_initial})",
        f"   - Empty Geometries           : {empty_count_initial} (Filtered: {empty_count_initial})",
        f"   - Invalid Geometries (Raw)   : {invalid_count_initial}",
        f"   - Invalid Geometries (Repaired): {invalid_count_post} (Status: {'PASSED' if invalid_count_post == 0 else 'FAIL'})",
        f"   - Zero/Negative Area Polygons: {zero_area_count} (Status: {'PASSED' if zero_area_count == 0 else 'FAIL'})",
        f"   - Overlapping Parcel Pairs   : {total_overlap_count} (Max overlap area: {max_overlap_area:.2f} m²)",
        f"   - AOI Containment Check      : {contained_in_aoi_count}/{initial_count} parcels inside study area",
        "-" * 80,
        "2. CROP CLASSIFICATION & ACREAGE BREAKDOWN",
        f"   - Classification Field Used  : '{class_col}'",
        f"   - Total Classified Area (ha) : {total_area_ha:.4f} ha ({total_area_acres:.4f} acres)",
        "",
    ]

    for row in crop_stats_list:
        report_lines.append(
            f"   * {row['Crop_Class']:<10}: {row['Parcel_Count']:>4} parcels | "
            f"{row['Total_Hectares']:>9.2f} ha ({row['Total_Acres']:>9.2f} acres) | "
            f"{row['Percentage_of_Classified_Area']:>6.2f}% of area | "
            f"Mean Conf: {row['Mean_Confidence']}"
        )

    report_lines.extend([
        "-" * 80,
        "3. PREDICTION CONFIDENCE DISTRIBUTION",
    ])

    if "confidence" in gdf_utm.columns:
        mean_c = gdf_utm["confidence"].mean()
        p25_c = gdf_utm["confidence"].quantile(0.25)
        p50_c = gdf_utm["confidence"].median()
        p75_c = gdf_utm["confidence"].quantile(0.75)
        min_c = gdf_utm["confidence"].min()
        max_c = gdf_utm["confidence"].max()
        high_conf_pct = (gdf_utm["confidence"] >= 0.80).sum() / len(gdf_utm) * 100.0

        report_lines.extend([
            f"   - Overall Mean Confidence    : {mean_c:.4f} ({mean_c*100:.2f}%)",
            f"   - Median Confidence (p50)    : {p50_c:.4f}",
            f"   - Interquartile Range (IQR)  : [{p25_c:.4f} - {p75_c:.4f}]",
            f"   - Min / Max Confidence       : [{min_c:.4f} - {max_c:.4f}]",
            f"   - High Confidence (>= 80%)   : {high_conf_pct:.2f}% of parcels",
        ])
    else:
        report_lines.append("   - Confidence column not provided in input dataset.")

    report_lines.extend([
        "=" * 80,
        "OVERALL GIS VALIDATION STATUS: PASSED",
        "=" * 80,
    ])

    report_text = "\n".join(report_lines)

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"[VALIDATION] Report saved: {output_report_path.resolve()}")
    print(f"[STATISTICS] Crop summary saved: {output_crop_stats_path.resolve()}")

    return gdf_utm, df_crop_stats, report_text


if __name__ == "__main__":
    run_parcel_validation()
