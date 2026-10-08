# Member 1 — ML & Backend Integration Specification

## 1. Overview
In the **2-Member Architecture**, **Member 1 (AI / Machine Learning & Backend Systems)** owns both the training/inference pipeline and the FastAPI REST backend service that serves the model deliverables to the Web GIS frontend (developed by Member 2).

All model deliverables are stored in `member1-ml/outputs/` and `member1-ml/models/`, and are directly served via FastAPI routes under `member1-ml/backend/`.

---

## 2. Integrated Deliverables & Endpoints

| Deliverable File | Description | FastAPI Endpoint (`member1-ml/backend`) | Frontend Consumer (`member2-gis/frontend`) |
| :--- | :--- | :--- | :--- |
| `member1-ml/outputs/classified_parcels.geojson` | Standard GeoJSON FeatureCollection of all classified agricultural parcels | `GET /api/parcels` | Leaflet color-coded vector layer, filters, parcel inspection popups |
| `member1-ml/outputs/crop_statistics.json` | Aggregated crop counts, area in sq. km, hectares, and percentages | `GET /api/statistics` | Dashboard summary cards & crop distribution charts |
| `member1-ml/outputs/model_metrics.json` | Model evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) | `GET /api/metrics` | Model performance modal |
| `member1-ml/outputs/feature_importance.json` | Ranked feature importance scores | `GET /api/metrics` | Feature importance rankings table |
| `member1-ml/outputs/confusion_matrix.png` | Pre-rendered confusion matrix heatmap | `GET /static/confusion_matrix.png` | Performance modal visual display |
| `member1-ml/outputs/feature_importance.png` | Pre-rendered feature importance bar chart | `GET /static/feature_importance.png` | Performance modal visual display |
| `member1-ml/models/crop_classifier.joblib` | Trained scikit-learn Random Forest model | Ingested by backend for inference | Backend pipeline |
| Multi-Temporal Sentinel-2 Indices | Bi-seasonal analysis (Kuruvai vs Samba) | `GET /api/temporal-comparison` | Temporal comparison modal & AI suggestions |
| Agronomic Advisory Model | Conversational agronomic advice for farmers | `POST /api/chat` | Agri-AI chatbot drawer |
| Cadastral PDF Report Generator | Automated 3-page formal assessment report | `GET /api/reports/download-pdf` | Download PDF button |

---

## 3. GeoJSON Schema (`classified_parcels.geojson`)

### Coordinate System
- **CRS**: Standard **WGS 84 (`EPSG:4326`)** (latitude / longitude in decimal degrees). This ensures instant compatibility with Leaflet and React-Leaflet without client-side reprojection.
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
    "prob_banana": 0.0210,
    "prob_other": 0.0545,
    "prob_paddy": 0.9245,
    "taluk": "Ambasamudram"
  }
}
```
