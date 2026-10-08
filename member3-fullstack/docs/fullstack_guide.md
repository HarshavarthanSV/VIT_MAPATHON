# Member 3 — Full Stack & Web GIS Guide

## 1. Executive Summary & Problem Context

**VIT MAPATHON Problem Statement 1**: Agricultural Land Parcel and Crop Identification in Tirunelveli District, covering **Ambasamudram Taluk** and **Cheranmahadevi Taluk** (Study Area $\ge 20 \text{ km}^2$, centered around Lat 8.70° N, Lon 77.49° E).

As **Member 3 (Full Stack / GIS Application Engineer)**, this module provides the complete geospatial database, high-performance REST API, and interactive Web GIS dashboard for ingesting, querying, and visualizing satellite-derived crop classifications (**Paddy**, **Banana**, **Other**).

---

## 2. Architecture & Data Flow

```
Member 1 ML Outputs
  ├── classified_parcels.geojson (EPSG:4326)
  ├── crop_statistics.json
  ├── model_metrics.json
  └── feature_importance.json & Plots
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  MEMBER 3 SPATIAL DATA LAYER                           │
│  - PostGIS Spatial Database (EPSG:4326 GIST Indexes)   │
│  - import_parcels.py (Batch Upsert & Validation)       │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  MEMBER 3 FASTAPI BACKEND SERVICE                      │
│  - GET /api/parcels (Crop & Confidence Filters)        │
│  - GET /api/parcels/{id} (Detailed Parcel Inspector)   │
│  - GET /api/statistics (Dynamic Area Aggregations)     │
│  - GET /api/metrics (Random Forest Performance)        │
│  - GET /api/health (System Health & DB Mode)           │
│  * Automatic PostGIS ↔ GeoJSON Fallback Engine        │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  MEMBER 3 REACT + LEAFLET GIS DASHBOARD                │
│  - Dual Basemap (Esri Satellite & OSM Standard)        │
│  - Crop-Themed Styling (Paddy/Green, Banana/Amber, etc)│
│  - Interactive Parcel Click Popups with Probabilities  │
│  - Live Area Breakdown & KPI Analytics Cards           │
│  - ML Evaluation Modal with Confusion Matrix Heatmap   │
└────────────────────────────────────────────────────────┘
```

---

## 3. Directory Layout

```
member3-fullstack/
├── database/
│   ├── schema.sql                   # PostGIS table definitions & spatial indexes
│   └── import_parcels.py            # Ingests classified_parcels.geojson into PostGIS
├── backend/
│   ├── main.py                      # FastAPI application entrypoint
│   ├── database.py                  # Database connection pool & fallback manager
│   ├── routers/
│   │   ├── parcels.py               # /api/parcels endpoints
│   │   └── statistics.py            # /api/statistics & /api/metrics endpoints
│   └── requirements.txt             # Backend python dependencies
├── frontend/                        # React + Leaflet Web Application
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.jsx          # Leaflet GIS map with parcel polygons
│   │   │   ├── ParcelPopup.jsx      # Interactive popup on parcel click
│   │   │   ├── FilterPanel.jsx      # Checkboxes to filter Paddy / Banana / Other
│   │   │   ├── StatisticsCard.jsx   # Metrics cards & area distribution
│   │   │   └── MetricsModal.jsx     # ML model accuracy & confusion matrix view
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   └── dist/                        # Production build bundle
├── inputs/                          # Offline dev & demonstration artifacts
│   ├── classified_parcels.geojson
│   ├── crop_statistics.json
│   ├── model_metrics.json
│   ├── feature_importance.json
│   ├── confusion_matrix.png
│   └── feature_importance.png
└── docs/
    └── fullstack_guide.md           # This guide
```

---

## 4. PostGIS Spatial Database Setup

### 4.1 Schema Definition (`database/schema.sql`)
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

### 4.2 Ingesting Parcels (`database/import_parcels.py`)
To ingest Member 1's classified parcel polygons into PostGIS:

```bash
# Dry run validation
python member3-fullstack/database/import_parcels.py --dry-run

# Ingest into local PostGIS
python member3-fullstack/database/import_parcels.py --host localhost --port 5432 --dbname postgres --user postgres --password postgres
```

---

## 5. Running the FastAPI Backend

### 5.1 Installation
```bash
pip install -r member3-fullstack/backend/requirements.txt
```

### 5.2 Start Server
```bash
cd member3-fullstack/backend
uvicorn main:app --reload --port 8000
```
Interactive OpenAPI documentation is live at: `http://localhost:8000/docs`

### 5.3 REST Endpoints
| Endpoint | Method | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/parcels` | GET | `crop`, `min_confidence`, `limit` | Returns GeoJSON FeatureCollection |
| `/api/parcels/{parcel_id}` | GET | None | Specific parcel details & geometry |
| `/api/statistics` | GET | None | Aggregated area, counts, & percentages |
| `/api/metrics` | GET | None | ML evaluation (Accuracy, F1, Precision) |
| `/api/feature-importance` | GET | None | Ranked spectral band importance |
| `/api/health` | GET | None | Backend health and PostGIS status |

---

## 6. Running the React + Leaflet Frontend

### 6.1 Installation
```bash
cd member3-fullstack/frontend
npm install
```

### 6.2 Start Development Server
```bash
npm run dev
```
Open browser at: `http://localhost:5173`

### 6.3 Production Build
```bash
npm run build
```

---

## 7. Zero-Fake-Data & Offline Fallback Architecture

To honor the **No Fake Data Rule** while ensuring seamless local development:
1. The backend automatically resolves deliverables by checking:
   - Priority 1: `member1-ml/outputs/`
   - Priority 2: `member3-fullstack/inputs/`
2. If PostGIS is active with ingested parcels, queries use PostGIS `ST_AsGeoJSON` and spatial SQL aggregations.
3. If PostGIS is offline or during standalone frontend dev, the backend serves the validated GeoJSON deliverable with full dynamic filtering.
4. All parcel coordinates are located strictly within the study area of Ambasamudram & Cheranmahadevi Taluks ($\ge 20 \text{ km}^2$), and all area calculations are geometrically validated in metric UTM Zone 43N (`EPSG:32643`).
