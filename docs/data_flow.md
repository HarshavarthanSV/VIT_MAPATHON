# Data Flow Specification

## End-to-End Data Lifecycle

```
[Copernicus Open Access / Planetary Computer / Earth Engine]
                         │
                         ▼
           Member 2: Satellite Acquisition
  (Sentinel-2 L2A Scenes covering Ambasamudram & Cheranmahadevi)
                         │
                         ▼
        Preprocessing & Radiometric Calibration
  (Cloud masking via SCL, band resampling to 10m in EPSG:32643)
                         │
                         ▼
        Spectral Index & Temporal Stack Generation
  (NDVI, EVI, SAVI, NDWI per date + multi-temporal stacks)
                         │
                         ▼
  [member2-gis/outputs/features/*.tif, temporal/*, labels/training_polygons.geojson]
                         │
                         ▼  ◄── [MEMBER 1 DATA CONTRACT INGESTION]
          Member 1: Verification & Spatial Alignment
  (Ensure CRS EPSG:32643, identical affine transform, geometry validity)
                         │
                         ▼
         Spatial-Aware Group Train/Test Splitting
  (GroupShuffleSplit by polygon/parcel ID to prevent spatial autocorrelation leakage)
                         │
                         ▼
       Random Forest Classifier Training & Evaluation
  (Train sklearn RandomForestClassifier, dynamic calculation of F1, Accuracy, etc.)
                         │
                         ▼
      Parcel-Level Inference & Area Statistics Aggregation
  (Zonal pixel extraction, class voting/mean, confidence score calculation)
                         │
                         ▼
  [member1-ml/outputs/classified_parcels.geojson, crop_statistics.json, model_metrics.json]
                         │
                         ▼  ◄── [MEMBER 3 HANDOFF INGESTION]
         Member 3: PostGIS Import & REST API
  (PostGIS spatial indexes, FastAPI query endpoints /parcels, /statistics)
                         │
                         ▼
          Interactive React + Leaflet Dashboard
  (Color-coded parcel layers, crop filters, summary charts, parcel inspector)
```

## Data Schema Summary

### Member 2 → Member 1 Handoff
- `member2-gis/outputs/features/`: Single-band GeoTIFFs: `B02.tif`, `B03.tif`, `B04.tif`, `B08.tif`, `B11.tif`, `B12.tif`, `NDVI.tif`, `EVI.tif`, `SAVI.tif`, `NDWI.tif`.
- `member2-gis/outputs/temporal/`: Date-based folders (`date_01/`, `date_02/`, ...) with corresponding GeoTIFFs.
- `member2-gis/outputs/labels/training_polygons.geojson`: Vector polygons with properties `parcel_id` (or `id`) and `crop_type` (`Paddy`, `Banana`, `Other`).
- `member2-gis/outputs/parcels/parcel_boundaries.geojson`: All agricultural parcel boundaries to be classified across the study area ($\ge 20 \text{ km}^2$).

### Member 1 → Member 3 Handoff
- `member1-ml/outputs/classified_parcels.geojson`: FeatureCollection of polygon parcels with properties:
  - `parcel_id`: Unique identifier
  - `predicted_crop`: "Paddy" | "Banana" | "Other"
  - `confidence`: Float between 0.0 and 1.0 (from `predict_proba`)
  - `area_sq_km`: Float
  - `pixel_count`: Integer
  - `mean_ndvi`: Float (optional summary)
- `member1-ml/outputs/crop_statistics.json`: Aggregated parcel count, total area, and percentage per crop class.
- `member1-ml/outputs/model_metrics.json`: Overall and per-class precision, recall, f1-score, accuracy, confusion matrix.
- `member1-ml/outputs/feature_importance.json`: Mapped feature importance rankings.
- `member1-ml/models/crop_classifier.joblib`: Trained scikit-learn model artifact.
