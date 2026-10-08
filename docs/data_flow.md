# Data Flow Specification (2-Member Architecture)

## End-to-End Data Lifecycle

```
[Copernicus Open Access / Planetary Computer / Earth Engine]
                         │
                         ▼
           Member 2: Satellite Acquisition & Processing
  (Sentinel-2 L2A Scenes covering Ambasamudram & Cheranmahadevi, Tirunelveli)
                         │
                         ▼
        Preprocessing & Radiometric Calibration (Member 2)
  (Cloud masking via SCL, band resampling to 10m in EPSG:32643)
                         │
                         ▼
        Spectral Index & Temporal Stack Generation (Member 2)
  (NDVI, EVI, SAVI, NDWI per date + multi-temporal stacks)
                         │
                         ▼
  [data/features/tabular/ml_training_dataset.csv, member2-gis/inputs/aoi_*.geojson]
                         │
                         ▼  ◄── [MEMBER 1 DATA CONTRACT INGESTION]
          Member 1: Verification & Spatial Alignment
  (Ensure CRS EPSG:32643, dimensions, bounds, zero NaN data checks)
                         │
                         ▼
         Spatial-Aware Group Train/Test Splitting (Member 1)
  (GroupShuffleSplit by parcel ID to prevent spatial autocorrelation leakage)
                         │
                         ▼
       Random Forest Classifier Training & Evaluation (Member 1)
  (Train sklearn RandomForestClassifier, dynamic calculation of F1, Accuracy, etc.)
                         │
                         ▼
      Parcel-Level Inference & Area Statistics Aggregation (Member 1)
  (Zonal extraction, voting, confidence calculation, classified_parcels.geojson)
                         │
                         ▼
         Member 1: PostGIS Database & FastAPI REST Backend
  (Endpoints: /api/parcels, /api/statistics, /api/metrics, /api/temporal-comparison, /api/chat, /api/reports/download-pdf)
                         │
                         ▼  ◄── [REST API CONSUMPTION]
       Member 2: Interactive React + Leaflet Dashboard
  (Color-coded parcel layers, crop filters, summary charts, parcel inspector, AI Chatbot modal)
```

## Data Schema Summary

### Member 2 → Member 1 Handoff
- `data/features/tabular/ml_training_dataset.csv`: 293 parcels with 240 extracted spectral band and index features across 4 dates.
- `member2-gis/inputs/`: Real boundary files (`aoi_ambasamudram_cheranmahadevi.geojson`), infrastructure lines (`real_infrastructure.geojson`), and village points (`real_places.json`).
- `data/parcels/cleaned/parcels.geojson`: All agricultural parcel boundaries to be classified across the study area ($240.65 \text{ km}^2$).

### Member 1 → Frontend Serving (Member 2 Dashboard)
- `member1-ml/outputs/classified_parcels.geojson`: FeatureCollection of polygon parcels with properties:
  - `parcel_id`: Unique identifier
  - `predicted_crop`: "Paddy" | "Banana" | "Other"
  - `confidence`: Float between 0.0 and 1.0 (from `predict_proba`)
  - `area_sq_km`: Float
  - `area_ha`: Float
  - `mean_ndvi`: Float (optional summary)
- `member1-ml/outputs/crop_statistics.json`: Aggregated parcel count, total area, and percentage per crop class.
- `member1-ml/outputs/model_metrics.json`: Overall and per-class precision, recall, f1-score, accuracy, confusion matrix.
- `member1-ml/outputs/feature_importance.json`: Mapped feature importance rankings.
- `member1-ml/models/crop_classifier.joblib`: Trained scikit-learn model artifact.
