# Model Upgrade Analysis: Parcel-Level Agricultural Crop Classification
**Project**: VIT MAPATHON — Agricultural Land Parcel & Crop Identification  
**Location**: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu (Study Area: 240.64 km²)  
**Document**: `docs/model_upgrade_analysis.md`  
**Date**: October 2026  
**Phase**: Phase 1 — Comprehensive Inspection & Architectural Upgrade Plan  

---

## 1. Executive Summary & Objective

The objective of this upgrade is to enhance the parcel-level crop classification pipeline for the three target agricultural categories:
1. **Paddy** (Wetland rice)
2. **Banana** (Riparian perennial plantation)
3. **Other** (Fallow, scrubland, water bodies, built-up infrastructure, mixed vegetation)

The current production baseline model (Random Forest, 200 estimators, 240 multi-temporal features) achieves **88.14% Overall Accuracy** and **87.06% Macro-F1** on the 20% holdout test set (59 parcels) with 5-fold cross-validation mean accuracy of **83.78%**. The historical project slide reported **91.84% accuracy** (Macro-F1: 0.9082) on an earlier split. 

The primary goal is to upgrade the feature engineering, temporal modeling, and algorithm benchmarking to improve generalization and target approximately **95% overall accuracy if scientifically supported by the data**, strictly adhering to:
- **No artificial forcing** or hardcoded predictions.
- **Zero spatial leakage** via strict parcel-level `GroupShuffleSplit` / `StratifiedGroupKFold`.
- **Defensible scientific methodology** grounded in Sentinel-2 optical physics, red-edge spectroscopy, phenological curves, and robust zonal statistics.
- **Complete backward compatibility** with the existing FastAPI backend, PostGIS schema, and React-Leaflet GIS dashboard.

---

## 2. Inspection of Existing Pipeline Architecture

### 2.1 Codebase Structure & Pipeline Flow

The repository contains two coordinated member sub-systems:
```
d:\VIT\
├── member1-ml\                      # Machine Learning & Backend Systems
│   ├── backend\                     # FastAPI REST API (routers: parcels, statistics, analysis, production_monitoring)
│   ├── classification\              # ParcelClassifier, train.py, predict.py
│   ├── config\config.yaml           # Pipeline hyperparameters & paths
│   ├── evaluation\                  # metrics.py, confusion_matrix.py, feature_importance.py
│   ├── models\                      # model_registry.py, crop_classifier.joblib
│   ├── pipelines\                   # training_pipeline.py, inference_pipeline.py, agronomic_indicators.py
│   ├── preprocessing\               # dataset_builder.py, feature_loader.py, label_loader.py, validation.py
│   ├── tests\                       # 50 unit and integration tests (all passing)
│   └── train_on_member2_data.py     # End-to-end training script on tabular features
├── member2-gis\                     # Remote Sensing & GIS Platform
│   ├── frontend\                    # React 18 + Vite + Leaflet Web GIS Dashboard (Port 5174)
│   ├── inputs\                      # aoi_ambasamudram_cheranmahadevi.geojson, real_infrastructure.geojson
│   ├── outputs\features\            # 10 GeoTIFFs (B02, B03, B04, B08, B11, B12, NDVI, EVI, SAVI, NDWI)
│   └── scripts\                     # acquire_sentinel2_l2a.py, generate_realistic_cadastral_parcels.py
├── preprocessing\                   # Shared Preprocessing & Feature Extraction
│   ├── align_bands.py               # Bilinear (reflectance) & Nearest (SCL) resampling to 10m grid
│   ├── calculate_indices.py         # NDVI, EVI, SAVI, NDWI array computations
│   ├── clip_aoi.py                  # AOI clipping
│   ├── cloud_mask.py                # SCL cloud & shadow filtering
│   ├── create_temporal_stack.py     # 60-layer multi-temporal GeoTIFF generator
│   └── extract_training_features.py # Zonal statistics extraction (mean, std, min, max) -> tabular CSV
├── data\
│   ├── aoi\study_area.geojson       # Ambasamudram (122.14 km²) + Cheranmahadevi (118.51 km²) = 240.64 km²
│   ├── features\tabular\            # ml_training_dataset.csv (293 parcels, 243 columns)
│   ├── features\temporal\           # feature_metadata.json (60 layer descriptions)
│   ├── parcels\cleaned\             # parcels.geojson, classified_parcels.geojson
│   └── parcels\training\            # training_labels.geojson
└── S2A_MSIL2A_20260320T...SAFE.zip  # Full 1.14 GB Sentinel-2 L2A archive with R10m & R20m bands
```

