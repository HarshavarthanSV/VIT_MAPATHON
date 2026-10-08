"""
Transparent Agricultural Disaster Fund Priority & Relief Allocation Engine.
Member 2 - Agricultural Land Parcel & Crop Identification (Ambasamudram & Cheranmahadevi).

Implements multi-criteria decision analysis (MCDA) for equitable, transparent disaster relief priority:
- Priority Score = (w1 * Norm_Affected_Area) + (w2 * Norm_Damage_Pct) + (w3 * Severity_Score) * Crop_Economic_Factor
- Recommended Relief Allocation = Total_Fund * (Parcel_Priority / Total_Priority)
- Supports user-defined relief fund amounts (default ₹10,000,000 baseline)
- Clearly labeled as "AI/GIS-based decision-support recommendation — requires statutory authority verification".

Exports:
- results/damage/fund_priority_summary.csv
- results/damage/fund_priority_summary.json
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import numpy as np
import pandas as pd
import geopandas as gpd


def load_priority_config(config_path: Path = Path("config/damage_thresholds.json")) -> dict:
    if not config_path.exists():
        return {
            "priority_score_weights": {
                "weight_affected_area": 0.40,
                "weight_damage_percentage": 0.35,
                "weight_severity_score": 0.25,
            },
            "fund_allocation_policy": {
                "crop_economic_weights": {"Paddy": 1.0, "Banana": 1.15, "Non-Crop": 0.0}
            }
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_fund_priority_and_allocation(
    damage_geojson_path: Path = Path("results/damage/crop_damage_assessment.geojson"),
    total_relief_fund: float = 10000000.0,  # Default ₹1 Crore (10 Million INR) baseline
    output_csv_path: Path = Path("results/damage/fund_priority_summary.csv"),
    output_json_path: Path = Path("results/damage/fund_priority_summary.json"),
) -> Tuple[pd.DataFrame, dict]:
    """
    Calculate parcel-level and crop-level priority ranking and proportional fund allocation.
    """
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_priority_config()

    w_cfg = cfg.get("priority_score_weights", {})
    w1 = float(w_cfg.get("weight_affected_area", 0.40))
    w2 = float(w_cfg.get("weight_damage_percentage", 0.35))
    w3 = float(w_cfg.get("weight_severity_score", 0.25))

    crop_weights = cfg.get("fund_allocation_policy", {}).get("crop_economic_weights", {
        "Paddy": 1.0, "Banana": 1.15, "Non-Crop": 0.0
    })

    # 1. Load Damage Assessment Data
    gdf_damage = gpd.read_file(damage_geojson_path)

    # Filter to affected parcels or all agricultural parcels
    max_aff_area = float(gdf_damage["affected_area_ha"].max())
    if max_aff_area <= 0:
        max_aff_area = 1.0

    priority_scores = []
    norm_aff_areas = []
    norm_dmg_pcts = []

    for idx, row in gdf_damage.iterrows():
        aff_ha = float(row.get("affected_area_ha", 0.0))
        dmg_pct = float(row.get("damage_percentage", 0.0))
        sev_score = float(row.get("severity_score", 0.0))
        crop = row.get("crop", "Unknown")

        # Normalize features (0.0 - 1.0)
        norm_area = aff_ha / max_aff_area
        norm_pct = dmg_pct / 100.0

        econ_weight = crop_weights.get(crop, 1.0)

        # Compute Transparent Weighted Score
        if aff_ha > 0.0001 and econ_weight > 0.0:
            score = ((w1 * norm_area) + (w2 * norm_pct) + (w3 * sev_score)) * econ_weight
        else:
            score = 0.0

        norm_aff_areas.append(round(norm_area, 4))
        norm_dmg_pcts.append(round(norm_pct, 4))
        priority_scores.append(round(score, 5))

    gdf_damage["priority_score"] = priority_scores
    gdf_damage["norm_affected_area"] = norm_aff_areas
    gdf_damage["norm_damage_pct"] = norm_dmg_pcts

    # 2. Compute Proportional Relief Allocation
    total_priority = sum(priority_scores)

    recommended_allocations = []
    for score in priority_scores:
        if total_priority > 0 and score > 0:
            alloc = round((score / total_priority) * total_relief_fund, 2)
        else:
            alloc = 0.0
        recommended_allocations.append(alloc)

    gdf_damage["recommended_relief_inr"] = recommended_allocations

    # 3. Export Updated GeoJSON
    gdf_damage.to_file(damage_geojson_path, driver="GeoJSON")
    m3_damage_geojson = Path("member3-fullstack/inputs/crop_damage_assessment.geojson")
    if m3_damage_geojson.parent.exists():
        gdf_damage.to_file(m3_damage_geojson, driver="GeoJSON")

    # 4. Generate Crop-Level Priority & Fund Summary Table
    crop_alloc_rows = []
    for c_name, grp in gdf_damage.groupby("crop"):
        p_cnt = len(grp)
        aff_cnt = int((grp["affected_area_ha"] > 0.001).sum())
        tot_ha = grp["parcel_area_ha"].sum()
        aff_ha = grp["affected_area_ha"].sum()
        c_priority = grp["priority_score"].sum()
        c_alloc = grp["recommended_relief_inr"].sum()
        alloc_pct = (c_alloc / total_relief_fund) * 100.0 if total_relief_fund > 0 else 0.0

        crop_alloc_rows.append({
            "Crop": c_name,
            "Total_Parcels": p_cnt,
            "Affected_Parcels": aff_cnt,
            "Total_Area_Ha": round(tot_ha, 2),
            "Affected_Area_Ha": round(aff_ha, 2),
            "Crop_Priority_Score": round(c_priority, 4),
            "Recommended_Allocation_INR": round(c_alloc, 2),
            "Allocation_Share_Pct": round(alloc_pct, 2),
        })

    df_crop_alloc = pd.DataFrame(crop_alloc_rows)
    df_crop_alloc.sort_values(by="Recommended_Allocation_INR", ascending=False, inplace=True)
    df_crop_alloc.to_csv(output_csv_path, index=False)

    # 5. Top Ranked Priority Parcels
    top_parcels = gdf_damage[gdf_damage["priority_score"] > 0].sort_values(
        by="priority_score", ascending=False
    )[[
        "parcel_id", "crop", "taluk", "parcel_area_ha", "affected_area_ha",
        "damage_percentage", "severity", "priority_score", "recommended_relief_inr"
    ]].head(15).to_dict(orient="records")

    summary_payload = {
        "status": "AI/GIS-based decision-support recommendation — requires statutory authority verification.",
        "total_relief_fund_pool_inr": total_relief_fund,
        "total_priority_score_sum": round(total_priority, 4),
        "priority_formula": w_cfg.get("formula_description", ""),
        "crop_allocation_summary": crop_alloc_rows,
        "highest_priority_crop": df_crop_alloc.iloc[0]["Crop"] if not df_crop_alloc.empty else "None",
        "top_priority_parcels": top_parcels,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    # Synchronize to member3 inputs
    m3_fund_json = Path("member3-fullstack/inputs/fund_priority_summary.json")
    if m3_fund_json.parent.exists():
        with open(m3_fund_json, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)

    print("\n[TRANSPARENT RELIEF FUND ALLOCATION]")
    print(df_crop_alloc.to_string(index=False))
    print(f"\n  [OK] Saved Fund Priority CSV : {output_csv_path.resolve()}")
    print(f"  [OK] Saved Fund Priority JSON: {output_json_path.resolve()}")

    return df_crop_alloc, summary_payload


if __name__ == "__main__":
    calculate_fund_priority_and_allocation()
