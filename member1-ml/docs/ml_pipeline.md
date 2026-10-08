# Member 1 ML / AI Pipeline Specification

## 1. Overview
The Machine Learning module processes Sentinel-2 Level-2A multi-spectral imagery and spectral indices prepared by Member 2, trains a Random Forest Classifier to distinguish **Paddy**, **Banana**, and **Other** crops, rigorously evaluates model performance, and produces classified parcel GeoJSON and summary statistics for backend serving and web GIS visualization.

---

## 2. End-to-End Pipeline Stages

```
[ Member 2 Feature GeoTIFFs + training_polygons.geojson ]
                         │
                         ▼
             Stage 1: Input Validation
  - validate_raster_metadata (CRS: EPSG:32643, width, height, nodata, NaN/Inf)
  - validate_raster_alignment (identical transform and spatial grid)
  - validate_labels_file (valid geometry, reprojection, class mapping)
                         │
                         ▼
             Stage 2: Feature Extraction
  - Extract multi-spectral bands (B02, B03, B04, B08, B11, B12)
  - Extract indices (NDVI, EVI, SAVI, NDWI)
  - Dynamic multi-temporal statistics (mean, std, min, max, range) if temporal stacks exist
                         │
                         ▼
        Stage 3: Spatial-Aware Train/Test Split
  - GroupShuffleSplit grouped by parcel_id (test_size = 20%)
  - Guarantees zero spatial autocorrelation leakage between train and test parcels
                         │
                         ▼
         Stage 4: Random Forest Model Training
  - sklearn.ensemble.RandomForestClassifier
  - class_weight="balanced", n_estimators=150, max_depth=16
  - Exports artifact: member1-ml/models/crop_classifier.joblib
                         │
                         ▼
             Stage 5: Dynamic Evaluation
  - Computes Accuracy, Precision (macro/weighted), Recall, F1-score
  - Computes Confusion Matrix (raw + normalized) -> confusion_matrix.png
  - Computes Feature Importances (MDI) -> feature_importance.json & .png
  - Exports metrics: member1-ml/outputs/model_metrics.json
                         │
                         ▼
          Stage 6: Parcel-Level Classification
  - Zonal extraction across all parcel boundaries in study area
  - Predicts crop type + probability confidence via predict_proba()
  - Validates total study area (>= 20 sq. km requirement)
  - Exports: member1-ml/outputs/classified_parcels.geojson
  - Exports: member1-ml/outputs/crop_statistics.json
```

---

## 3. Spatial Leakage Prevention Strategy
In geospatial machine learning, random pixel-level train/test splitting leads to severe spatial autocorrelation leakage: adjacent pixels from the same field share virtually identical spectral signatures, artificially inflating validation accuracy.

To ensure true model generalization to unseen agricultural fields:
- **Group-Aware Splitting**: We group samples by `parcel_id`.
- `GroupShuffleSplit` assigns all pixels / samples of an entire agricultural parcel exclusively to either the training set OR the test set.
- The reported evaluation metrics reflect real-world generalization to unvisited farm parcels across Ambasamudram and Cheranmahadevi.

---

## 4. Multi-Temporal Feature Logic
- **Paddy phenology**: Initial transplanting phase shows high soil moisture / water inundation (high NDWI, low NDVI), followed by rapid tillering and heading (steep NDVI growth), followed by senescence/harvesting drop.
- **Banana phenology**: Perennial horticulture crop with year-round canopy, maintaining high, relatively steady NDVI and EVI throughout multiple dates.
- When multi-temporal dates are provided by Member 2, the pipeline calculates:
  - `NDVI_temporal_mean`, `NDVI_temporal_std`, `NDVI_temporal_min`, `NDVI_temporal_max`, `NDVI_temporal_range`
  - Per-date spectral snapshots (`NDVI_date1`, `NDVI_date2`, etc.)

---

## 5. Execution Commands

To run the pipeline with default configuration:
```bash
python member1-ml/main.py --config member1-ml/config/config.yaml
```

To run with custom CLI overrides:
```bash
python member1-ml/main.py \
  --features-dir member2-gis/outputs/features \
  --temporal-dir member2-gis/outputs/temporal \
  --labels-file member2-gis/outputs/labels/training_polygons.geojson \
  --parcels-file member2-gis/outputs/parcels/parcel_boundaries.geojson
```

To run automated tests:
```bash
pytest member1-ml/tests/ -v
```