### 2.2 Existing Training & Inference Flow

1. **Input Data**:
   - 4 multi-temporal Sentinel-2 Level-2A observations:
     - `2026-03-20` (Pre-monsoon / land preparation)
     - `2026-04-02` (Early vegetative growth)
     - `2026-04-22` (Peak canopy / reproductive stage)
     - `2026-09-09` (Late season / second crop cycle)
   - Bands: 6 spectral bands (`B02`, `B03`, `B04`, `B08`, `B11`, `B12`) + `SCL`.
   - Indices: 4 standard vegetation/water indices (`NDVI`, `EVI`, `SAVI`, `NDWI`).
   - Summary statistics: 5 temporal stats across the 4 dates for each of the 4 indices (`mean`, `min`, `max`, `std`, `range`).
   - Total raster layers: $(6 \text{ bands} + 4 \text{ indices}) \times 4 \text{ dates} + (4 \text{ indices} \times 5 \text{ stats}) = 40 + 20 = 60 \text{ channels}$.
2. **Parcel Zonal Feature Extraction**:
   - For each of the 293 parcels, 4 zonal summary statistics (`mean`, `std`, `min`, `max`) are extracted per layer.
   - Result: $60 \text{ layers} \times 4 \text{ stats} = 240 \text{ feature columns}$ in `ml_training_dataset.csv`.
3. **Training & Validation**:
   - `RandomForestClassifier(n_estimators=200, max_depth=15, min_samples_split=4, min_samples_leaf=2, class_weight='balanced')`.
   - Split: 80% train (234 parcels) / 20% test (59 parcels) using stratified holdout.
   - 5-Fold Stratified Cross-Validation on training data.
   - Missing values imputed using column median.
4. **Outputs & Deliverables**:
   - Model artifact: `models/crop_classifier/v1.0/crop_classifier.joblib`.
   - Vector deliverable: `data/parcels/cleaned/classified_parcels.geojson` (EPSG:4326) containing `parcel_id`, `predicted_crop`, `confidence`, `prob_paddy`, `prob_banana`, `prob_other`, `area_sq_km`, `area_ha`.
   - Statistics: `member1-ml/outputs/crop_statistics.json`.
   - Metrics: `member1-ml/outputs/model_metrics.json`.
   - Visual plots: `confusion_matrix.png`, `feature_importance.png`.

---

## 3. Analysis of Current Limitations

Through our inspection of the existing pipeline, we identified six critical limitations explaining why certain fields and vegetation areas are misclassified:

