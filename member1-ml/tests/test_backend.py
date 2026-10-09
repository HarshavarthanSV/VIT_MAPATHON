"""
Unit and Integration Tests for FastAPI Backend (Maintained by Member 1).
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
    assert data["study_area"]["target_crops"] == ["Paddy", "Banana", "Other"]


def test_get_statistics():
    response = client.get("/api/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "study_area_summary" in data
    assert "crop_distribution" in data
    
    summary = data["study_area_summary"]
    assert summary["total_parcels"] > 0
    assert summary["total_study_area_sq_km"] >= 20.0
    assert summary["meets_min_area_requirement"] is True

    dist = data["crop_distribution"]
    assert "Paddy" in dist
    assert "Banana" in dist
    assert "Other" in dist


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


def test_get_temporal_comparison():
    res = client.get("/api/temporal-comparison")
    assert res.status_code == 200
    data = res.json()
    assert "period_1" in data
    assert "period_2" in data
    assert "deltas" in data
    assert "ai_suggestions" in data
    assert len(data["ai_suggestions"]) >= 3
    assert data["deltas"]["paddy_area_ha_delta"] > 0


def test_chat_assistant():
    res = client.post("/api/chat", json={"message": "How do I improve paddy yield in Cheranmahadevi?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "Paddy" in data["reply"] or "paddy" in data["reply"] or "நெல்" in data["reply"]


def test_download_pdf_report():
    res = client.get("/api/reports/download-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "VIT_MAPATHON_Agricultural_Cadastral_Report.pdf" in res.headers.get("content-disposition", "")
    assert len(res.content) > 1000


def test_get_parcels_geojson():
    res = client.get("/api/parcels/geojson")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


def test_get_crops():
    res = client.get("/api/crops")
    assert res.status_code == 200
    data = res.json()
    assert "classes" in data
    assert "Paddy" in data["classes"]
    assert "Banana" in data["classes"]
    assert "Non-Crop" in data["classes"]
    assert "crop_summary" in data


def test_get_disaster_fund_priority():
    res = client.get("/api/fund-priority")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "priority_rankings" in data
    assert "total_damaged_area_ha" in data


def test_chat_parcel_crop_count():
    res = client.post("/api/chat", json={"message": "What is the crop count in PARCEL_0128?"})
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "PARCEL_0128" in reply
    assert "764" in reply  # Exact detected banana count from YOLOv8
    assert "Banana" in reply


def test_chat_planting_capacity():
    res = client.post("/api/chat", json={"message": "How many crops can be planted in PARCEL_0126?"})
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "PARCEL_0126" in reply
    assert "Planting Capacity" in reply
    assert "542" in reply  # Detected existing plants
    assert "Remaining Plantable" in reply


def test_chat_hazard_loss_rate():
    res = client.post("/api/chat", json={"message": "If flood occurs what is the loss rate for banana in PARCEL_0128?"})
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "PARCEL_0128" in reply
    assert "Disaster & Hazard Loss Valuation" in reply
    assert "SDRF" in reply
    assert "₹" in reply or "Rs" in reply


def test_chat_api_key_auto_capture():
    mock_key = "AIzaSyA_AUTOMATED_TEST_KEY_FOR_MAPATHON_35"
    res = client.post("/api/chat", json={"message": f"here is my api key: {mock_key}"})
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "Successfully Connected & Saved" in reply
    # Clean up test key from env
    from services.gemini_service import set_gemini_api_key
    set_gemini_api_key("", persist=True)



