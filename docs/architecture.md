# System Architecture (2-Member Structure)

## Overview
The VIT MAPATHON project develops an automated satellite-to-dashboard pipeline for agricultural land parcel identification and crop differentiation (Paddy vs. Banana vs. Other) across Ambasamudram and Cheranmahadevi Taluks in Tirunelveli District, Tamil Nadu. The system is engineered and maintained across 2 balanced team members.

## High-Level Architecture Diagram

```
+--------------------------------------------------------------------------+
|                        DATA SOURCE: COPERNICUS HUB                      |
|                  Sentinel-2 Level-2A (Bottom of Atmosphere)              |
+--------------------------------------------------------------------------+
                                     │
                                     ▼
+--------------------------------------------------------------------------+
|       MEMBER 2: GIS, REMOTE SENSING & WEB GIS FRONTEND (ENGINE 1)        |
| - Boundary ingestion: Ambasamudram & Cheranmahadevi Taluks (240.65 sq km)|
| - S2 L2A Scene Filtering (<10% cloud, 4 multi-temporal dates)            |
| - Cloud & shadow masking using Scene Classification Layer (SCL)          |
| - Resampling: 20m bands (B11, B12) to 10m grid aligned with B02,03,04,08 |
| - Index generation: NDVI, EVI, SAVI, NDWI                                |
| - 293 Cadastral parcel delineation & zonal tabular feature extraction    |
| - Projected Coordinate System: EPSG:32643 (UTM Zone 43N)                 |
| - Interactive Web GIS Dashboard: React + Leaflet (member2-gis/frontend)  |
| - Bi-seasonal temporal comparison UI & Agri-AI Chatbot client            |
+--------------------------------------------------------------------------+
                                     │
                    Feature Handoff: ml_training_dataset.csv
                                     ▼
+--------------------------------------------------------------------------+
|          MEMBER 1: AI, MACHINE LEARNING & BACKEND SYSTEMS (ENGINE 2)     |
| - Strict validation: CRS (EPSG:32643), dimensions, bounds, nodata, NaN   |
| - Spatial Leakage Prevention: Stratified GroupSplit on parcel IDs        |
| - Model: Tuned RandomForestClassifier (n_estimators=200, depth=15)       |
| - Dynamic evaluation: Accuracy (88.14%), Macro-F1 (87.06%), Confusion Mat|
| - Parcel-level inference with prediction confidence score                |
| - Crop statistics aggregation (counts & area in sq km & hectares)        |
| - FastAPI REST Backend (member1-ml/backend):                             |
|     * /api/parcels, /api/statistics, /api/metrics                        |
|     * /api/temporal-comparison, /api/chat, /api/reports/download-pdf     |
| - PostgreSQL / PostGIS schema design & data loading (member1-ml/database)|
| - Automated 3-page Agricultural Cadastral PDF Report Generator           |
+--------------------------------------------------------------------------+
                                     │
           REST API Responses & Vector Layers (EPSG:4326 GeoJSON)
                                     ▼
+--------------------------------------------------------------------------+
|           INTEGRATED SYSTEM EXECUTION: BROWSER / DECISION MAKERS         |
| - Color-coded parcel vectors (Paddy = Green, Banana = Gold, Other = Gray)|
| - Live crop filters, confidence thresholds, and parcel inspection        |
| - Bi-seasonal multi-temporal comparison & agronomic advisory             |
| - Instant PDF report export & standalone interactive Folium map          |
+--------------------------------------------------------------------------+
```

## Coordinate Reference System Standard
- **Project Standard CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- All rasters and vector calculations use this metric projection so that area calculations (in square meters / square kilometers) are geometrically accurate and free from spherical distortion.
- GeoJSON outputs for web visualization will have geometries in standard WGS 84 (`EPSG:4326` / lat-lon) for Leaflet compatibility, while maintaining precise area properties (`area_sq_km`) computed in `EPSG:32643`.

## Target Classes
1. **Paddy**: Wetland rice cultivation, characterized by inundation (high NDWI / low initial NDVI) followed by rapid vegetative growth (steep NDVI increase).
2. **Banana**: Perennial horticulture crop with large leaf area index, maintaining consistently high NDVI and EVI throughout multiple seasons without drastic harvesting drops.
3. **Other**: Fallow land, scrubland, built-up areas, water bodies, and other seasonal vegetation.