| # | Current Limitation | Root Cause & Evidence | Impact on Classification |
|---|---|---|---|
| 1 | **Missing Red-Edge Bands (B05, B06, B07, B8A)** | The existing pipeline only loads `B02, B03, B04, B08, B11, B12`. The Sentinel-2 red-edge bands (705 nm, 740 nm, 783 nm) and narrow NIR (865 nm) are omitted despite being present in the SAFE archive. | Banana has thick, broad, high-chlorophyll leaf structures causing distinct red-edge slope steepening, whereas flooded paddy exhibits unique red-edge reflection during tillering. Omitting red-edge bands impairs Paddy vs. Banana discrimination. |
| 2 | **Absence of Advanced Indices & Moisture Metrics** | Only 4 indices (NDVI, EVI, SAVI, NDWI) are used. Advanced chlorophyll indices (NDRE1, NDRE2, NDRE3, MTCI, CIred-edge) and soil/moisture indices (NDMI, MSI, EVI2, MSAVI) are missing. | NDVI saturates at high leaf area index ($\text{LAI} > 3$), making dense banana plantations and mature paddy canopies look indistinguishable at peak growth. Red-edge indices do not saturate at high biomass. |
| 3 | **Lack of Spectral Relationship Features (Ratios & Differences)** | No direct cross-band ratios or differences (e.g., $B08/B04$, $B08/B05$, $B08/B11$, $B08 - B11$) are explicitly engineered. | Water-backed flooded paddy fields show heavy SWIR absorption relative to NIR; banana orchards maintain higher SWIR reflectance from woody biomass and soil background. |
| 4 | **Crude Temporal Modeling (No Phenology Fingerprinting)** | The existing temporal features only compute basic per-pixel temporal statistics (`mean`, `min`, `max`, `std`, `range`). No crop growth dynamics are modeled: peak NDVI/NDRE timing, growth rates, decline rates, seasonal amplitudes, or green-up duration. | Banana is a perennial 11–12 month crop with year-round high greenness, while Paddy is a sharp 105–130 day seasonal cycle with rapid flooding, green-up, and harvest decline. Phenological curves are the single most powerful discriminator between Paddy and Banana. |
| 5 | **Missing Robust Percentile Zonal Statistics** | Parcels currently only extract `mean`, `std`, `min`, `max`. Min and max are notoriously sensitive to edge pixels, parcel boundary slivers, and tree shadow noise. | Robust percentiles ($P_{10}, P_{25}, P_{50}, P_{75}, P_{90}$) are needed to insulate zonal parcel signatures from border effects and tree shadows. |
| 6 | **Lack of Rigorous Grouped Cross-Validation & Algorithm Comparison** | Only Random Forest is evaluated. No benchmarking against gradient boosted decision trees (XGBoost), no formal feature selection, and validation was run with standard `StratifiedKFold` rather than strictly checking spatial stability across parcel groups. | Hyperparameter tuning and gradient boosting on non-linear phenology features can yield significant generalization gains over default Random Forest. |

---

## 4. Available Data Assets

| Data Asset | Path | Details | Status |
|---|---|---|---|
| **Raw Sentinel-2 L2A Archive** | `S2A_MSIL2A_20260320T...SAFE.zip` | 1.14 GB archive. Contains all 10m bands (B02, B03, B04, B08) and 20m bands (**B05, B06, B07, B8A**, B11, B12, SCL). Native EPSG:32643. | **Available & Verified** |
| **Existing Multi-Temporal Tabular Dataset** | `data/features/tabular/ml_training_dataset.csv` | 293 parcels $\times$ 240 features across 4 dates (`2026-03-20`, `2026-04-02`, `2026-04-22`, `2026-09-09`). | **Available & Verified** |
| **Parcel Boundaries (Vectors)** | `data/parcels/cleaned/parcels.geojson` | 293 agricultural parcels in Ambasamudram & Cheranmahadevi (EPSG:32643). | **Available & Verified** |
| **Ground Truth Training Labels** | `data/parcels/training/training_labels.geojson` | 293 labeled parcels: Paddy (119), Banana (109), Other (65). | **Available & Verified** |
| **Study Area AOI** | `data/aoi/study_area.geojson` | 240.64 km² covering Ambasamudram & Cheranmahadevi Taluks. | **Available & Verified** |
| **Processed Raster Features** | `member2-gis/outputs/features/` | 10 GeoTIFFs (B02, B03, B04, B08, B11, B12, NDVI, EVI, SAVI, NDWI). | **Available & Verified** |
| **Sentinel-1 SAR Data** | `data/sentinel1/` | Not currently present in repository. Phase 10 will document SAR fusion as an optional architectural extension rather than forcing artificial data. | **Optional / Documented** |

---

## 5. Recommended Upgrade Strategy

