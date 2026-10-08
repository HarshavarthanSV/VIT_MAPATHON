"""
VIT MAPATHON — Hazards Router (Member 3 / Member 2 Integration)
Serves natural hazard footprints, inundation layers, and disaster event metadata.
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

logger = logging.getLogger("HazardsRouter")
router = APIRouter(prefix="/api/hazards", tags=["hazards"])

_cached_hazard_geojson = None


def get_hazard_geojson() -> Dict[str, Any]:
    global _cached_hazard_geojson
    if _cached_hazard_geojson is None:
        path = resolve_artifact_path("hazard_affected_area.geojson")
        if not path:
            # Fallback path search in results/hazard/
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cand = os.path.join(repo_root, "results", "hazard", "hazard_affected_area.geojson")
            if os.path.exists(cand):
                path = cand
            else:
                raise HTTPException(status_code=404, detail="hazard_affected_area.geojson deliverable not found.")
        with open(path, "r", encoding="utf-8") as f:
            _cached_hazard_geojson = json.load(f)
    return _cached_hazard_geojson


@router.get("/latest", response_model=Dict[str, Any])
def get_latest_hazard():
    """
    Returns the latest detected natural hazard event (e.g. Monsoon Flood / Inundation)
    with full GeoJSON FeatureCollection footprint, temporal observation dates, and summary metrics.
    """
    geojson = get_hazard_geojson()
    features = geojson.get("features", [])

    total_area_ha = sum(f.get("properties", {}).get("area_ha", 0.0) for f in features)
    before_date = features[0].get("properties", {}).get("observation_before", "2026-04-22") if features else "2026-04-22"
    after_date = features[0].get("properties", {}).get("observation_after", "2026-09-09") if features else "2026-09-09"
    hazard_type = features[0].get("properties", {}).get("hazard_type", "Flood / Heavy Rainfall Inundation") if features else "Flood"

    return {
        "hazard_id": "HAZARD_EVENT_2026_09",
        "hazard_type": hazard_type,
        "observation_before": before_date,
        "observation_after": after_date,
        "total_inundated_area_ha": round(total_area_ha, 2),
        "total_inundated_area_acres": round(total_area_ha * 2.47105, 2),
        "total_hazard_polygons": len(features),
        "source": "Sentinel-2 Level-2A Multi-Temporal Change Detection (NDWI / LSWI / Delta NDVI)",
        "geojson": geojson
    }


@router.get("", response_model=List[Dict[str, Any]])
def list_hazards():
    """
    Returns list of all cataloged hazard events in the study area.
    """
    latest = get_latest_hazard()
    return [
        {
            "hazard_id": latest["hazard_id"],
            "hazard_type": latest["hazard_type"],
            "observation_before": latest["observation_before"],
            "observation_after": latest["observation_after"],
            "total_inundated_area_ha": latest["total_inundated_area_ha"],
            "total_hazard_polygons": latest["total_hazard_polygons"],
            "status": "Verified via Multi-Temporal Sentinel-2 Imagery"
        }
    ]


@router.get("/{hazard_id}", response_model=Dict[str, Any])
def get_hazard_by_id(hazard_id: str):
    """
    Returns a specific hazard feature or event by ID.
    """
    geojson = get_hazard_geojson()
    for feat in geojson.get("features", []):
        if feat.get("properties", {}).get("hazard_id") == hazard_id:
            return feat
    if hazard_id in ["HAZARD_EVENT_2026_09", "latest"]:
        return get_latest_hazard()
    raise HTTPException(status_code=404, detail=f"Hazard ID '{hazard_id}' not found.")
