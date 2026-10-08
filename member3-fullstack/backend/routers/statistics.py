"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
Statistics Router: Serves dynamic study area aggregations and ML model metrics.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import is_db_connected, get_db, load_json_artifact

logger = logging.getLogger("StatisticsRouter")
router = APIRouter(prefix="/api", tags=["statistics"])


@router.get("/statistics", response_model=Dict[str, Any])
def get_statistics(db: Optional[Session] = Depends(get_db)):
    """
    Returns aggregated study area summary and per-crop distribution (counts, area in sq. km, ha, %).
    Calculates dynamically from PostGIS if connected; otherwise serves crop_statistics.json deliverable.
    """
    if is_db_connected() and db is not None:
        try:
            # Dynamic PostGIS aggregation
            summary_sql = """
                SELECT 
                    COUNT(*) as total_parcels,
                    COALESCE(SUM(area_sq_km), 0.0) as total_area_sq_km,
                    COALESCE(SUM(area_ha), 0.0) as total_area_ha,
                    COALESCE(AVG(confidence), 0.0) as overall_mean_conf
                FROM agricultural_parcels;
            """
            s_row = db.execute(text(summary_sql)).fetchone()
            total_parcels = s_row.total_parcels
            total_area_sq_km = float(s_row.total_area_sq_km)
            total_area_ha = float(s_row.total_area_ha)
            overall_conf = float(s_row.overall_mean_conf)

            dist_sql = """
                SELECT 
                    predicted_crop,
                    COUNT(*) as p_count,
                    COALESCE(SUM(area_sq_km), 0.0) as c_area_sq_km,
                    COALESCE(SUM(area_ha), 0.0) as c_area_ha,
                    COALESCE(AVG(confidence), 0.0) as c_mean_conf
                FROM agricultural_parcels
                GROUP BY predicted_crop;
            """
            d_rows = db.execute(text(dist_sql)).fetchall()

            crop_dist = {}
            for r in d_rows:
                pct_parcels = round((r.p_count / total_parcels * 100.0), 2) if total_parcels > 0 else 0.0
                pct_area = round((float(r.c_area_sq_km) / total_area_sq_km * 100.0), 2) if total_area_sq_km > 0 else 0.0
                crop_dist[r.predicted_crop] = {
                    "parcel_count": r.p_count,
                    "percentage_of_parcels": pct_parcels,
                    "area_sq_km": round(float(r.c_area_sq_km), 4),
                    "area_hectares": round(float(r.c_area_ha), 2),
                    "percentage_of_total_area": pct_area,
                    "mean_confidence": round(float(r.c_mean_conf), 4)
                }

            return {
                "source": "PostGIS_Live_Query",
                "study_area_summary": {
                    "total_parcels": total_parcels,
                    "total_study_area_sq_km": round(total_area_sq_km, 4),
                    "total_study_area_hectares": round(total_area_ha, 2),
                    "overall_mean_confidence": round(overall_conf, 4),
                    "meets_min_area_requirement": total_area_sq_km >= 20.0
                },
                "crop_distribution": crop_dist
            }
        except Exception as e:
            logger.warning(f"PostGIS aggregation failed: {e}. Falling back to crop_statistics.json.")

    try:
        data = load_json_artifact("crop_statistics.json")
        data["source"] = "Artifact_File"
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Crop statistics not available: {e}")


@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics():
    """
    Returns machine learning evaluation metrics (Accuracy, Precision, Recall, F1, per-class metrics)
    from model_metrics.json deliverable.
    """
    try:
        return load_json_artifact("model_metrics.json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model metrics not available: {e}")


@router.get("/feature-importance", response_model=Dict[str, Any])
def get_feature_importance():
    """
    Returns ranked feature importance scores from feature_importance.json deliverable.
    """
    try:
        return load_json_artifact("feature_importance.json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Feature importance not available: {e}")
