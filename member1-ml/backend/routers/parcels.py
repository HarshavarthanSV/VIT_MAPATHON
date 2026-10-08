"""
VIT MAPATHON — Member 1 (AI / ML & Backend Systems)
Parcels Router: Serves GeoJSON parcel vector layers with dynamic filtering.
"""

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

from database import is_db_connected, get_db, load_json_artifact, resolve_artifact_path
from timeseries_db import TimeSeriesDB

logger = logging.getLogger("ParcelsRouter")
router = APIRouter(prefix="/api/parcels", tags=["parcels"])

_ts_db = TimeSeriesDB()

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

    # Check TimeSeriesDB for live multi-temporal observations
    ts_res = _ts_db.get_latest_observations(crop=crop, min_confidence=min_confidence, limit=limit)
    if ts_res.get("total_features", 0) > 0:
        return ts_res

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

    # Check TimeSeriesDB for live observations & multi-temporal history
    history = _ts_db.get_parcel_history(parcel_id)
    if history:
        latest = history[-1]
        raw_data = get_cached_geojson()
        geom = None
        for f in raw_data.get("features", []):
            if f.get("properties", {}).get("parcel_id") == parcel_id:
                geom = f.get("geometry")
                break
        return {
            "parcel_id": latest["parcel_id"],
            "observation_date": latest["observation_date"],
            "predicted_crop": latest["crop"],
            "confidence": latest["confidence"],
            "crop_health": latest.get("crop_health", "Healthy"),
            "health_score": latest.get("health_score", 0.8),
            "ndvi": latest.get("ndvi"),
            "ndwi": latest.get("ndwi"),
            "hazard": latest.get("hazard", "None"),
            "damage_percent": latest.get("damage_percent", 0.0),
            "model_version": latest.get("model_version", "v1.0"),
            "area_ha": latest.get("area_ha", 0.5),
            "probabilities": {
                "paddy": latest.get("prob_paddy") or 0.0,
                "banana": latest.get("prob_banana") or 0.0,
                "other": latest.get("prob_other") or 0.0
            },
            "history_count": len(history),
            "temporal_history": history,
            "geometry": geom
        }

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
