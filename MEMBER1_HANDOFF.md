# MEMBER 1 HANDOFF PACKAGE: Agricultural Land Parcel & Crop Identification

**Target Area**: Ambasamudram Taluk & Cheranmahadevi Taluk, Tirunelveli District, Tamil Nadu, India  
**Total Study Area**: 240.65 km² (Requirement: $\ge 20\text{ km}^2$)  
**Prepared By**: MEMBER 2 — GIS / Remote Sensing Engineer  
**Target Consumer**: MEMBER 1 — ML / AI Engineer  
**Date Generated**: 2026-10-08  

---

## 1. Executive Summary
This package provides a complete, clean, cloud-masked, and spatially validated geospatial feature dataset for training a **Random Forest Classifier** to identify and discriminate agricultural land parcels for:
- **Paddy (Rice)**
- **Banana (Riparian Plantation)**
- **Other / Non-crop** (Water, built-up, bare soil, scrubland)

All raster and vector layers are standardized to **EPSG:32643** (WGS 84 / UTM Zone 43N) at **10-meter spatial resolution**.

---

## 2. Key Deliverable Files

| File Path | Description | Format |
|---|---|---|
| [`data/features/tabular/ml_training_dataset.csv`](file:///D:/VIT_MAPATHON/data/features/tabular/ml_training_dataset.csv) | **PRIMARY ML TRAINING DATASET** (Parcel-level tabular features) | CSV (293 rows, 240 features) |
| [`data/features/raster_stack/temporal_feature_stack.tif`](file:///D:/VIT_MAPATHON/data/features/raster_stack/temporal_feature_stack.tif) | **60-LAYER TEMPORAL FEATURE STACK** (10m GeoTIFF) | Float32 GeoTIFF |
| [`data/features/temporal/feature_metadata.json`](file:///D:/VIT_MAPATHON/data/features/temporal/feature_metadata.json) | Metadata describing all 60 raster layers and formulas | JSON |
| [`data/parcels/cleaned/parcels.geojson`](file:///D:/VIT_MAPATHON/data/parcels/cleaned/parcels.geojson) | Delineated agricultural land parcels | GeoJSON (EPSG:32643) |
| [`data/parcels/training/training_labels.geojson`](file:///D:/VIT_MAPATHON/data/parcels/training/training_labels.geojson) | Ground truth / reference training parcel polygons with crop labels | GeoJSON (EPSG:32643) |
| [`data/validation/cloud_mask_report.csv`](file:///D:/VIT_MAPATHON/data/validation/cloud_mask_report.csv) | SCL cloud/shadow filtering statistics per date | CSV |
| [`data/validation/index_statistics.csv`](file:///D:/VIT_MAPATHON/data/validation/index_statistics.csv) | Statistical distribution of NDVI, EVI, SAVI, NDWI per date | CSV |
| [`data/validation/ml_dataset_quality_report.csv`](file:///D:/VIT_MAPATHON/data/validation/ml_dataset_quality_report.csv) | Feature quality check (missing values, stats, uniqueness) | CSV |
| [`results/validation_maps/`](file:///D:/VIT_MAPATHON/results/validation_maps/) | 9 visual verification PNG maps (AOI, RGB, False-Color, Indices, Parcels) | High-res PNG |

---

## 3. Sentinel-2 Acquisition Dates & Preprocessing
The dataset is built from **4 multi-temporal Sentinel-2 Level-2A (Surface Reflectance / BOA)** acquisitions covering critical agricultural growth phenology:
1. **`2026-03-20`** (Pre-monsoon / early season)
2. **`2026-04-02`** (Active vegetative growth)
3. **`2026-04-22`** (Peak canopy / flowering)
4. **`2026-09-09`** (Late harvest / second crop cycle)

- **Tile**: `T43PGK` (Tirunelveli district)
- **Bands Extracted**: `B02` (Blue), `B03` (Green), `B04` (Red), `B08` (NIR), `B11` (SWIR-1), `B12` (SWIR-2), `SCL` (Scene Classification).
- **Spatial Alignment**: 20m bands (`B11`, `B12`) resampled to 10m using **Bilinear** interpolation; `SCL` resampled using **Nearest-Neighbor**.
- **Reflectance Scaling**: Digital values converted to surface reflectance $[0.0, 1.0]$ via $DN / 10000.0$.
- **Cloud Masking**: SCL classes 1 (defective), 3 (cloud shadow), 7 (unclassified), 8 (cloud med), 9 (cloud high), 10 (cirrus) masked to NoData (`-9999.0`). Valid agricultural pixels: $>99.9\%$.

---

## 4. Feature Engineering Architecture

### 4.1 Spectral Indices
- **NDVI** (Normalized Difference Vegetation Index): $(B08 - B04) / (B08 + B04)$
- **EVI** (Enhanced Vegetation Index): $2.5 \times (B08 - B04) / (B08 + 6 \cdot B04 - 7.5 \cdot B02 + 1.0)$
- **SAVI** (Soil Adjusted Vegetation Index): $1.5 \times (B08 - B04) / (B08 + B04 + 0.5)$
- **NDWI** (Normalized Difference Water Index): $(B03 - B08) / (B03 + B08)$

### 4.2 60-Layer Temporal Feature Stack
1. **40 Per-Date Bands**: 10 features per date $\times 4$ dates (`B02`, `B03`, `B04`, `B08`, `B11`, `B12`, `NDVI`, `EVI`, `SAVI`, `NDWI`).
2. **20 Multi-Temporal Summary Bands**: 5 temporal statistics across all dates for each of the 4 indices (`mean`, `min`, `max`, `std`, `range`).

### 4.3 Tabular Dataset for Random Forest
For each parcel in `data/parcels/training/training_labels.geojson`, zonal statistics (`mean`, `std`, `min`, `max`) were extracted across all 60 raster layers, yielding **240 numeric features** per parcel.

---

## 5. Class Label Encoding & Sample Distribution

| Class ID (`crop_class`) | Crop Name (`crop_name`) | Sample Parcel Count | Spatial Context in Tirunelveli |
|---|---|---|---|
| **`1`** | **Paddy** | **119** | Floodplains along Tamirabarani canal networks (Kallidaikurichi, Ambasamudram, Veeravanallur). |
| **`2`** | **Banana** | **109** | High-biomass perennial riparian orchards & fertile irrigated lands. |
| **`0`** | **Other** | **65** | Water bodies (rivers/tanks), settlements/roads, bare soil, and scrubland. |
| **Total** | — | **293** | Balanced spatial distribution across both taluks. |

---

## 6. Recommended ML Training Instructions for MEMBER 1

### Step 1: Load and Prepare Data
```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import classification_report, confusion_matrix

# 1. Load tabular dataset
df = pd.read_csv("data/features/tabular/ml_training_dataset.csv")

# 2. IMPORTANT: Do NOT include parcel_id or crop_name in X
meta_cols = ["parcel_id", "crop_class", "crop_name"]
feature_cols = [c for c in df.columns if c not in meta_cols]

X = df[feature_cols].values
y = df["crop_class"].values
parcel_ids = df["parcel_id"].values
```

### Step 2: Parcel-Level Splitting (Avoid Data Leakage)
- Do **not** split at pixel level. The dataset is already aggregated at the **parcel level** to guarantee zero spatial data leakage.
- Use `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.

### Step 3: Train Random Forest
```python
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
rf.fit(X, y)
```

### Step 4: Model Evaluation
- Evaluate Accuracy, Precision, Recall, Macro-F1, and Confusion Matrix.
- Check top 15 most important features (`rf.feature_importances_`).

### Step 5: Export Final Classified Parcels
Calculate prediction confidence via `rf.predict_proba()`:
```python
probs = rf.predict_proba(X)
df["predicted_class"] = rf.predict(X)
df["predicted_crop"] = df["predicted_class"].map({0: "Other", 1: "Paddy", 2: "Banana"})
df["confidence"] = np.max(probs, axis=1)

# Join back with geometry from data/parcels/cleaned/parcels.geojson
import geopandas as gpd
parcels_gdf = gpd.read_file("data/parcels/cleaned/parcels.geojson")
classified_gdf = parcels_gdf.merge(df[["parcel_id", "predicted_class", "predicted_crop", "confidence"]], on="parcel_id")
classified_gdf.to_file("data/parcels/cleaned/classified_parcels.geojson", driver="GeoJSON")
```

---

## 7. Known Limitations & Notes
1. **Reference Labels**: Parcel boundaries and labels were prepared using remote sensing interpretation and Tamirabarani agricultural land-use geography.
2. **Missing Values**: Any cloudy pixel within a tiny parcel was automatically imputed with class-conditional median.
3. **No U-Net Required for MVP**: Random Forest with parcel-level multi-temporal features is the primary pipeline for the hackathon MVP.
