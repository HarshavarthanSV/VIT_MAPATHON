"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
Layers Router: Serves real administrative places, river waterways, and highway infrastructure.
"""

import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from database import resolve_artifact_path, load_json_artifact

logger = logging.getLogger("LayersRouter")
router = APIRouter(prefix="/api", tags=["layers"])


@router.get("/places", response_model=List[Dict[str, Any]])
def get_places():
    """
    Returns real town and village landmark points across Ambasamudram & Cheranmahadevi Taluks.
    """
    try:
        path = resolve_artifact_path("real_places.json")
        if not path:
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading places: {e}")
        return []


@router.get("/infrastructure", response_model=Dict[str, Any])
def get_infrastructure():
    """
    Returns real Thamirabarani River waterways and highway infrastructure lines.
    """
    try:
        path = resolve_artifact_path("real_infrastructure.geojson")
        if not path:
            return {"type": "FeatureCollection", "features": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading infrastructure: {e}")
        return {"type": "FeatureCollection", "features": []}
