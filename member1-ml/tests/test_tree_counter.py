"""
Member 1 — AI / Computer Vision Engineer
Tests for Individual Tree & Plant Counting Module
"""

import os
import json
import pytest
import pandas as pd
import geopandas as gpd
from fastapi.testclient import TestClient

import sys
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from main import app

client = TestClient(app)


def test_tree_count_deliverables_exist():
    """Verifies that all 4 required deliverables exist in results/tree_count/."""
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "tree_count"))
    
    assert os.path.exists(os.path.join(results_dir, "tree_detections.geojson")), "tree_detections.geojson missing"
    assert os.path.exists(os.path.join(results_dir, "parcel_tree_counts.csv")), "parcel_tree_counts.csv missing"
    assert os.path.exists(os.path.join(results_dir, "tree_count_summary.json")), "tree_count_summary.json missing"
    assert os.path.exists(os.path.join(results_dir, "tree_detection_map.png")), "tree_detection_map.png missing"


def test_geojson_detections_schema():
    """Verifies tree_detections.geojson CRS, schema, and non-empty geometries."""
    geojson_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "tree_count", "tree_detections.geojson"))
    gdf = gpd.read_file(geojson_path)
    
    assert len(gdf) > 1000, "Should contain detected trees"
    assert str(gdf.crs) == "EPSG:4326", "Must be in geographic WGS84 for web consumption"
    
    required_cols = ["detection_id", "class_name", "confidence", "parcel_id", "latitude", "longitude"]
    for col in required_cols:
        assert col in gdf.columns, f"Missing required column: {col}"
        
    # Valid class names
    valid_classes = {"banana", "coconut", "other_tree"}
    assert set(gdf["class_name"].unique()).issubset(valid_classes)
    assert (gdf["confidence"] >= 0.0).all() and (gdf["confidence"] <= 1.0).all()


def test_parcel_tree_counts_csv_structure():
    """Verifies parcel_tree_counts.csv records, non-negative values, and density computation."""
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "tree_count", "parcel_tree_counts.csv"))
    df = pd.read_csv(csv_path)
    
    assert len(df) == 293, "Must cover all 293 agricultural parcels in the study area"
    required_cols = [
        "parcel_id", "crop_type", "area_ha", "banana_count",
        "coconut_count", "other_tree_count", "total_tree_count", "plant_density"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
        
    assert (df["banana_count"] >= 0).all()
    assert (df["coconut_count"] >= 0).all()
    assert (df["total_tree_count"] >= 0).all()
    assert (df["plant_density"] >= 0.0).all()

    # Check density calculation for active parcels
    active = df[df["total_tree_count"] > 0]
    assert len(active) > 0, "Must have active parcels with trees"
    for _, row in active.head(10).iterrows():
        expected_density = round(row["total_tree_count"] / row["area_ha"], 1)
        assert abs(row["plant_density"] - expected_density) <= 0.2


def test_summary_json_contains_accuracy_and_limitations():
    """Verifies that summary JSON contains real evaluation metrics and physical limitations."""
    summary_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "results", "tree_count", "tree_count_summary.json"))
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "model_detection_performance" in data
    assert "counting_accuracy_metrics" in data
    assert "methodology_and_limitations" in data
    
    det = data["model_detection_performance"]
    assert "precision" in det and "recall" in det and "mAP50" in det
    assert det["precision"] > 0.0
    
    counting = data["counting_accuracy_metrics"]
    assert "total_actual_count" in counting
    assert "total_predicted_count" in counting
    assert "absolute_count_error" in counting
    assert "percentage_count_error" in counting
    
    # Limitations statement check
    limitation = data["methodology_and_limitations"]["macro_vs_micro_fusion"]
    assert "Sentinel-2" in limitation
    assert "High-resolution" in limitation or "high-resolution" in limitation


def test_backend_tree_counts_endpoints():
    """Verifies FastAPI REST endpoints for tree counts and summary."""
    res = client.get("/api/tree-counts?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total_parcels" in data
    assert len(data["data"]) == 10
    assert "banana_count" in data["data"][0]
    
    res_summary = client.get("/api/tree-counts/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert "imagery_specifications" in summary_data
    assert "model_detection_performance" in summary_data
