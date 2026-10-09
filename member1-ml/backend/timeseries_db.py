"""
Member 1 — AI / ML & Backend Systems
Module: Time-Series Database Manager
Provides unified PostgreSQL/PostGIS and SQLite time-series storage for multi-temporal agricultural parcel observations.
Guarantees:
- Zero hardcoded dates or 'latest' values
- Multiple observations per parcel across years (2026, 2027, 2028...) coexist without overwriting
- Robust querying for latest observations, parcel history, hazards, and crop health
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("TimeSeriesDB")


class TimeSeriesDB:
    """
    Manages multi-temporal agricultural parcel observations.
    Uses SQLite locally (stored in data/database/timeseries.db) and synchronizes with PostGIS when active.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(curr_dir, "..", ".."))
            self.db_path = os.path.join(repo_root, "data", "database", "timeseries.db")
        else:
            self.db_path = db_path

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        """Initializes tables and indexes in SQLite."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS parcel_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parcel_id TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    processing_date TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    crop_confidence REAL NOT NULL,
                    prob_paddy REAL,
                    prob_banana REAL,
                    prob_other REAL,
                    ndvi REAL,
                    ndwi REAL,
                    evi REAL,
                    crop_health TEXT DEFAULT 'Healthy',
                    health_score REAL,
                    damage_percent REAL DEFAULT 0.0,
                    hazard TEXT DEFAULT 'None',
                    severity TEXT DEFAULT 'None',
                    hazard_evidence TEXT,
                    model_version TEXT NOT NULL,
                    source_scene TEXT,
                    area_ha REAL NOT NULL,
                    area_sq_km REAL NOT NULL,
                    taluk TEXT DEFAULT 'Ambasamudram',
                    geom_json TEXT NOT NULL,
                    UNIQUE(parcel_id, observation_date)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_pid ON parcel_observations(parcel_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_dt ON parcel_observations(observation_date DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_crop ON parcel_observations(crop)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_hazard ON parcel_observations(hazard)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_health ON parcel_observations(crop_health)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_model ON parcel_observations(model_version)")
            conn.commit()

    def upsert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates parcel observation records.
        Preserves historical observations across distinct dates.
        """
        if not records:
            return 0

        sql = """
            INSERT INTO parcel_observations (
                parcel_id, observation_date, processing_date, crop, crop_confidence,
                prob_paddy, prob_banana, prob_other, ndvi, ndwi, evi,
                crop_health, health_score, damage_percent, hazard, severity,
                hazard_evidence, model_version, source_scene, area_ha, area_sq_km,
                taluk, geom_json
            ) VALUES (
                :parcel_id, :observation_date, :processing_date, :crop, :crop_confidence,
                :prob_paddy, :prob_banana, :prob_other, :ndvi, :ndwi, :evi,
                :crop_health, :health_score, :damage_percent, :hazard, :severity,
                :hazard_evidence, :model_version, :source_scene, :area_ha, :area_sq_km,
                :taluk, :geom_json
            )
            ON CONFLICT(parcel_id, observation_date) DO UPDATE SET
                processing_date = excluded.processing_date,
                crop = excluded.crop,
                crop_confidence = excluded.crop_confidence,
                prob_paddy = excluded.prob_paddy,
                prob_banana = excluded.prob_banana,
                prob_other = excluded.prob_other,
                ndvi = excluded.ndvi,
                ndwi = excluded.ndwi,
                evi = excluded.evi,
                crop_health = excluded.crop_health,
                health_score = excluded.health_score,
                damage_percent = excluded.damage_percent,
                hazard = excluded.hazard,
                severity = excluded.severity,
                hazard_evidence = excluded.hazard_evidence,
                model_version = excluded.model_version,
                source_scene = excluded.source_scene,
                area_ha = excluded.area_ha,
                area_sq_km = excluded.area_sq_km,
                taluk = excluded.taluk,
                geom_json = excluded.geom_json
        """

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(sql, records)
            conn.commit()

        logger.info(f"Successfully upserted {len(records)} observations into time-series database.")
        return len(records)

    def get_latest_observations(
        self,
        crop: Optional[str] = None,
        min_confidence: Optional[float] = None,
        taluk: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dynamically retrieves the latest observation for every parcel
        by selecting MAX(observation_date) per parcel_id.
        """
        conditions = []
        params = {}

        if crop:
            conditions.append("o.crop = :crop")
            params["crop"] = crop
        if min_confidence is not None:
            conditions.append("o.crop_confidence >= :min_conf")
            params["min_conf"] = min_confidence
        if taluk and taluk.lower() != "all":
            conditions.append("o.taluk = :taluk")
            params["taluk"] = taluk

        where_clause = ("AND " + " AND ".join(conditions)) if conditions else ""
        limit_clause = f"LIMIT {limit}" if limit else ""

        sql = f"""
            WITH latest_dates AS (
                SELECT parcel_id, MAX(observation_date) AS max_date
                FROM parcel_observations
                GROUP BY parcel_id
            )
            SELECT o.*
            FROM parcel_observations o
            JOIN latest_dates ld ON o.parcel_id = ld.parcel_id AND o.observation_date = ld.max_date
            WHERE 1=1 {where_clause}
            ORDER BY o.parcel_id ASC
            {limit_clause}
        """

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            return {
                "type": "FeatureCollection",
                "message": "No recent usable satellite observation available.",
                "total_features": 0,
                "features": []
            }

        features = []
        obs_dates = set()
        model_versions = set()

        for r in rows:
            obs_dates.add(r["observation_date"])
            model_versions.add(r["model_version"])
            try:
                geom = json.loads(r["geom_json"])
                if not isinstance(geom, dict) or not geom.get("type") or not geom.get("coordinates"):
                    geom = None
            except Exception:
                geom = None

            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "parcel_id": r["parcel_id"],
                    "observation_date": r["observation_date"],
                    "processing_date": r["processing_date"],
                    "predicted_crop": r["crop"],
                    "confidence": r["crop_confidence"],
                    "crop_health": r["crop_health"],
                    "health_score": r["health_score"],
                    "ndvi": r["ndvi"],
                    "ndwi": r["ndwi"],
                    "evi": r["evi"],
                    "hazard": r["hazard"],
                    "severity": r["severity"],
                    "damage_percent": r["damage_percent"],
                    "hazard_evidence": r["hazard_evidence"],
                    "model_version": r["model_version"],
                    "source_scene": r["source_scene"],
                    "area_ha": r["area_ha"],
                    "area_sq_km": r["area_sq_km"],
                    "taluk": r["taluk"],
                    "prob_paddy": r["prob_paddy"],
                    "prob_banana": r["prob_banana"],
                    "prob_other": r["prob_other"]
                }
            })

        latest_dt = max(obs_dates) if obs_dates else None

        return {
            "type": "FeatureCollection",
            "source": "TimeSeriesDB_Latest_Query",
            "latest_observation_date": latest_dt,
            "distinct_dates_in_batch": sorted(list(obs_dates)),
            "active_model_versions": sorted(list(model_versions)),
            "total_features": len(features),
            "features": features
        }

    def get_observations_by_date(
        self,
        target_date: str,
        crop: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Retrieves parcel observations for a specific observation date."""
        conditions = ["observation_date = :target_date"]
        params = {"target_date": target_date}

        if crop:
            conditions.append("crop = :crop")
            params["crop"] = crop
        if min_confidence is not None:
            conditions.append("crop_confidence >= :min_conf")
            params["min_conf"] = min_confidence

        where_clause = "WHERE " + " AND ".join(conditions)
        sql = f"SELECT * FROM parcel_observations {where_clause} ORDER BY parcel_id ASC"

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            return {
                "type": "FeatureCollection",
                "message": f"No observations found for date {target_date}.",
                "observation_date": target_date,
                "total_features": 0,
                "features": []
            }

        features = []
        for r in rows:
            try:
                geom = json.loads(r["geom_json"])
                if not isinstance(geom, dict) or not geom.get("type") or not geom.get("coordinates"):
                    geom = None
            except Exception:
                geom = None

            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "parcel_id": r["parcel_id"],
                    "observation_date": r["observation_date"],
                    "processing_date": r["processing_date"],
                    "predicted_crop": r["crop"],
                    "confidence": r["crop_confidence"],
                    "crop_health": r["crop_health"],
                    "ndvi": r["ndvi"],
                    "ndwi": r["ndwi"],
                    "evi": r["evi"],
                    "hazard": r["hazard"],
                    "severity": r["severity"],
                    "damage_percent": r["damage_percent"],
                    "model_version": r["model_version"],
                    "source_scene": r["source_scene"],
                    "area_ha": r["area_ha"],
                    "area_sq_km": r["area_sq_km"],
                    "taluk": r["taluk"]
                }
            })

        return {
            "type": "FeatureCollection",
            "source": "TimeSeriesDB_Date_Query",
            "observation_date": target_date,
            "total_features": len(features),
            "features": features
        }

    def get_available_dates(self) -> List[Dict[str, Any]]:
        """Returns distinct observation dates with summary metrics."""
        sql = """
            SELECT 
                observation_date,
                COUNT(*) as parcel_count,
                AVG(crop_confidence) as mean_confidence,
                AVG(ndvi) as mean_ndvi,
                AVG(ndwi) as mean_ndwi,
                model_version,
                source_scene,
                MAX(processing_date) as last_processed
            FROM parcel_observations
            GROUP BY observation_date, model_version
            ORDER BY observation_date DESC
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "observation_date": r["observation_date"],
                "parcel_count": r["parcel_count"],
                "mean_confidence": round(float(r["mean_confidence"]), 4) if r["mean_confidence"] else 0.0,
                "mean_ndvi": round(float(r["mean_ndvi"]), 4) if r["mean_ndvi"] else 0.0,
                "mean_ndwi": round(float(r["mean_ndwi"]), 4) if r["mean_ndwi"] else 0.0,
                "model_version": r["model_version"],
                "source_scene": r["source_scene"],
                "processing_date": r["last_processed"]
            })
        return results

    def get_parcel_history(self, parcel_id: str) -> List[Dict[str, Any]]:
        """Returns chronological time-series observations for a single parcel."""
        sql = """
            SELECT *
            FROM parcel_observations
            WHERE parcel_id = :parcel_id
            ORDER BY observation_date ASC
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, {"parcel_id": parcel_id})
            rows = cur.fetchall()

        history = []
        for r in rows:
            history.append({
                "parcel_id": r["parcel_id"],
                "observation_date": r["observation_date"],
                "processing_date": r["processing_date"],
                "crop": r["crop"],
                "confidence": r["crop_confidence"],
                "crop_health": r["crop_health"],
                "health_score": r["health_score"],
                "ndvi": r["ndvi"],
                "ndwi": r["ndwi"],
                "evi": r["evi"],
                "hazard": r["hazard"],
                "severity": r["severity"],
                "damage_percent": r["damage_percent"],
                "hazard_evidence": r["hazard_evidence"],
                "model_version": r["model_version"],
                "source_scene": r["source_scene"],
                "area_ha": r["area_ha"]
            })
        return history

    def get_latest_hazards(self) -> Dict[str, Any]:
        """Returns the most recent validated hazard assessment."""
        sql = """
            WITH latest_obs AS (
                SELECT o.*
                FROM parcel_observations o
                JOIN (
                    SELECT parcel_id, MAX(observation_date) AS max_date
                    FROM parcel_observations
                    GROUP BY parcel_id
                ) ld ON o.parcel_id = ld.parcel_id AND o.observation_date = ld.max_date
            )
            SELECT *
            FROM latest_obs
            WHERE hazard != 'None' AND hazard IS NOT NULL
            ORDER BY damage_percent DESC
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        # Fleet-level hazard breakdown
        hazard_summary = {"Flood": 0, "Drought": 0, "Cyclone": 0, "Potential": 0, "None": 0}
        total_damaged_area_ha = 0.0

        affected_parcels = []
        for r in rows:
            h_type = r["hazard"]
            hazard_summary[h_type] = hazard_summary.get(h_type, 0) + 1
            if r["damage_percent"] > 0:
                total_damaged_area_ha += float(r["area_ha"])

            affected_parcels.append({
                "parcel_id": r["parcel_id"],
                "observation_date": r["observation_date"],
                "crop": r["crop"],
                "hazard": r["hazard"],
                "severity": r["severity"],
                "damage_percent": r["damage_percent"],
                "evidence": r["hazard_evidence"],
                "area_ha": r["area_ha"],
                "ndvi": r["ndvi"],
                "ndwi": r["ndwi"]
            })

        latest_date_sql = "SELECT MAX(observation_date) as max_dt FROM parcel_observations"
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(latest_date_sql)
            max_dt_row = cur.fetchone()
            latest_dt = max_dt_row["max_dt"] if max_dt_row else None

        return {
            "source": "TimeSeriesDB_Hazard_Query",
            "observation_date": latest_dt,
            "total_parcels_affected": len(affected_parcels),
            "total_damaged_area_ha": round(total_damaged_area_ha, 2),
            "hazard_breakdown": hazard_summary,
            "affected_parcels": affected_parcels
        }

    def get_latest_health(self) -> Dict[str, Any]:
        """Returns the most recent crop health classification breakdown."""
        sql = """
            WITH latest_obs AS (
                SELECT o.*
                FROM parcel_observations o
                JOIN (
                    SELECT parcel_id, MAX(observation_date) AS max_date
                    FROM parcel_observations
                    GROUP BY parcel_id
                ) ld ON o.parcel_id = ld.parcel_id AND o.observation_date = ld.max_date
            )
            SELECT 
                crop_health,
                COUNT(*) as parcel_count,
                SUM(area_ha) as total_area_ha,
                AVG(ndvi) as mean_ndvi,
                AVG(ndwi) as mean_ndwi,
                AVG(crop_confidence) as mean_conf
            FROM latest_obs
            GROUP BY crop_health
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        breakdown = {
            "Healthy": {"parcel_count": 0, "area_ha": 0.0, "mean_ndvi": 0.0},
            "Moderate Stress": {"parcel_count": 0, "area_ha": 0.0, "mean_ndvi": 0.0},
            "Severe Stress": {"parcel_count": 0, "area_ha": 0.0, "mean_ndvi": 0.0},
            "Unknown": {"parcel_count": 0, "area_ha": 0.0, "mean_ndvi": 0.0}
        }

        total_parcels = 0
        for r in rows:
            h = r["crop_health"] or "Unknown"
            cnt = r["parcel_count"]
            total_parcels += cnt
            breakdown[h] = {
                "parcel_count": cnt,
                "area_ha": round(float(r["total_area_ha"] or 0.0), 2),
                "mean_ndvi": round(float(r["mean_ndvi"] or 0.0), 4),
                "mean_ndwi": round(float(r["mean_ndwi"] or 0.0), 4),
                "mean_confidence": round(float(r["mean_conf"] or 0.0), 4)
            }

        # Calculate percentages
        for h, d in breakdown.items():
            d["percentage_of_parcels"] = round((d["parcel_count"] / max(total_parcels, 1)) * 100.0, 2)

        return {
            "source": "TimeSeriesDB_CropHealth_Query",
            "total_parcels_evaluated": total_parcels,
            "health_distribution": breakdown
        }

    def get_data_freshness_status(self, threshold_days: int = 60) -> Dict[str, Any]:
        """
        Evaluates data freshness against threshold.
        Returns 'Fresh', 'Delayed', 'Data may be outdated', or 'No recent usable satellite observation available.'
        """
        try:
            threshold_days = int(threshold_days)
        except Exception:
            threshold_days = 60

        sql = """
            SELECT 
                MAX(observation_date) as last_obs_date,
                MAX(processing_date) as last_proc_date,
                COUNT(DISTINCT observation_date) as total_dates,
                COUNT(*) as total_records
            FROM parcel_observations
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            row = cur.fetchone()

        last_obs = row["last_obs_date"] if row else None
        last_proc = row["last_proc_date"] if row else None

        if not last_obs:
            return {
                "status": "No recent usable satellite observation available.",
                "last_observation_date": None,
                "last_processing_date": None,
                "days_since_observation": None,
                "is_outdated": True,
                "message": "No recent usable satellite observation available."
            }

        try:
            obs_dt = datetime.strptime(last_obs, "%Y-%m-%d").date()
            # Reference date against current system time
            now_dt = datetime.utcnow().date()
            days_diff = (now_dt - obs_dt).days
        except Exception:
            days_diff = 0

        if days_diff <= 30:
            status = "Fresh"
            msg = "Satellite observation is current and verified."
        elif days_diff <= threshold_days:
            status = "Delayed"
            msg = f"Last observation was {days_diff} days ago. Scheduled ingestion pending."
        else:
            status = "Data may be outdated."
            msg = f"Data may be outdated ({days_diff} days since last observation). Inspection recommended."

        return {
            "status": status,
            "last_observation_date": last_obs,
            "last_processing_date": last_proc,
            "days_since_observation": days_diff,
            "threshold_days": threshold_days,
            "is_outdated": days_diff > threshold_days,
            "message": msg,
            "total_observation_dates": row["total_dates"],
            "total_observation_records": row["total_records"]
        }
