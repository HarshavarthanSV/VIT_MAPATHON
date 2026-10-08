# Member 1 — AI, Machine Learning & Backend Systems Module

## Overview
Member 1 is responsible for the complete Machine Learning and Backend Systems lifecycle in the 2-member project architecture:
1. **Machine Learning Pipeline**: Data validation, spatial leakage prevention (group-stratified splitting), Random Forest model training, multi-temporal feature importance extraction, parcel inference, and evaluation metrics.
2. **Backend Services & Database**: FastAPI REST API service, PostgreSQL / PostGIS spatial database schema and ingestion, automated agricultural PDF report generation, and the Agri-AI advisory chatbot backend.

---

## Directory Structure
```
member1-ml/
├── backend/                  # FastAPI REST API Backend
│   ├── main.py               # Application entrypoint & routes
│   ├── database.py           # Database connection & artifact resolver
│   ├── requirements.txt      # Backend Python dependencies
│   ├── reports/              # Automated PDF report generator
│   └── routers/              # API endpoints (parcels, stats, layers, analysis)
├── database/                 # Spatial Database
│   ├── schema.sql            # PostGIS table definitions & spatial indexes
│   └── import_parcels.py     # GeoJSON ingestion script for PostGIS
├── classification/           # Model classification logic
├── config/                   # Model and pipeline YAML configurations
├── docs/                     # ML & Backend documentation
├── evaluation/               # Model evaluation scripts & metrics
├── models/                   # Saved model artifacts (crop_classifier.joblib)
├── outputs/                  # Exported deliverables (classified_parcels.geojson, etc.)
├── preprocessing/            # ML feature scaling & imputation
├── tests/                    # Automated test suite (ML + Backend, 30 tests)
└── train_on_member2_data.py  # Primary Random Forest training pipeline
```

---

## Model Performance
- **Holdout Test Accuracy**: **88.14%**
- **5-Fold Cross-Validation Accuracy**: **83.78%**
- **Macro F1-Score**: **87.06%**
- **Features Extracted**: 240 features across 4 Sentinel-2 acquisition dates.
- **Parcels Classified**: 293 agricultural parcels across Ambasamudram & Cheranmahadevi Taluks.

---

## Running the Pipelines
1. **Train Model**:
   ```bash
   python member1-ml/train_on_member2_data.py
   ```
2. **Run Test Suite**:
   ```bash
   pytest member1-ml/tests/ -v
   ```
3. **Start FastAPI Backend**:
   ```bash
   uvicorn main:app --app-dir member1-ml/backend --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive OpenAPI docs: `http://localhost:8000/docs`
