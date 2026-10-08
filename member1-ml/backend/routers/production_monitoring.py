"""
VIT MAPATHON — Member 1 (AI / ML & Backend Systems)
Production Monitoring Router
Provides REST APIs for:
- Latest and historical crop observations across time
- Parcel multi-temporal trajectory
- Calibrated crop health indicators
- Hazard detection and impact monitoring
- Model version registry and active production model metadata
- Operational data freshness tracking
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends

# Ensure backend and models directories in path
router_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(router_dir)
member1_dir = os.path.dirname(backend_dir)
repo_root = os.path.dirname(member1_dir)
if os.path.join(member1_dir, "models") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "models"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from timeseries_db import TimeSeriesDB
from model_registry import ModelRegistry

logger = logging.getLogger("ProductionMonitoringRouter")
router = APIRouter(prefix="/api", tags=["production_monitoring"])

_ts_db = TimeSeriesDB()
_registry = ModelRegistry()


@router.get("/crops/latest", response_model=Dict[str, Any])
def get_latest_crops(
    crop: Optional[str] = Query(None, description="Filter by crop: Paddy, Banana, Other"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    taluk: Optional[str] = Query(None, description="Filter by taluk: Ambasamudram, Cheranmahadevi, all"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum parcel count")
):
    """
    Returns latest parcel observations by dynamically selecting MAX(observation_date)
    for each parcel from the time-series database.
    Zero hardcoded dates. If no data exists, returns 'No recent usable satellite observation available.'
    """
    res = _ts_db.get_latest_observations(crop=crop, min_confidence=min_confidence, taluk=taluk, limit=limit)
    if res.get("total_features", 0) == 0:
        return {
            "type": "FeatureCollection",
            "message": "No recent usable satellite observation available.",
            "total_features": 0,
            "features": []
        }
    return res


@router.get("/crops/history", response_model=List[Dict[str, Any]])
def get_crops_history():
    """
    Returns chronological timeline of all available satellite observation dates,
    parcel counts, mean NDVI, mean NDWI, and model versions.
    """
    return _ts_db.get_available_dates()


@router.get("/crops/date/{obs_date}", response_model=Dict[str, Any])
def get_crops_by_date(
    obs_date: str,
    crop: Optional[str] = Query(None, description="Filter by crop: Paddy, Banana, Other"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold")
):
    """
    Returns parcel observations for a specific historical observation date.
    Allows time-series comparison across 2026, 2027, 2028...
    """
    return _ts_db.get_observations_by_date(target_date=obs_date, crop=crop, min_confidence=min_confidence)


@router.get("/crops/{parcel_id}/history", response_model=List[Dict[str, Any]])
def get_parcel_temporal_history(parcel_id: str):
    """
    Returns full multi-temporal observation trajectory for a specific agricultural parcel,
    including NDVI changes, crop classifications, and health scores across time.
    """
    history = _ts_db.get_parcel_history(parcel_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"No observation history found for parcel '{parcel_id}'.")
    return history


@router.get("/hazards/latest", response_model=Dict[str, Any])
def get_latest_hazards():
    """
    Returns the most recent validated hazard assessment (Flood, Drought, Cyclone, Potential, None).
    Derived from multi-temporal spectral delta indicators against baseline conditions.
    """
    return _ts_db.get_latest_hazards()


@router.get("/hazards/history", response_model=Dict[str, Any])
def get_hazards_history():
    """
    Returns historical hazard event log across all observation dates.
    """
    dates = _ts_db.get_available_dates()
    return {
        "source": "TimeSeriesDB_Hazard_History",
        "total_monitoring_dates": len(dates),
        "monitoring_dates": dates,
        "latest_summary": _ts_db.get_latest_hazards()
    }


@router.get("/health/latest", response_model=Dict[str, Any])
def get_latest_crop_health():
    """
    Returns current crop health condition breakdown (Healthy, Moderate Stress, Severe Stress, Unknown).
    Computed using crop-specific NDVI and NDWI thresholds.
    """
    return _ts_db.get_latest_health()


@router.get("/models/production", response_model=Dict[str, Any])
def get_production_model_info():
    """
    Returns active production model metadata, version, features used, and validation metrics.
    """
    try:
        return _registry.get_production_model_meta()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Production model metadata unavailable: {e}")


@router.get("/models/registry", response_model=Dict[str, Any])
def get_model_registry_entries():
    """
    Returns full model registry including production, candidate, and retired models.
    """
    return _registry.load_registry()


@router.get("/data-status", response_model=Dict[str, Any])
def get_data_status(threshold_days: int = Query(60, ge=1, description="Days threshold before marking outdated")):
    """
    Returns data freshness status:
    - 'Fresh': Observation <= 30 days old
    - 'Delayed': Observation 31-60 days old
    - 'Data may be outdated': Observation > threshold_days old
    - 'No recent usable satellite observation available.': No records exist
    """
    return _ts_db.get_data_freshness_status(threshold_days=threshold_days)
