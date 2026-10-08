"""
Unit and Integration Tests for Member 3 FastAPI Backend.
Verifies endpoints, response structures, filtering logic, and error handling.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "study_area" in data


def test_get_statistics():
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "study_area_summary" in data
    assert "crop_distribution" in data
    
    summary = data["study_area_summary"]
    assert summary["total_parcels"] == 293
    assert summary["total_study_area_hectares"] > 100.0

    dist = data["crop_distribution"]
    assert "Paddy" in dist
    assert "Banana" in dist
    assert "Non-Crop" in dist
    assert dist["Paddy"]["parcel_count"] == 83
    assert dist["Banana"]["parcel_count"] == 79
    assert dist["Non-Crop"]["parcel_count"] == 131


def test_get_crops():
    response = client.get("/api/crops")
    assert response.status_code == 200
    crops = response.json()
    assert isinstance(crops, list)
    crop_names = {c["crop"] for c in crops}
    assert "Paddy" in crop_names
    assert "Banana" in crop_names
    assert "Non-Crop" in crop_names


def test_get_parcels_geojson():
    response = client.get("/api/parcels/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 293


def test_get_metrics():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "per_class" in data
    assert data["overall"]["accuracy"] > 0.85
    assert "Paddy" in data["per_class"]


def test_get_feature_importance():
    response = client.get("/api/feature-importance")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert "NDVI_mean" in data


def test_get_parcels_all():
    response = client.get("/api/parcels")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

    first = data["features"][0]
    assert "geometry" in first
    assert "properties" in first
    props = first["properties"]
    assert "parcel_id" in props
    assert "predicted_crop" in props
    assert "confidence" in props
    assert "area_sq_km" in props


def test_get_parcels_filter_crop():
    response = client.get("/api/parcels?crop=Paddy")
    assert response.status_code == 200
    data = response.json()
    for feat in data["features"]:
        assert feat["properties"]["predicted_crop"] == "Paddy"


def test_get_parcels_filter_confidence():
    response = client.get("/api/parcels?min_confidence=0.85")
    assert response.status_code == 200
    data = response.json()
    for feat in data["features"]:
        assert feat["properties"]["confidence"] >= 0.85


def test_get_parcel_detail():
    list_res = client.get("/api/parcels?limit=1")
    assert list_res.status_code == 200
    features = list_res.json()["features"]
    assert len(features) == 1
    p_id = features[0]["properties"]["parcel_id"]

    detail_res = client.get(f"/api/parcels/{p_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["parcel_id"] == p_id
    assert "predicted_crop" in detail
    assert "probabilities" in detail


def test_get_parcel_detail_not_found():
    res = client.get("/api/parcels/non_existent_parcel_99999")
    assert res.status_code == 404


def test_get_taluk_acreage():
    res = client.get("/api/statistics/taluk-acreage")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    taluks = {row["taluk"] for row in data}
    assert "Ambasamudram" in taluks or "Cheranmahadevi" in taluks


def test_get_places():
    res = client.get("/api/places")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any("Ambasamudram" in p.get("name", "") for p in data)


def test_get_infrastructure():
    res = client.get("/api/infrastructure")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_get_latest_hazard():
    res = client.get("/api/hazards/latest")
    assert res.status_code == 200
    data = res.json()
    assert "hazard_id" in data
    assert "total_inundated_area_ha" in data
    assert data["total_inundated_area_ha"] > 0
    assert "geojson" in data


def test_get_latest_damage():
    res = client.get("/api/damage/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 293
    first = data["features"][0]["properties"]
    assert "affected_area_ha" in first
    assert "damage_percentage" in first
    assert "severity" in first


def test_get_damage_by_crop():
    res = client.get("/api/damage/by-crop")
    assert res.status_code == 200
    data = res.json()
    assert "crop_damage_breakdown" in data
    assert len(data["crop_damage_breakdown"]) > 0


def test_get_fund_priority():
    res = client.get("/api/fund-priority")
    assert res.status_code == 200
    data = res.json()
    assert "crop_allocation_summary" in data
    assert "top_priority_parcels" in data
    assert data["total_priority_score_sum"] > 0


def test_get_fund_allocation():
    res = client.get("/api/fund-allocation?total_fund=5000000")
    assert res.status_code == 200
    data = res.json()
    assert data["input_relief_fund_pool_inr"] == 5000000
    assert "crop_allocation_recommendations" in data
    assert len(data["crop_allocation_recommendations"]) > 0


