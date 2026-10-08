# Web GIS Platform Guide (2-Member Architecture)

## 1. Executive Summary & Problem Context

**VIT MAPATHON Problem Statement 1**: Agricultural Land Parcel and Crop Identification in Tirunelveli District, covering **Ambasamudram Taluk** and **Cheranmahadevi Taluk** (Study Area $\ge 20 \text{ km}^2$, total $240.65\text{ km}^2$, centered around Lat 8.70° N, Lon 77.49° E).

In the **2-Member Architecture**, the Web GIS platform is divided between:
- **Member 1 (AI / Machine Learning & Backend Systems)**: PostGIS database, FastAPI REST backend services, automated PDF reporting, and Agri-AI advisory engine (`member1-ml/backend/` & `member1-ml/database/`).
- **Member 2 (GIS, Remote Sensing & Web GIS Frontend)**: Cadastral parcel digitizing, Sentinel-2 spectral indices, and the interactive React + Leaflet Web GIS dashboard (`member2-gis/frontend/`).

---

## 2. Architecture & Data Flow

```
Member 1 ML Outputs (member1-ml/outputs/)
  ├── classified_parcels.geojson (EPSG:4326)
  ├── crop_statistics.json
  ├── model_metrics.json
  └── feature_importance.json & Plots
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  MEMBER 1 SPATIAL DATA & BACKEND SERVICE               │
│  - PostGIS Spatial Database (member1-ml/database)      │
│  - FastAPI REST API (member1-ml/backend)               │
│    * GET /api/parcels (Crop & Confidence Filters)      │
│    * GET /api/statistics (Dynamic Area Aggregations)   │
│    * GET /api/metrics (Random Forest Performance)      │
│    * GET /api/temporal-comparison (Bi-seasonal stats)  │
│    * POST /api/chat (Agronomic Advisory AI Chatbot)    │
│    * GET /api/reports/download-pdf (3-Page Report)     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  MEMBER 2 REACT + LEAFLET GIS DASHBOARD                │
│  (member2-gis/frontend)                                │
│  - Dual Basemap (Esri Satellite & OSM Standard)        │
│  - Crop-Themed Styling (Paddy/Green, Banana/Amber, etc)│
│  - Interactive Parcel Click Popups with Probabilities  │
│  - Live Area Breakdown & KPI Analytics Cards           │
│  - ML Evaluation Modal with Confusion Matrix Heatmap   │
│  - Bi-seasonal Temporal Comparison Modal               │
│  - Agri-AI Floating Chatbot Assistant                  │
└────────────────────────────────────────────────────────┘
```

---

## 3. Directory Layout

```
VIT/
├── member1-ml/
│   ├── backend/                     # FastAPI Backend (Member 1)
│   │   ├── main.py                  # Application entrypoint & routes
│   │   ├── database.py              # Database pool & artifact resolver
│   │   ├── reports/                 # Automated PDF report generator
│   │   └── routers/                 # Endpoints (parcels, stats, layers, analysis)
│   ├── database/                    # Spatial Database (Member 1)
│   │   ├── schema.sql               # PostGIS table definitions & spatial indexes
│   │   └── import_parcels.py        # Ingests classified_parcels.geojson into PostGIS
│   ├── tests/                       # Automated test suite (ML + Backend, 30 tests)
│   └── train_on_member2_data.py     # Primary Random Forest ML pipeline
├── member2-gis/
│   ├── frontend/                    # React + Leaflet Web Application (Member 2)
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   ├── index.html
│   │   └── src/                     # React components, UI styling, and Leaflet maps
│   ├── inputs/                      # AOI & Vector administrative layers
│   └── outputs/                     # Extracted features & temporal stacks
```

---

## 4. PostGIS Spatial Database Setup

### 4.1 Schema Definition (`member1-ml/database/schema.sql`)
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS agricultural_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    predicted_crop VARCHAR(30) NOT NULL,
    confidence FLOAT NOT NULL,
    area_sq_km FLOAT NOT NULL,
    area_ha FLOAT NOT NULL,
    prob_paddy FLOAT,
    prob_banana FLOAT,
    prob_other FLOAT,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parcels_geom ON agricultural_parcels USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_parcels_crop ON agricultural_parcels (predicted_crop);
CREATE INDEX IF NOT EXISTS idx_parcels_confidence ON agricultural_parcels (confidence);
```

### 4.2 Ingesting Parcels (`member1-ml/database/import_parcels.py`)
```bash
# Dry run validation
python member1-ml/database/import_parcels.py --dry-run

# Ingest into local PostGIS
python member1-ml/database/import_parcels.py --host localhost --port 5432 --dbname postgres --user postgres --password postgres
```

---

## 5. Running the FastAPI Backend (Member 1)

```bash
uvicorn main:app --app-dir member1-ml/backend --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation is live at: `http://localhost:8000/docs`

---

## 6. Running the React + Leaflet Frontend (Member 2)

```bash
cd member2-gis/frontend
npm run dev
```
Open browser at: `http://localhost:5173`
Production build: `npm run build`
