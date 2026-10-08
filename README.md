# VIT MAPATHON — Agricultural Land Parcel and Crop Identification

## Problem Statement 1: Agricultural Land Parcel and Crop Identification
Automated identification and differentiation of agricultural land parcels, **Paddy** (rice), and **Banana** plantations in **Tirunelveli District** (covering **Ambasamudram Taluk** and **Cheranmahadevi Taluk**), Tamil Nadu, India, using openly available Sentinel-2 Level-2A surface reflectance satellite imagery.
- **Minimum Study Area**: $\ge 20 \text{ km}^2$ (Actual study area covered: $240.65 \text{ km}^2$)
- **Target Classes**: `Paddy`, `Banana`, `Other`
- **Primary Model**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)

---

## 3-Member Collaborative Architecture

```
[ Sentinel-2 L2A Imagery (4 Multi-temporal Dates) ]
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 2 — GIS / Remote Sensing Engineer                   │
│  - AOI Definition: Ambasamudram & Cheranmahadevi (240.65km²)│
│  - SCL Cloud & Shadow Masking (>99.9% valid pixels)         │
│  - 20m -> 10m Resampling in EPSG:32643 (UTM Zone 43N)       │
│  - 60-Layer Temporal Feature Stack (Bands & Indices)        │
│  - 293 Clean Agricultural Parcels with 240 Tabular Features │
│  - Deliverables: data/features/tabular/ml_training_dataset.csv│
└─────────────────────────────────────────────────────────────┘
                         ↓ (Handoff: MEMBER1_HANDOFF.md)
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 1 — ML / AI Engineer                                │
│  - Train Random Forest Classifier (n_estimators=200)        │
│  - Stratified & Group Cross-Validation (Zero Data Leakage)  │
│  - Dynamic Metrics: Accuracy, Precision, Recall, Macro-F1   │
│  - Feature Importance Analysis (MDI rankings)               │
│  - Parcel-Level Inference with Confidence Scores            │
│  - Outputs: classified_parcels.geojson, crop_statistics.json│
└─────────────────────────────────────────────────────────────┘
                         ↓ (Handoff: member3_handoff.md)
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 3 — Full Stack / GIS Application Engineer           │
│  - PostgreSQL + PostGIS Spatial Database Schema             │
│  - FastAPI REST Endpoints (/api/parcels, /api/statistics)   │
│  - React + TypeScript + React-Leaflet Map Dashboard         │
│  - Parcel Popups, Crop Filters (Paddy/Banana/Other) & Charts│
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 Team Roles & Directory Ownership

| Member | Primary Directory | Branch | Key Responsibilities |
|---|---|---|---|
| **Member 1** (ML / AI) | `member1-ml/` | `member1-ml` | Random Forest training, evaluation metrics, parcel inference, `classified_parcels.geojson`, and `crop_statistics.json`. |
| **Member 2** (GIS) | `preprocessing/`, `data/` | `member2-gis` | S2 L2A preprocessing, cloud masking, 60-layer temporal stack, parcel extraction, and `ml_training_dataset.csv`. |
| **Member 3** (Full Stack) | `member3-fullstack/` | `member3-fullstack` | PostGIS database, FastAPI backend, React + Leaflet frontend GIS dashboard. |

---

## 🚀 Running Member 1 ML Pipeline

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run automated test suite:
   ```bash
   pytest member1-ml/tests/ -v
   ```
3. Run the ML model on Member 2's dataset:
   ```bash
   python member1-ml/main.py
   ```

---

## 🗺️ Running Member 2 GIS Postprocessing & Validation Pipeline

1. Run spatial integrity validation and crop statistics:
   ```bash
   python postprocessing/validate_classified_parcels.py
   ```
2. Run taluk-level crop acreage summary (Ambasamudram vs Cheranmahadevi):
   ```bash
   python postprocessing/calculate_taluk_acreage.py
   ```
3. Generate publication-quality 300 DPI classification map:
   ```bash
   python postprocessing/generate_classification_map.py
   ```
4. Output results generated in:
   - `results/taluk_crop_acreage_summary.csv`
   - `results/crop_statistics.csv`
   - `results/gis_validation_report.txt`
   - `results/validation_maps/final_crop_classification_map.png`

