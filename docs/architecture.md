# System Architecture

## Overview
The VIT MAPATHON project develops an automated satellite-to-dashboard pipeline for agricultural land parcel identification and crop differentiation (Paddy vs. Banana vs. Other) across Ambasamudram and Cheranmahadevi Taluks in Tirunelveli District, Tamil Nadu.

## High-Level Architecture Diagram

```
+--------------------------------------------------------------------------+
|                        DATA SOURCE: COPERNICUS HUB                      |
|                  Sentinel-2 Level-2A (Bottom of Atmosphere)              |
+--------------------------------------------------------------------------+
                                     │
                                     ▼
+--------------------------------------------------------------------------+
|                  MEMBER 2: GIS & REMOTE SENSING ENGINE                   |
| - Boundary ingestion: Ambasamudram & Cheranmahadevi Taluks (>= 20 sq km) |
| - S2 L2A Scene Filtering (<10% cloud, multi-temporal dates)              |
| - Cloud & shadow masking using Scene Classification Layer (SCL)          |
| - Resampling: 20m bands (B11, B12) to 10m grid aligned with B02,03,04,08 |
| - Index generation: NDVI, EVI, SAVI, NDWI                                |
| - Projected Coordinate System: EPSG:32643 (UTM Zone 43N)                 |
| - Output generation: GeoTIFFs + GeoJSON labels                           |
+--------------------------------------------------------------------------+
                                     │
                    Handoff: GeoTIFFs + training_polygons.geojson
                                     │
                                     ▼
+--------------------------------------------------------------------------+
|                  MEMBER 1: MACHINE LEARNING & AI PIPELINE                |
| - Strict validation: CRS (EPSG:32643), dimensions, bounds, nodata, NaN   |
| - Spatial Leakage Prevention: GroupShuffleSplit on parcel/polygon IDs    |
| - Feature extraction: Multi-spectral bands + indices + temporal stats    |
| - Model: RandomForestClassifier (Paddy, Banana, Other)                   |
| - Dynamic evaluation: Accuracy, Precision, Recall, F1, Confusion Matrix  |
| - Feature importance extraction: Mapped to physical spectral bands       |
| - Parcel-level inference with prediction confidence score                |
| - Crop statistics aggregation (counts & area in sq km)                   |
+--------------------------------------------------------------------------+
                                     │
                    Handoff: classified_parcels.geojson + metrics
                                     │
                                     ▼
+--------------------------------------------------------------------------+
|                  MEMBER 3: FULL STACK & WEB GIS DASHBOARD                |
| - Spatial Database: PostgreSQL + PostGIS (parcels, geometries, metadata) |
| - Backend: FastAPI REST service with spatial queries & filters           |
| - Frontend: React + Leaflet / React-Leaflet GIS interface               |
| - Features: Layer toggles, crop class coloring, parcel popup info,       |
|   dynamic summary charts, study area statistics                          |
+--------------------------------------------------------------------------+
```

## Coordinate Reference System Standard
- **Project Standard CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- All rasters and vector calculations MUST use this metric projection so that area calculations (in square meters / square kilometers) are geometrically accurate and free from spherical distortion.
- GeoJSON outputs for web visualization (Member 3) will have geometries in standard WGS 84 (`EPSG:4343` / lat-lon) for Leaflet compatibility, while maintaining precise area properties (`area_sq_km`) computed in `EPSG:32643`.

## Target Classes
1. **Paddy**: Wetland rice cultivation, characterized by inundation (high NDWI / low initial NDVI) followed by rapid vegetative growth (steep NDVI increase).
2. **Banana**: Perennial horticulture crop with large leaf area index, maintaining consistently high NDVI and EVI throughout multiple seasons without drastic harvesting drops.
3. **Other**: Fallow land, scrubland, built-up areas, water bodies, and other seasonal vegetation.
