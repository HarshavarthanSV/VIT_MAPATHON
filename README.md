# VIT MAPATHON — Agricultural Land Parcel and Crop Identification

## Problem Statement 1: Agricultural Land Parcel and Crop Identification
Automated identification and differentiation of agricultural land parcels, **Paddy** (rice), and **Banana** plantations in **Tirunelveli District** (covering **Ambasamudram Taluk** and **Cheranmahadevi Taluk**), Tamil Nadu, India, using openly available Sentinel-2 Level-2A surface reflectance satellite imagery.
- **Minimum Study Area**: $\ge 20 \text{ km}^2$ (Actual study area covered: $240.65 \text{ km}^2$)
- **Target Classes**: `Paddy`, `Banana`, `Other`
- **Primary Model**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`, 88.14% holdout test accuracy, 83.78% 5-fold CV)
- **Team Size**: 2 Members (Balanced Full-Stack AI & Geospatial Division)

---

## 2-Member Collaborative Architecture

```
[ Sentinel-2 L2A Imagery (4 Multi-temporal Dates) ]
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 2 — GIS, Remote Sensing & Web GIS Frontend         │
│  - AOI Definition: Ambasamudram & Cheranmahadevi (240.65km²)│
│  - SCL Cloud & Shadow Masking (>99.9% valid pixels)         │
│  - 20m -> 10m Resampling in EPSG:32643 (UTM Zone 43N)       │
│  - 60-Layer Temporal Feature Stack (Bands & Indices)        │
│  - 293 Cadastral Parcels Delineation & Zonal Extraction     │
│  - React + Leaflet Web GIS Dashboard (member2-gis/frontend) │
│  - Bi-seasonal temporal comparison UI & Agri-AI Chatbot UI  │
│  - Deliverables: ml_training_dataset.csv & Interactive UI   │
└─────────────────────────────────────────────────────────────┘
                         ↕ (Bi-directional Data & API Contract)
┌─────────────────────────────────────────────────────────────┐
│  MEMBER 1 — AI / Machine Learning & Backend Systems        │
│  - Train Tuned Random Forest Classifier (n_estimators=200)  │
│  - Stratified & Group Cross-Validation (Zero Data Leakage)  │
│  - Dynamic Metrics: Accuracy (88.14%), F1-Score (87.06%)    │
│  - Feature Importance Rankings & Confusion Matrix Heatmap   │
│  - Parcel Inference & Spatial GeoJSON Output Generation    │
│  - FastAPI REST API (member1-ml/backend: /parcels, /stats)  │
│  - Automated Agricultural PDF Report Generator & AI Advisory│
│  - PostGIS Database Schema & Ingestion Pipelines            │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 Team Roles & Directory Ownership

| Member | Focus Area | Primary Directory | Working Branch | Key Responsibilities |
|---|---|---|---|---|
| **Member 1** | AI / Machine Learning & Backend Systems | `member1-ml/` | `member1-ml` | Random Forest training, evaluation metrics, parcel inference, `classified_parcels.geojson`, FastAPI REST API backend (`member1-ml/backend/`), PostGIS spatial database schema, automated PDF report generation, and automated backend test suite. |
| **Member 2** | GIS / Remote Sensing & Web GIS Frontend | `member2-gis/`, `data/` | `member2-gis` | S2 L2A preprocessing, cloud masking, 60-layer temporal stack, parcel extraction, `ml_training_dataset.csv`, React + Leaflet GIS frontend dashboard (`member2-gis/frontend/`), temporal analytics UI, and cartographic verification maps. |

---

## 🚀 Running Member 1: ML & Backend Pipeline

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run full automated test suite (ML + Backend, 30 tests):
   ```bash
   pytest member1-ml/tests/ -v
   ```
3. Run the ML model training & evaluation pipeline:
   ```bash
   python member1-ml/train_on_member2_data.py
   ```
4. Start the FastAPI backend service:
   ```bash
   uvicorn main:app --app-dir member1-ml/backend --host 127.0.0.1 --port 8000 --reload
   ```
   API interactive docs available at: `http://localhost:8000/docs`

---

## 🗺️ Running Member 2: GIS & Web Frontend Dashboard

1. Launch the React + Leaflet Web GIS frontend:
   ```bash
   cd member2-gis/frontend
   npm run dev
   ```
   Open dashboard at: `http://localhost:5173`

2. Run GIS validation and taluk acreage summary:
   ```bash
   python postprocessing/validate_classified_parcels.py
   python postprocessing/calculate_taluk_acreage.py
   ```

3. Generate publication-quality 300 DPI classification map:
   ```bash
   python postprocessing/generate_classification_map.py
   ```
   Outputs generated in:
   - `results/taluk_crop_acreage_summary.csv`
   - `results/crop_statistics.csv`
   - `results/gis_validation_report.txt`
   - `results/validation_maps/final_crop_classification_map.png`
