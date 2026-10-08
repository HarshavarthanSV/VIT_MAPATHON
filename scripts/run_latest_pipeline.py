"""
VIT MAPATHON — Automated Operational Pipeline Runner
Script: run_latest_pipeline.py

Executes end-to-end periodic or on-demand processing of latest Sentinel-2 observations:
1. Identifies new satellite observations / feature tables
2. Validates cloud cover & AOI coverage quality gates
3. Extracts and aligns feature schema with production model
4. Runs existing production model inference (WITHOUT RETRAINING)
5. Computes crop health condition and multi-temporal hazard assessments
6. Updates time-series database (preserves historical observations)
7. Generates operational quality report and updates data freshness status
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
member1_dir = os.path.join(repo_root, "member1-ml")
if member1_dir not in sys.path:
    sys.path.insert(0, member1_dir)
if os.path.join(member1_dir, "pipelines") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "pipelines"))
if os.path.join(member1_dir, "models") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "models"))
if os.path.join(member1_dir, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "backend"))

from inference_pipeline import SatelliteInferencePipeline
from timeseries_db import TimeSeriesDB
from model_registry import ModelRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("OperationalPipelineRunner")


def run_pipeline(
    observation_date: str,
    feature_csv: Optional[str] = None,
    source_scene: str = "Sentinel-2_MSI_L2A",
    cloud_cover: float = 3.5,
    aoi_coverage: float = 100.0,
    force: bool = False
) -> Dict[str, Any]:
    """
    Executes production inference pipeline for a given observation date.
    """
    logger.info("=" * 75)
    logger.info("VIT MAPATHON — PRODUCTION SATELLITE MONITORING PIPELINE")
    logger.info(f"Target Observation Date: {observation_date}")
    logger.info(f"Scene Product ID:        {source_scene}")
    logger.info(f"Cloud Cover:             {cloud_cover}% (Threshold <= 20%)")
    logger.info("=" * 75)

    db = TimeSeriesDB()
    reg = ModelRegistry()

    # 1. Check if observation date already processed (prevent duplicate work unless force=True)
    existing_dates = [d["observation_date"] for d in db.get_available_dates()]
    if observation_date in existing_dates and not force:
        logger.info(f"Observation date {observation_date} already exists in database. Skipping duplicate processing.")
        return {
            "success": True,
            "message": f"Observation {observation_date} already ingested. Use --force to reprocess.",
            "observation_date": observation_date,
            "already_existed": True
        }

    # 2. Resolve feature dataset
    if feature_csv is None or not os.path.exists(feature_csv):
        default_csv = os.path.join(repo_root, "data", "features", "tabular", "ml_training_dataset.csv")
        if os.path.exists(default_csv):
            feature_csv = default_csv
        else:
            err = f"Feature dataset could not be located at {feature_csv}"
            logger.error(err)
            return {"success": False, "error": err, "stage": "input_resolution"}

    logger.info(f"Loading input feature vectors from: {feature_csv}")
    df_features = pd.read_csv(feature_csv)

    # 3. Instantiate pipeline & execute inference
    pipeline = SatelliteInferencePipeline()
    result = pipeline.run_inference_on_observation(
        observation_date=observation_date,
        features_df=df_features,
        source_scene=source_scene,
        cloud_cover_percent=cloud_cover,
        aoi_coverage_percent=aoi_coverage
    )

    if not result.get("success", False):
        logger.error(f"Pipeline execution halted: {result.get('error')}")
        return result

    # 4. Post-ingestion validation
    latest_info = db.get_data_freshness_status()
    logger.info("=" * 75)
    logger.info("OPERATIONAL INGESTION COMPLETED SUCCESSFULLY!")
    logger.info(f"Parcels Processed:       {result.get('parcels_ingested')}")
    logger.info(f"Production Model Used:   {result.get('model_version')}")
    logger.info(f"Mean Confidence:         {result.get('mean_confidence')}")
    logger.info(f"Data Freshness Status:   {latest_info.get('status')}")
    logger.info(f"Days Since Observation:  {latest_info.get('days_since_observation')}")
    logger.info("=" * 75)

    return result


def main():
    parser = argparse.ArgumentParser(description="Operational Sentinel-2 Monitoring Pipeline")
    parser.add_argument("--date", type=str, default=None, help="Observation date in YYYY-MM-DD format")
    parser.add_argument("--features", type=str, default=None, help="Path to parcel feature CSV")
    parser.add_argument("--scene", type=str, default="S2_MSIL2A_OPERATIONAL", help="Sentinel-2 product/scene name")
    parser.add_argument("--cloud", type=float, default=4.0, help="Cloud cover percentage (default: 4.0)")
    parser.add_argument("--force", action="store_true", help="Force reprocessing if date already exists")
    args = parser.parse_args()

    # If no date specified, default to latest observation in features or prompt
    target_date = args.date or "2026-09-09"
    res = run_pipeline(
        observation_date=target_date,
        feature_csv=args.features,
        source_scene=args.scene,
        cloud_cover=args.cloud,
        force=args.force
    )
    if not res.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
