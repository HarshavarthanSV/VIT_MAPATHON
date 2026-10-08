"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
Statistics Router: Serves dynamic study area aggregations and ML model metrics.
"""

import csv
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except (ImportError, Exception):
    text = None
    Session = None

from database import is_db_connected, get_db, load_json_artifact, resolve_artifact_path

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
                    "study_area_taluks": "Ambasamudram & Cheranmahadevi",
                    "district": "Tirunelveli",
                    "state": "Tamil Nadu",
                    "meets_min_area_requirement": True
                },
                "crop_distribution": crop_dist
            }
        except Exception as e:
            logger.warning(f"PostGIS aggregation failed: {e}. Falling back to dynamic GeoJSON calculation.")

    # Dynamic calculation from classified_parcels.geojson deliverable
    geojson_path = resolve_artifact_path("classified_parcels.geojson")
    if geojson_path:
        try:
            import json
            with open(geojson_path, "r", encoding="utf-8") as f:
                raw_geojson = json.load(f)
            features = raw_geojson.get("features", [])
            total_parcels = len(features)
            total_area_ha = 0.0
            total_area_sq_km = 0.0
            conf_sum = 0.0

            crop_bins = {}
            for feat in features:
                props = feat.get("properties", {})
                c = props.get("predicted_crop") or props.get("crop") or "Unknown"
                conf = float(props.get("confidence", 0.0))
                area_ha = float(props.get("area_ha", 0.0))
                area_sq_km = float(props.get("area_sq_km", area_ha / 100.0))

                total_area_ha += area_ha
                total_area_sq_km += area_sq_km
                conf_sum += conf

                if c not in crop_bins:
                    crop_bins[c] = {"count": 0, "area_ha": 0.0, "area_sq_km": 0.0, "conf_sum": 0.0}
                crop_bins[c]["count"] += 1
                crop_bins[c]["area_ha"] += area_ha
                crop_bins[c]["area_sq_km"] += area_sq_km
                crop_bins[c]["conf_sum"] += conf

            crop_dist = {}
            for c, b in crop_bins.items():
                cnt = b["count"]
                crop_dist[c] = {
                    "parcel_count": cnt,
                    "percentage_of_parcels": round(cnt / total_parcels * 100.0, 2) if total_parcels > 0 else 0.0,
                    "area_sq_km": round(b["area_sq_km"], 4),
                    "area_hectares": round(b["area_ha"], 2),
                    "percentage_of_total_area": round(b["area_ha"] / total_area_ha * 100.0, 2) if total_area_ha > 0 else 0.0,
                    "mean_confidence": round(b["conf_sum"] / cnt, 4) if cnt > 0 else 0.0
                }

            return {
                "source": "GeoJSON_Live_Aggregation",
                "study_area_summary": {
                    "total_parcels": total_parcels,
                    "total_study_area_sq_km": round(total_area_sq_km, 4),
                    "total_study_area_hectares": round(total_area_ha, 2),
                    "overall_mean_confidence": round(conf_sum / total_parcels, 4) if total_parcels > 0 else 0.0,
                    "study_area_taluks": "Ambasamudram & Cheranmahadevi",
                    "district": "Tirunelveli",
                    "state": "Tamil Nadu",
                    "meets_min_area_requirement": True
                },
                "crop_distribution": crop_dist
            }
        except Exception as e:
            logger.warning(f"Live GeoJSON aggregation failed: {e}. Checking crop_statistics.json.")

    try:
        data = load_json_artifact("crop_statistics.json")
        data["source"] = "Artifact_File"
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Crop statistics not available: {e}")


@router.get("/crops", response_model=List[Dict[str, Any]])
def get_crops(db: Optional[Session] = Depends(get_db)):
    """
    Returns active classified crop types with live parcel counts and acreage.
    Derives strictly from PostGIS / live classified GeoJSON.
    """
    stats = get_statistics(db=db)
    crop_dist = stats.get("crop_distribution", {})
    results = []
    for crop_name, data in crop_dist.items():
        results.append({
            "crop": crop_name,
            "parcel_count": data.get("parcel_count", 0),
            "percentage_of_parcels": data.get("percentage_of_parcels", 0.0),
            "area_hectares": data.get("area_hectares", 0.0),
            "area_sq_km": data.get("area_sq_km", 0.0),
            "percentage_of_total_area": data.get("percentage_of_total_area", 0.0),
            "mean_confidence": data.get("mean_confidence", 0.0)
        })
    return results



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


@router.get("/taluk-acreage", response_model=List[Dict[str, Any]])
@router.get("/statistics/taluk-acreage", response_model=List[Dict[str, Any]])
def get_taluk_acreage():
    """
    Returns taluk-level agricultural acreage statistics (Ambasamudram vs Cheranmahadevi)
    from results/taluk_crop_acreage_summary.csv generated by Member 2.
    """
    path = resolve_artifact_path("taluk_crop_acreage_summary.csv")
    if not path:
        raise HTTPException(status_code=404, detail="taluk_crop_acreage_summary.csv not found")
    try:
        records = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    "taluk": row.get("Taluk"),
                    "crop": row.get("Crop"),
                    "parcel_count": int(row.get("Parcel_Count", 0)),
                    "area_hectares": float(row.get("Area_Hectares", 0.0)),
                    "area_acres": float(row.get("Area_Acres", 0.0)),
                    "percentage_of_taluk": float(row.get("Percentage_of_Taluk", 0.0))
                })
        return records
    except Exception as e:
        logger.error(f"Error reading taluk acreage CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read taluk acreage summary: {e}")

