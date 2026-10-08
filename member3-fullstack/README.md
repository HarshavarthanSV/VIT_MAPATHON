# Member 3 — Full Stack & Web GIS Module

## Responsibilities
- Ingest `classified_parcels.geojson`, `crop_statistics.json`, and `model_metrics.json` produced by Member 1 (`member1-ml/outputs/`).
- Design and initialize PostGIS database schema to store parcel geometries, spatial attributes, and crop classification results.
- Develop FastAPI REST API providing endpoints for:
  - `GET /api/parcels` (GeoJSON FeatureCollection with crop type, confidence, area)
  - `GET /api/parcels/{id}` (Specific parcel details)
  - `GET /api/statistics` (Aggregated statistics: counts, area in sq km per crop)
  - `GET /api/metrics` (Model evaluation metrics: Accuracy, Precision, Recall, F1, Confusion Matrix)
- Develop React + Leaflet frontend dashboard:
  - Color-coded parcel boundaries (Paddy = Green, Banana = Gold/Yellow, Other = Gray)
  - Crop filter checkboxes (Toggle Paddy, Banana, Other)
  - Interactive parcel popup on click (ID, Predicted Crop, Confidence %, Area)
  - Summary metric cards and charts (Area distribution, Crop distribution)
  - Basemap switcher (Satellite imagery vs OSM standard)
