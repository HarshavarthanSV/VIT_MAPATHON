"""
VIT MAPATHON — Production Agricultural Monitoring System
Unit & Integration Test Suite: Phase 2 Production Monitoring, Latest Satellite Data,
Model Versioning, and Periodic Retraining.
Tests all 15 operational requirements from Phase 2 specification.
"""

import os
import sys
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Path setup
tests_dir = os.path.dirname(os.path.abspath(__file__))
member1_dir = os.path.dirname(tests_dir)
repo_root = os.path.abspath(os.path.join(member1_dir, ".."))

if member1_dir not in sys.path:
    sys.path.insert(0, member1_dir)
if os.path.join(member1_dir, "pipelines") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "pipelines"))
if os.path.join(member1_dir, "models") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "models"))
if os.path.join(member1_dir, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "backend"))

from model_registry import ModelRegistry
from timeseries_db import TimeSeriesDB
from inference_pipeline import SatelliteInferencePipeline
from training_pipeline import ModelTrainingPipeline
from agronomic_indicators import calculate_crop_health, assess_hazard_impact
from main import app

client = TestClient(app)


def test_01_training_inference_separation():
    """Confirms training pipeline and inference pipeline are strictly decoupled."""
    trainer = ModelTrainingPipeline()
    inferencer = SatelliteInferencePipeline()
    assert hasattr(trainer, "train_model_version")
    assert hasattr(inferencer, "run_inference_on_observation")
    # Inference does not expose train method
    assert not hasattr(inferencer, "train_model_version")


def test_02_model_registry_and_versioning():
    """Confirms model registry tracks active production model v1.0 with complete metadata."""
    reg = ModelRegistry()
    prod_meta = reg.get_production_model_meta()

    assert prod_meta["model_version"] == "v1.0"
    assert prod_meta["status"] == "production"
    assert "artifact_path" in prod_meta
    assert "training_start_date" in prod_meta
    assert "training_end_date" in prod_meta
    assert "training_dataset_version" in prod_meta
    assert "features_used" in prod_meta
    assert len(prod_meta["features_used"]) == 240
    assert "validation_metrics" in prod_meta
    assert prod_meta["validation_metrics"]["overall"]["accuracy"] > 0.70


def test_03_ingest_new_observation_date_and_coexistence():
    """
    Ingests observation for 2026-03-20, then new observation 2026-09-09.
    Confirms old data remains, and 2026-09-09 becomes latest.
    """
    db = TimeSeriesDB()
    pipeline = SatelliteInferencePipeline()
    df = pd.read_csv(os.path.join(repo_root, "data", "features", "tabular", "ml_training_dataset.csv"))

    # Ingest date 1
    res1 = pipeline.run_inference_on_observation(
        observation_date="2026-03-20",
        features_df=df,
        source_scene="S2A_20260320",
        cloud_cover_percent=2.5
    )
    assert res1["success"] is True

    # Ingest date 2
    res2 = pipeline.run_inference_on_observation(
        observation_date="2026-09-09",
        features_df=df,
        source_scene="S2B_20260909",
        cloud_cover_percent=4.1
    )
    assert res2["success"] is True

    # Confirm both dates coexist
    dates = db.get_available_dates()
    date_strings = [d["observation_date"] for d in dates]
    assert "2026-03-20" in date_strings
    assert "2026-09-09" in date_strings

    # Confirm latest observation is 2026-09-09
    latest = db.get_latest_observations()
    assert latest["latest_observation_date"] == "2026-09-09"
    assert latest["total_features"] == 293


def test_04_parcel_time_series_history():
    """Confirms individual parcels maintain chronological observation records."""
    db = TimeSeriesDB()
    history = db.get_parcel_history("PARCEL_0001")
    assert len(history) >= 2
    dates = [h["observation_date"] for h in history]
    assert dates == sorted(dates)  # Chronologically ordered
    assert "2026-03-20" in dates
    assert "2026-09-09" in dates


def test_05_model_version_stored_with_observation():
    """Confirms every observation record explicitly stores the model_version."""
    db = TimeSeriesDB()
    latest = db.get_latest_observations(limit=10)
    for feat in latest["features"]:
        props = feat["properties"]
        assert props["model_version"] == "v1.0"
        assert "observation_date" in props
        assert "processing_date" in props
        assert "source_scene" in props


def test_06_simulate_failed_processing_high_cloud():
    """
    Simulates observation with 35% cloud cover (exceeding 20% limit).
    Confirms rejection, error logging, and that no fake observation is stored.
    """
    db = TimeSeriesDB()
    pipeline = SatelliteInferencePipeline()
    df = pd.read_csv(os.path.join(repo_root, "data", "features", "tabular", "ml_training_dataset.csv"))

    dates_before = [d["observation_date"] for d in db.get_available_dates()]

    # Attempt ingestion with cloud cover = 35%
    result = pipeline.run_inference_on_observation(
        observation_date="2027-05-20",
        features_df=df,
        cloud_cover_percent=35.0
    )

    assert result["success"] is False
    assert result["stage"] == "cloud_quality_gate"
    assert result["status"] == "REJECTED_HIGH_CLOUD_COVER"

    # Confirm date 2027-05-20 was NOT inserted into database
    dates_after = [d["observation_date"] for d in db.get_available_dates()]
    assert "2027-05-20" not in dates_after
    assert dates_before == dates_after


