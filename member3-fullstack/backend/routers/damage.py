"""
VIT MAPATHON — Crop Damage Assessment & Fund Priority Router (Member 3 / Member 2 Integration)
Serves parcel-level damage intersections, crop summaries, severity breakdowns, and transparent relief allocations.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except (ImportError, Exception):
    text = None
    Session = None

from database import is_db_connected, get_db, resolve_artifact_path

logger = logging.getLogger("DamageRouter")
router = APIRouter(prefix="/api", tags=["damage-and-relief"])

_cached_damage_geojson = None
_cached_damage_summary = None
_cached_fund_priority = None


def get_damage_geojson() -> Dict[str, Any]:
    global _cached_damage_geojson
    if _cached_damage_geojson is None:
        path = resolve_artifact_path("crop_damage_assessment.geojson")
        if not path:
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cand = os.path.join(repo_root, "results", "damage", "crop_damage_assessment.geojson")
            if os.path.exists(cand):
                path = cand
            else:
                raise HTTPException(status_code=404, detail="crop_damage_assessment.geojson deliverable not found.")
        with open(path, "r", encoding="utf-8") as f:
            _cached_damage_geojson = json.load(f)
    return _cached_damage_geojson


def get_damage_summary_json() -> Dict[str, Any]:
    global _cached_damage_summary
    if _cached_damage_summary is None:
        path = resolve_artifact_path("crop_damage_summary.json")
        if not path:
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cand = os.path.join(repo_root, "member3-fullstack", "inputs", "crop_damage_summary.json")
            if os.path.exists(cand):
                path = cand
            else:
                raise HTTPException(status_code=404, detail="crop_damage_summary.json not found.")
        with open(path, "r", encoding="utf-8") as f:
            _cached_damage_summary = json.load(f)
    return _cached_damage_summary


def get_fund_priority_json() -> Dict[str, Any]:
    global _cached_fund_priority
    if _cached_fund_priority is None:
        path = resolve_artifact_path("fund_priority_summary.json")
        if not path:
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cand = os.path.join(repo_root, "results", "damage", "fund_priority_summary.json")
            if os.path.exists(cand):
                path = cand
            else:
                raise HTTPException(status_code=404, detail="fund_priority_summary.json not found.")
        with open(path, "r", encoding="utf-8") as f:
            _cached_fund_priority = json.load(f)
    return _cached_fund_priority


@router.get("/damage/latest", response_model=Dict[str, Any])
def get_latest_damage_assessment(
    crop: Optional[str] = Query(None, description="Filter by crop (Paddy, Banana, Non-Crop)"),
    severity: Optional[str] = Query(None, description="Filter by severity (Low Damage, Moderate Damage, High Damage, Severe Damage)"),
    affected_only: bool = Query(False, description="Return only parcels with affected_area > 0")
):
    """
    Returns GeoJSON FeatureCollection of all 293 cadastral parcels enriched with
    hazard intersection metrics, affected area in hectares, damage percentage, and severity.
    """
    geojson = get_damage_geojson()
    features = geojson.get("features", [])

    filtered = []
    for f in features:
        props = f.get("properties", {})
        if crop and props.get("crop") != crop:
            continue
        if severity and props.get("severity") != severity:
            continue
        if affected_only and props.get("affected_area_ha", 0.0) <= 0.0001:
            continue
        filtered.append(f)

    return {
        "type": "FeatureCollection",
        "total_returned": len(filtered),
        "hazard_type": "Flood / Inundation",
        "observation_dates": {"before": "2026-04-22", "after": "2026-09-09"},
        "features": filtered
    }


@router.get("/damage/by-crop", response_model=Dict[str, Any])
def get_damage_by_crop():
    """
    Returns aggregated crop-wise damage summary (total parcels, affected area ha, damage %, severity distribution).
    """
    return get_damage_summary_json()


@router.get("/damage/by-severity", response_model=Dict[str, Any])
def get_damage_by_severity():
    """
    Returns summary of parcels and affected hectares grouped by severity level.
    """
    geojson = get_damage_geojson()
    features = geojson.get("features", [])

    severity_groups = {
        "Severe Damage": {"parcel_count": 0, "affected_area_ha": 0.0, "total_parcel_area_ha": 0.0},
        "High Damage": {"parcel_count": 0, "affected_area_ha": 0.0, "total_parcel_area_ha": 0.0},
        "Moderate Damage": {"parcel_count": 0, "affected_area_ha": 0.0, "total_parcel_area_ha": 0.0},
        "Low Damage": {"parcel_count": 0, "affected_area_ha": 0.0, "total_parcel_area_ha": 0.0},
        "No Damage / Unaffected": {"parcel_count": 0, "affected_area_ha": 0.0, "total_parcel_area_ha": 0.0},
    }

    for f in features:
        props = f.get("properties", {})
        sev = props.get("severity", "No Damage / Unaffected")
        if sev not in severity_groups:
            sev = "No Damage / Unaffected"
        severity_groups[sev]["parcel_count"] += 1
        severity_groups[sev]["affected_area_ha"] += props.get("affected_area_ha", 0.0)
        severity_groups[sev]["total_parcel_area_ha"] += props.get("parcel_area_ha", 0.0)

    for k in severity_groups:
        severity_groups[k]["affected_area_ha"] = round(severity_groups[k]["affected_area_ha"], 2)
        severity_groups[k]["total_parcel_area_ha"] = round(severity_groups[k]["total_parcel_area_ha"], 2)

    return {
        "severity_levels": severity_groups,
        "total_parcels": len(features),
        "source": "Sentinel-2 Multi-Temporal Inundation Assessment"
    }


@router.get("/fund-priority", response_model=Dict[str, Any])
def get_fund_priority():
    """
    Returns multi-criteria priority scores and ranked top-priority affected parcels.
    """
    return get_fund_priority_json()


@router.get("/fund-allocation", response_model=Dict[str, Any])
def calculate_fund_allocation(
    total_fund: float = Query(10000000.0, ge=1000.0, description="Total relief fund pool in INR (e.g. 10000000 for 1 Crore)")
):
    """
    Calculates transparent, proportional disaster relief fund allocation based on multi-criteria priority scores:
    Allocation = Total_Fund * (Priority_Score / Total_Priority_Sum).
    Clearly labeled as AI/GIS decision support recommendation.
    """
    priority_data = get_fund_priority_json()
    total_priority = priority_data.get("total_priority_score_sum", 1.9461)
    crop_summaries = priority_data.get("crop_allocation_summary", [])

    crop_results = []
    for c in crop_summaries:
        c_score = c.get("Crop_Priority_Score", 0.0)
        if total_priority > 0 and c_score > 0:
            c_alloc = round((c_score / total_priority) * total_fund, 2)
            c_share = round((c_score / total_priority) * 100.0, 2)
        else:
            c_alloc = 0.0
            c_share = 0.0

        crop_results.append({
            "Crop": c.get("Crop"),
            "Total_Parcels": c.get("Total_Parcels"),
            "Affected_Parcels": c.get("Affected_Parcels"),
            "Affected_Area_Ha": c.get("Affected_Area_Ha"),
            "Crop_Priority_Score": c_score,
            "Recommended_Allocation_INR": c_alloc,
            "Allocation_Share_Pct": c_share,
        })

    # Recalculate top priority parcels
    top_parcels = []
    for p in priority_data.get("top_priority_parcels", []):
        p_score = p.get("priority_score", 0.0)
        p_alloc = round((p_score / total_priority) * total_fund, 2) if total_priority > 0 else 0.0
        p_copy = dict(p)
        p_copy["recommended_relief_inr"] = p_alloc
        top_parcels.append(p_copy)

    return {
        "status": "AI/GIS-based decision-support recommendation — requires statutory authority verification.",
        "input_relief_fund_pool_inr": total_fund,
        "total_priority_score_sum": total_priority,
        "priority_formula": priority_data.get("priority_formula", ""),
        "crop_allocation_recommendations": crop_results,
        "top_priority_parcels": top_parcels,
        "disclaimer": "This allocation is generated through mathematical Multi-Criteria Decision Analysis (MCDA) based on satellite-observed inundated hectares and damage percentage. Final disbursement requires revenue department field verification."
    }