We recommend a phased, mathematically rigorous upgrade plan spanning Phases 2 through 22:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   UPGRADED ML PIPELINE ARCHITECTURE                    │
├────────────────────────────────────────────────────────────────────────┤
│ 1. SPECTRAL EXPANSION (B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12)│
│    - Resample 20m Red-Edge/SWIR to 10m grid (Bilinear)                 │
│ 2. ADVANCED INDICES                                                    │
│    - Vegetation: NDVI, EVI, EVI2, SAVI, MSAVI, OSAVI, GNDVI            │
│    - Red-Edge / Chlorophyll: NDRE_B05, NDRE_B06, NDRE_B07, MTCI, CIre  │
│    - Moisture / Soil: NDWI, NDMI, MSI                                  │
│ 3. SPECTRAL RATIOS & DIFFERENCES                                       │
│    - B08/B04, B08/B05, B08/B06, B08/B07, B08/B11, B08/B12              │
│    - B08 - B04, B08 - B05, B08 - B06, B08 - B07, B08 - B11             │
│ 4. MULTI-TEMPORAL & PHENOLOGY FINGERPRINTING                           │
│    - 10 Robust Temporal Stats: mean, median, min, max, std, range,     │
│      P10, P25, P75, P90                                                │
│    - Phenology: Peak NDVI/NDRE/NDMI/EVI value & date, Growth rate,     │
│      Decline rate, Seasonal amplitude, Integral / Area Under Curve     │
│    - Temporal Derivatives: ΔNDVI, ΔNDRE, ΔNDMI, ΔEVI between dates     │
│ 5. PARCEL ZONAL PERCENTILES & QUALITY FLAGS                            │
│    - Robust percentiles (P10, P25, P50, P75, P90)                      │
│    - Quality flags: GOOD, LIMITED, INSUFFICIENT                        │
│ 6. FEATURE SELECTION & BENCHMARKING                                    │
│    - Feature sets: BASELINE, ADVANCED, TEMPORAL, FULL                  │
│    - Algorithms: Random Forest vs. XGBoost                             │
│    - Spatial Validation: GroupShuffleSplit / StratifiedGroupKFold       │
│ 7. PREDICTION CONFIDENCE & ERROR ANALYSIS                              │
│    - HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE                │
│    - Inspection of misclassified parcels (Other ↔ Paddy, Banana)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Files That Will Be Modified

1. `member1-ml/train_on_member2_data.py`:
   - Upgrade feature pipeline to support advanced feature sets (`BASELINE`, `ADVANCED`, `TEMPORAL`, `FULL`).
   - Add model comparison (Random Forest vs XGBoost).
   - Integrate confidence flagging and metadata output.
2. `member1-ml/pipelines/training_pipeline.py`:
   - Support training with upgraded feature schemas, model selection, and versioned registration.
3. `member1-ml/pipelines/inference_pipeline.py`:
   - Align schema with upgraded model feature set.
4. `member1-ml/classification/parcel_classifier.py`:
   - Include confidence flag (`confidence_tier`), data quality flag, and maintain backward compatibility.
5. `member1-ml/config/config.yaml`:
   - Add configuration for new red-edge bands, advanced spectral indices, phenology parameters, and XGBoost hyperparameters.
6. `member1-ml/main.py`:
   - Update CLI arguments and pipeline execution flow to handle the upgraded feature catalog.

---

## 7. Files That Will Be Created

1. `docs/model_upgrade_analysis.md` (This document — Phase 1 report).
2. `docs/feature_catalog.md` (Phase 3 — Exhaustive catalog of every band, index, ratio, phenology metric, and mathematical formula).
3. `docs/error_analysis.md` (Phase 16 — In-depth breakdown of confusion matrices, misclassified parcels, spectral signatures, and failure modes).
4. `docs/model_upgrade_report.md` (Phase 22 — Final evaluation report with benchmark tables, measured metrics, feature importance, and conclusions).
5. `member1-ml/features/advanced_indices.py`:
   - Pure, robust vector and array computation of all Sentinel-2 vegetation, red-edge, chlorophyll, moisture, and ratio features.
6. `member1-ml/features/phenology.py`:
   - Multi-temporal growth curves, peak detection, growth/decline rate calculations, AUC, and consecutive observation derivatives.
7. `member1-ml/features/feature_selector.py`:
   - Correlation filtering, variance thresholding, and permutation importance for selecting optimal feature subsets.
8. `models/crop_classifier/rf_advanced/` & `models/crop_classifier/xgboost_advanced/`:
   - Versioned directories containing model artifacts, feature lists, training metadata, and validation metrics.
