# Member 1 → Member 3 Handoff Specification

## 1. Overview
This document specifies the exact artifacts and data schemas produced by **Member 1 (ML / AI Engineer)** for direct consumption by **Member 3 (Full Stack / GIS Application Engineer)**.

All outputs are saved in `member1-ml/outputs/` and `member1-ml/models/`.

---

## 2. Handoff Deliverables

| Deliverable File | Description | Target Use by Member 3 |
| :--- | :--- | :--- |
| `member1-ml/outputs/classified_parcels.geojson` | Standard GeoJSON FeatureCollection of all classified agricultural parcels | Ingestion into PostGIS database & Leaflet vector display |
| `member1-ml/outputs/crop_statistics.json` | Aggregated crop counts, area in sq. km, hectares, and percentages | Backend `/api/statistics` endpoint & Frontend summary cards/charts |
| `member1-ml/outputs/model_metrics.json` | Model evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) | Backend `/api/metrics` endpoint & Frontend model performance tab |
| `member1-ml/outputs/feature_importance.json` | Ranked feature importance scores | Frontend ML explanation tab |
| `member1-ml/outputs/confusion_matrix.png` | Pre-rendered confusion matrix heatmap | Visual display in dashboard |
| `member1-ml/outputs/feature_importance.png` | Pre-rendered feature importance bar chart | Visual display in dashboard |
| `member1-ml/models/crop_classifier.joblib` | Trained scikit-learn Random Forest model | Optional on-the-fly inference backend service |

---

## 3. GeoJSON Schema (`classified_parcels.geojson`)

### Coordinate System
- **CRS**: Standard **WGS 84 (`EPSG:4326`)** (latitude / longitude in decimal degrees). This ensures instant compatibility with Leaflet, React-Leaflet, and Mapbox without client-side reprojection.
- Note: All area calculations (`area_sq_km`, `area_ha`) were geometrically computed in metric UTM Zone 43N (`EPSG:32643`) before export to prevent latitude distortion errors.

### Feature Properties Schema
Each GeoJSON `Feature` has the following properties:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[77.451, 8.702], [77.456, 8.702], [77.456, 8.708], [77.451, 8.708], [77.451, 8.702]]]
  },
  "properties": {
    "parcel_id": "parcel_00142",
    "predicted_crop": "Paddy",
    "confidence": 0.9245,
    "area_sq_km": 0.0452,
    "area_ha": 4.52,
    "prob_paddy": 0.9245,
    "prob_banana": 0.0512,
    "prob_other": 0.0243
  }
}
```

### Crop Color Guidelines for Leaflet Frontend
- **Paddy**: Emerald Green (`#2e7d32` or `#4caf50`)
- **Banana**: Golden Yellow / Amber (`#fbc02d` or `#ffb300`)
- **Other**: Slate Gray (`#78909c` or `#9e9e9e`)

---

## 4. Crop Statistics Schema (`crop_statistics.json`)

```json
{
  "study_area_summary": {
    "total_parcels": 2450,
    "total_study_area_sq_km": 34.82,
    "total_study_area_hectares": 3482.0,
    "overall_mean_confidence": 0.8942,
    "meets_min_area_requirement": true
  },
  "crop_distribution": {
    "Paddy": {
      "parcel_count": 1420,
      "percentage_of_parcels": 57.96,
      "area_sq_km": 21.45,
      "area_hectares": 2145.0,
      "percentage_of_total_area": 61.60,
      "mean_confidence": 0.9124
    },
    "Banana": {
      "parcel_count": 680,
      "percentage_of_parcels": 27.76,
      "area_sq_km": 9.12,
      "area_hectares": 912.0,
      "percentage_of_total_area": 26.19,
      "mean_confidence": 0.8841
    },
    "Other": {
      "parcel_count": 350,
      "percentage_of_parcels": 14.28,
      "area_sq_km": 4.25,
      "area_hectares": 425.0,
      "percentage_of_total_area": 12.21,
      "mean_confidence": 0.8412
    }
  }
}
```

---

## 5. Model Metrics Schema (`model_metrics.json`)

```json
{
  "overall": {
    "accuracy": 0.9150,
    "precision_macro": 0.9080,
    "precision_weighted": 0.9160,
    "recall_macro": 0.9020,
    "recall_weighted": 0.9150,
    "f1_score_macro": 0.9048,
    "f1_score_weighted": 0.9152,
    "total_test_samples": 490
  },
  "per_class": {
    "Paddy": {
      "precision": 0.9320,
      "recall": 0.9410,
      "f1_score": 0.9365,
      "support": 284
    },
    "Banana": {
      "precision": 0.8950,
      "recall": 0.8780,
      "f1_score": 0.8864,
      "support": 136
    },
    "Other": {
      "precision": 0.8970,
      "recall": 0.8870,
      "f1_score": 0.8920,
      "support": 70
    }
  }
}
```

---

## 6. Suggested PostGIS & FastAPI Integration

### Recommended PostGIS Table DDL
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE agricultural_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    predicted_crop VARCHAR(30) NOT NULL,
    confidence FLOAT NOT NULL,
    area_sq_km FLOAT NOT NULL,
    area_ha FLOAT NOT NULL,
    prob_paddy FLOAT,
    prob_banana FLOAT,
    prob_other FLOAT,
    geom GEOMETRY(Geometry, 4326) NOT NULL
);

CREATE INDEX idx_parcels_geom ON agricultural_parcels USING GIST (geom);
CREATE INDEX idx_parcels_crop ON agricultural_parcels (predicted_crop);
```

### Suggested FastAPI Endpoints
- `GET /api/parcels` — Returns GeoJSON FeatureCollection with optional query param `?crop=Paddy`.
- `GET /api/parcels/{parcel_id}` — Returns specific parcel metadata and coordinates.
- `GET /api/statistics` — Serves `crop_statistics.json`.
- `GET /api/metrics` — Serves `model_metrics.json`.
