"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
Parcels Router: Serves GeoJSON parcel vector layers with dynamic filtering.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import is_db_connected, get_db, load_json_artifact, resolve_artifact_path

logger = logging.getLogger("ParcelsRouter")
router = APIRouter(prefix="/api/parcels", tags=["parcels"])

# In-memory cache for fast GeoJSON serving in fallback mode
_cached_geojson = None


def get_cached_geojson() -> Dict[str, Any]:
    global _cached_geojson
    if _cached_geojson is None:
        path = resolve_artifact_path("classified_parcels.geojson")
        if not path:
            raise HTTPException(status_code=404, detail="classified_parcels.geojson deliverable not found.")
        with open(path, "r", encoding="utf-8") as f:
            _cached_geojson = json.load(f)
    return _cached_geojson


@router.get("", response_model=Dict[str, Any])
def get_parcels(
    crop: Optional[str] = Query(None, description="Filter by crop name: Paddy, Banana, Other"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    limit: Optional[int] = Query(None, ge=1, description="Optional maximum parcel count"),
    db: Optional[Session] = Depends(get_db)
):
    """
    Returns GeoJSON FeatureCollection of classified agricultural parcels.
    Supports dynamic filtering by crop type and confidence threshold.
    Queries PostGIS spatial database if connected; otherwise falls back to GeoJSON deliverable.
    """
    if is_db_connected() and db is not None:
        try:
            sql = """
                SELECT 
                    parcel_id,
                    predicted_crop,
                    confidence,
                    area_sq_km,
                    area_ha,
                    prob_paddy,
                    prob_banana,
                    prob_other,
                    ST_AsGeoJSON(geom) AS geom_json
                FROM agricultural_parcels
                WHERE (:crop IS NULL OR predicted_crop = :crop)
                  AND (:min_conf IS NULL OR confidence >= :min_conf)
                ORDER BY id ASC
            """
            if limit:
                sql += f" LIMIT {limit}"

            rows = db.execute(text(sql), {"crop": crop, "min_conf": min_confidence}).fetchall()
            features = []
            for r in rows:
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(r.geom_json),
                    "properties": {
                        "parcel_id": r.parcel_id,
                        "predicted_crop": r.predicted_crop,
                        "confidence": r.confidence,
                        "area_sq_km": r.area_sq_km,
                        "area_ha": r.area_ha,
                        "prob_paddy": r.prob_paddy,
                        "prob_banana": r.prob_banana,
                        "prob_other": r.prob_other
                    }
                })

            return {
                "type": "FeatureCollection",
                "source": "PostGIS",
                "total_features": len(features),
                "features": features
            }
        except Exception as e:
            logger.warning(f"PostGIS query failed: {e}. Falling back to GeoJSON deliverable.")

    # Fallback to file-based deliverable
    raw_data = get_cached_geojson()
    features = raw_data.get("features", [])

    filtered_features = []
    for feat in features:
        props = feat.get("properties", {})
        
        # Crop filter (case-insensitive check)
        if crop and props.get("predicted_crop", "").lower() != crop.lower():
            continue
            
        # Confidence filter
        if min_confidence is not None and float(props.get("confidence", 0.0)) < min_confidence:
            continue

        filtered_features.append(feat)
        if limit and len(filtered_features) >= limit:
            break

    return {
        "type": "FeatureCollection",
        "source": "GeoJSON_File",
        "name": raw_data.get("name", "classified_parcels"),
        "crs": raw_data.get("crs"),
        "total_features": len(filtered_features),
        "features": filtered_features
    }


@router.get("/{parcel_id}", response_model=Dict[str, Any])
def get_parcel_detail(
    parcel_id: str,
    db: Optional[Session] = Depends(get_db)
):
    """
    Returns specific parcel attributes, probabilities, and boundary geometry.
    """
    if is_db_connected() and db is not None:
        try:
            sql = """
                SELECT 
                    parcel_id,
                    predicted_crop,
                    confidence,
                    area_sq_km,
                    area_ha,
                    prob_paddy,
                    prob_banana,
                    prob_other,
                    ST_AsGeoJSON(geom) AS geom_json
                FROM agricultural_parcels
                WHERE parcel_id = :parcel_id
                LIMIT 1
            """
            row = db.execute(text(sql), {"parcel_id": parcel_id}).fetchone()
            if row:
                return {
                    "parcel_id": row.parcel_id,
                    "predicted_crop": row.predicted_crop,
                    "confidence": row.confidence,
                    "area_sq_km": row.area_sq_km,
                    "area_ha": row.area_ha,
                    "probabilities": {
                        "paddy": row.prob_paddy,
                        "banana": row.prob_banana,
                        "other": row.prob_other
                    },
                    "geometry": json.loads(row.geom_json)
                }
        except Exception as e:
            logger.warning(f"PostGIS detail query failed: {e}. Checking GeoJSON deliverable.")

    # Fallback check
    raw_data = get_cached_geojson()
    for feat in raw_data.get("features", []):
        props = feat.get("properties", {})
        if props.get("parcel_id") == parcel_id:
            return {
                "parcel_id": props.get("parcel_id"),
                "predicted_crop": props.get("predicted_crop"),
                "confidence": props.get("confidence"),
                "area_sq_km": props.get("area_sq_km"),
                "area_ha": props.get("area_ha"),
                "probabilities": {
                    "paddy": props.get("prob_paddy"),
                    "banana": props.get("prob_banana"),
                    "other": props.get("prob_other")
                },
                "geometry": feat.get("geometry")
            }

    raise HTTPException(status_code=404, detail=f"Parcel '{parcel_id}' not found.")
