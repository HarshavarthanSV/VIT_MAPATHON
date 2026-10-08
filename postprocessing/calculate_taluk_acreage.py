"""
Taluk-Level Agricultural Crop Acreage Summary Module.
Member 2 - Agricultural Land Parcel & Crop Identification (Tirunelveli District).

Performs spatial join between classified agricultural parcels and official taluk boundaries
for Ambasamudram Taluk and Cheranmahadevi Taluk.
Computes parcel counts, area in hectares, area in acres, and percentage shares.
Outputs results/taluk_crop_acreage_summary.csv.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import geopandas as gpd


def compute_taluk_acreage_summary(
    classified_parcels_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    aoi_path: Path = Path("data/aoi/study_area.geojson"),
    output_summary_path: Path = Path("results/taluk_crop_acreage_summary.csv"),
    target_crs: str = "EPSG:32643",
) -> pd.DataFrame:
    """
    Perform spatial join and calculate crop acreage summaries for Ambasamudram and Cheranmahadevi taluks.
    """
    output_summary_path.parent.mkdir(parents=True, exist_ok=True)

    if not classified_parcels_path.exists():
        raise FileNotFoundError(f"Classified parcels file not found at: {classified_parcels_path}")
    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI boundary file not found at: {aoi_path}")

    # 1. Load Datasets
    parcels_gdf = gpd.read_file(classified_parcels_path)
    aoi_gdf = gpd.read_file(aoi_path)

    # 2. Harmonize Projected CRS (EPSG:32643)
    if parcels_gdf.crs is None or parcels_gdf.crs.to_string().upper() != target_crs.upper():
        parcels_gdf = parcels_gdf.to_crs(target_crs)
    if aoi_gdf.crs is None or aoi_gdf.crs.to_string().upper() != target_crs.upper():
        aoi_gdf = aoi_gdf.to_crs(target_crs)

    # Calculate metric parcel area in m²
    parcels_gdf["area_m2_exact"] = parcels_gdf.geometry.area
    parcels_gdf["area_ha_exact"] = parcels_gdf["area_m2_exact"] / 10000.0
    parcels_gdf["area_acres_exact"] = parcels_gdf["area_m2_exact"] / 4046.8564224

    # 3. Check for Taluk Column or Perform Spatial Join
    taluk_col = None
    for candidate in ["taluk_name", "taluk", "name", "admin_name"]:
        if candidate in aoi_gdf.columns:
            taluk_col = candidate
            break

    if taluk_col is None or aoi_gdf[taluk_col].nunique() < 2:
        # Check if parcels already contain taluk field
        if "taluk" in parcels_gdf.columns and parcels_gdf["taluk"].nunique() >= 2:
            joined_gdf = parcels_gdf.copy()
            taluk_field = "taluk"
        else:
            print("[WARN] Separate taluk boundary data is required for Ambasamudram-vs-Cheranmahadevi acreage statistics.")
            # Fallback to single area calculation
            joined_gdf = parcels_gdf.copy()
            joined_gdf["taluk"] = "Ambasamudram_Cheranmahadevi_Combined"
            taluk_field = "taluk"
    else:
        # Spatial join between parcel centroids (to avoid multi-taluk boundary splits) and taluk polygons
        parcels_centroids = parcels_gdf.copy()
        parcels_centroids["centroid_geom"] = parcels_centroids.geometry.centroid
        parcels_centroids.set_geometry("centroid_geom", inplace=True)

        joined_centroids = gpd.sjoin(parcels_centroids, aoi_gdf[[taluk_col, "geometry"]], how="inner", predicate="intersects")
        parcels_gdf["taluk_spatial"] = joined_centroids[taluk_col]

        # Fill any parcels outside boundary with existing taluk column or nearest
        if "taluk" in parcels_gdf.columns:
            parcels_gdf["taluk_final"] = parcels_gdf["taluk_spatial"].fillna(parcels_gdf["taluk"])
        else:
            parcels_gdf["taluk_final"] = parcels_gdf["taluk_spatial"].fillna("Unassigned")

        joined_gdf = parcels_gdf.copy()
        taluk_field = "taluk_final"

    # Identify Crop column
    crop_col = None
    for candidate in ["predicted_crop", "crop_name", "crop_class", "class"]:
        if candidate in joined_gdf.columns:
            crop_col = candidate
            break

    if crop_col is None:
        raise KeyError("Could not identify crop classification column in parcels.")

    # 4. Compute Summary Aggregations
    summary_rows = []
    unique_taluks = sorted(joined_gdf[taluk_field].unique())

    for taluk_val in unique_taluks:
        taluk_subset = joined_gdf[joined_gdf[taluk_field] == taluk_val]
        taluk_total_ha = taluk_subset["area_ha_exact"].sum()
        taluk_total_acres = taluk_subset["area_acres_exact"].sum()
        taluk_total_parcels = len(taluk_subset)

        for crop_val, crop_subset in taluk_subset.groupby(crop_col):
            p_count = len(crop_subset)
            ha = crop_subset["area_ha_exact"].sum()
            acres = crop_subset["area_acres_exact"].sum()
            pct = (ha / taluk_total_ha) * 100.0 if taluk_total_ha > 0 else 0.0

            summary_rows.append({
                "Taluk": taluk_val,
                "Crop": crop_val,
                "Parcel_Count": p_count,
                "Area_Hectares": round(ha, 4),
                "Area_Acres": round(acres, 4),
                "Percentage_of_Taluk": round(pct, 2),
            })

        # Add Subtotal Row for the Taluk
        summary_rows.append({
            "Taluk": f"{taluk_val} (Subtotal)",
            "Crop": "ALL_CROPS",
            "Parcel_Count": taluk_total_parcels,
            "Area_Hectares": round(taluk_total_ha, 4),
            "Area_Acres": round(taluk_total_acres, 4),
            "Percentage_of_Taluk": 100.0,
        })

    # Add Grand Total Row
    grand_total_ha = joined_gdf["area_ha_exact"].sum()
    grand_total_acres = joined_gdf["area_acres_exact"].sum()
    summary_rows.append({
        "Taluk": "GRAND_TOTAL",
        "Crop": "ALL_CROPS",
        "Parcel_Count": len(joined_gdf),
        "Area_Hectares": round(grand_total_ha, 4),
        "Area_Acres": round(grand_total_acres, 4),
        "Percentage_of_Taluk": 100.0,
    })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(output_summary_path, index=False)

    print(f"\n[TALUK ACREAGE] Summary saved to: {output_summary_path.resolve()}")
    print("-" * 75)
    print(df_summary.to_string(index=False))
    print("-" * 75)

    return df_summary


if __name__ == "__main__":
    compute_taluk_acreage_summary()
