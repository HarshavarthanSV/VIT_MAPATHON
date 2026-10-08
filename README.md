# VIT MAPATHON — Agricultural Land Parcel and Crop Identification

## Problem Statement 1: Agricultural Land Parcel and Crop Identification
Differentiate agricultural land parcels and identify/differentiate **Paddy** and **Banana** cultivation in **Tirunelveli District**, covering:
- **Ambasamudram Taluk**
- **Cheranmahadevi Taluk**

Using openly available satellite imagery (**Sentinel-2 Level-2A (L2A)**).
- **Minimum Study Area**: $\ge 20 \text{ km}^2$
- **Target Classes**: `Paddy`, `Banana`, `Other`
- **Primary Model**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)

---

## 3-Member Collaborative Architecture

This project is structured as **one coherent end-to-end system** across three dedicated modules:

```
[ Sentinel-2 L2A Imagery ]
            ↓
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 2 — GIS / Remote Sensing Engineer                   │
│  - AOI Definition (Ambasamudram & Cheranmahadevi >= 20 km²) │
│  - Cloud/Shadow Masking & Band Resampling to 10m            │
│  - Bands (B02, B03, B04, B08, B11, B12)                     │
│  - Spectral Indices (NDVI, EVI, SAVI, NDWI)                 │
│  - Multi-temporal Stacks & Parcel Boundaries                │
│  - Ground Truth Training Polygons (Paddy, Banana, Other)    │
└─────────────────────────────────────────────────────────────┘
            ↓ (Data Contract: GeoTIFF rasters + GeoJSON polygons)
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 1 — ML / AI Engineer                                │
│  - Input Data Validation (CRS EPSG:32643, alignment, NaN)   │
│  - Spatial-aware Splitting (GroupShuffleSplit on parcels)   │
│  - Feature Extraction (Spectral & Multi-temporal)           │
│  - Random Forest Crop Classifier Training & Tuning          │
│  - Dynamic Metrics (Accuracy, Precision, Recall, F1)        │
│  - Confusion Matrix & Feature Importance Calculation        │
│  - Parcel Classification with Model Confidence              │
│  - Outputs: classified_parcels.geojson, crop_statistics.json│
│             model_metrics.json, crop_classifier.joblib      │
└─────────────────────────────────────────────────────────────┘
            ↓ (Handoff Contract: classified_parcels.geojson + statistics)
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 3 — Full Stack / GIS Application Engineer           │
│  - PostGIS Spatial Database Integration                     │
│  - FastAPI REST Endpoints (/parcels, /statistics, /metrics) │
│  - React + Leaflet Interactive Agricultural GIS Dashboard   │
│  - Parcel Boundary Visualization, Crop Filters & Stats      │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
VIT_MAPATHON/
├── .gitignore
├── requirements.txt
├── README.md
├── docs/
│   ├── architecture.md
│   ├── data_flow.md
│   └── team_workflow.md
├── member2-gis/                    # Member 2: GIS / Remote Sensing
│   ├── README.md
│   ├── inputs/                     # Raw satellite scene metadata & AOI
│   └── outputs/                    # Member 2 handoff to Member 1
│       ├── features/               # Co-registered GeoTIFF rasters (10m)
│       ├── temporal/               # Multi-temporal date stacks
│       ├── parcels/                # Agricultural parcel boundaries
│       └── labels/                 # Training polygons with ground truth
├── member1-ml/                     # Member 1: ML / AI Engineering
│   ├── config/
│   │   └── config.yaml             # Data-driven pipeline configuration
│   ├── preprocessing/              # Validation, loading & dataset builder
│   │   ├── feature_loader.py
│   │   ├── label_loader.py
│   │   ├── dataset_builder.py
│   │   └── validation.py
│   ├── classification/             # Model training, prediction & parcel classification
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── parcel_classifier.py
│   ├── evaluation/                 # Metrics, confusion matrix, feature importance
│   │   ├── metrics.py
│   │   ├── confusion_matrix.py
│   │   └── feature_importance.py
│   ├── models/                     # Trained Random Forest artifact (.joblib)
│   ├── outputs/                    # Handoff artifacts for Member 3
│   │   ├── classified_parcels.geojson
│   │   ├── crop_statistics.json
│   │   ├── model_metrics.json
│   │   └── feature_importance.json
│   ├── docs/                       # Member 1 contracts & guides
│   │   ├── data_contract.md        # Member 2 -> Member 1 contract
│   │   ├── ml_pipeline.md          # Pipeline implementation details
│   │   └── member3_handoff.md      # Member 1 -> Member 3 contract
│   ├── tests/                      # Automated unit tests
│   └── main.py                     # Member 1 pipeline entrypoint
└── member3-fullstack/              # Member 3: Full Stack GIS Dashboard
    ├── README.md
    ├── backend/                    # FastAPI + PostGIS
    ├── frontend/                   # React + Leaflet Web GIS Dashboard
    └── docs/
```

---

## Git Branching Model

- `main`: Release and integration branch.
- `member1-ml`: Active development branch for Member 1 (ML / AI).
- `member2-gis`: Active development branch for Member 2 (GIS / Remote Sensing).
- `member3-fullstack`: Active development branch for Member 3 (Full Stack / Web GIS).

---

## Running Member 1 Pipeline

1. Ensure requirements are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Run automated tests:
   ```bash
   pytest member1-ml/tests/
   ```
3. Run the ML pipeline with real Member 2 data:
   ```bash
   python member1-ml/main.py --config member1-ml/config/config.yaml
   ```