def test_07_feature_schema_validation():
    """
    Simulates feature mismatch (missing expected columns).
    Confirms pipeline halts with FAILED_SCHEMA_MISMATCH and does not guess.
    """
    pipeline = SatelliteInferencePipeline()
    bad_df = pd.DataFrame({"parcel_id": ["P1", "P2"], "dummy_col": [1.0, 2.0]})

    result = pipeline.run_inference_on_observation(
        observation_date="2027-06-01",
        features_df=bad_df
    )
    assert result["success"] is False
    assert result["stage"] == "feature_schema_validation"
    assert result["status"] == "FAILED_SCHEMA_MISMATCH"


def test_08_candidate_vs_production_model_comparison():
    """
    Tests comparing candidate model v2.0 against production model v1.0.
    Confirms evaluation recommendations based on accuracy and Macro-F1.
    """
    reg = ModelRegistry()
    comp = reg.compare_models(candidate_version="v2.0", production_version="v1.0")

    assert comp["candidate_version"] == "v2.0"
    assert comp["production_version"] == "v1.0"
    assert "metrics_comparison" in comp
    assert "recommendation" in comp
    assert comp["recommendation"] in ["PROMOTE_TO_PRODUCTION", "REJECT_OR_REFINE"]

    # Production remains v1.0
    prod = reg.get_production_model_meta()
    assert prod["model_version"] == "v1.0"
    assert prod["status"] == "production"


def test_09_crop_health_formula():
    """Tests agronomic crop health calculation across thresholds."""
    # Paddy: Healthy >= 0.60, Moderate >= 0.40, Severe < 0.40
    status_h, score_h = calculate_crop_health("Paddy", ndvi=0.75, ndwi=0.20, confidence=0.90)
    assert status_h == "Healthy"
    assert score_h > 0.70

    status_m, score_m = calculate_crop_health("Paddy", ndvi=0.48, ndwi=0.05, confidence=0.85)
    assert status_m == "Moderate Stress"

    status_s, score_s = calculate_crop_health("Paddy", ndvi=0.28, ndwi=-0.10, confidence=0.80)
    assert status_s == "Severe Stress"


def test_10_hazard_impact_assessment():
    """Tests multi-temporal hazard assessment distinguishing flood, drought, and normal."""
    # Flood: Water surge (+0.25 NDWI) and canopy destruction (-0.30 NDVI)
    flood_eval = assess_hazard_impact(
        crop_name="Paddy",
        current_ndvi=0.35,
        current_ndwi=0.30,
        baseline_ndvi=0.68,
        baseline_ndwi=0.05
    )
    assert flood_eval["hazard"] == "Flood"
    assert flood_eval["damage_percent"] > 0

    # Normal conditions
    normal_eval = assess_hazard_impact(
        crop_name="Banana",
        current_ndvi=0.72,
        current_ndwi=0.10,
        baseline_ndvi=0.70,
        baseline_ndwi=0.08
    )
    assert normal_eval["hazard"] == "None"
    assert normal_eval["damage_percent"] == 0.0


def test_11_rest_api_crops_latest():
    """Tests GET /api/crops/latest returns live FeatureCollection from database."""
    r = client.get("/api/crops/latest")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert data["total_features"] == 293
    assert data["latest_observation_date"] == "2026-09-09"
    # Verify properties
    feat = data["features"][0]
    props = feat["properties"]
    assert "crop_health" in props
    assert "hazard" in props
    assert "model_version" in props


def test_12_rest_api_crops_history():
    """Tests GET /api/crops/history returns available observation dates."""
    r = client.get("/api/crops/history")
    assert r.status_code == 200
    dates = r.json()
    assert len(dates) >= 2
    assert any(d["observation_date"] == "2026-09-09" for d in dates)
    assert any(d["observation_date"] == "2026-03-20" for d in dates)


def test_13_rest_api_hazards_and_health():
    """Tests GET /api/hazards/latest and GET /api/health/latest."""
    r_hz = client.get("/api/hazards/latest")
    assert r_hz.status_code == 200
    hz_data = r_hz.json()
    assert "hazard_breakdown" in hz_data

    r_hl = client.get("/api/health/latest")
    assert r_hl.status_code == 200
    hl_data = r_hl.json()
    assert "health_distribution" in hl_data
    assert "Healthy" in hl_data["health_distribution"]


def test_14_rest_api_data_status_freshness():
    """Tests GET /api/data-status returns freshness metrics."""
    r = client.get("/api/data-status")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data["status"] in ["Fresh", "Delayed", "Data may be outdated"]
    assert data["last_observation_date"] == "2026-09-09"


def test_15_rest_api_production_model_endpoint():
    """Tests GET /api/models/production returns active production model."""
    r = client.get("/api/models/production")
    assert r.status_code == 200
    meta = r.json()
    assert meta["model_version"] == "v1.0"
    assert meta["status"] == "production"
    assert len(meta["features_used"]) == 240
