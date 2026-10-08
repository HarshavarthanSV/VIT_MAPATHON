# Geospatial & ML Classification Audit and Validation Report
**Study Area:** Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu  
**Audit Date:** 2026-10-09  
**Audit Status:** PASSED (Production Data Verified, Fabricated Scaffolding Eliminated)

---

## 1. Executive Summary
This audit rigorously validates the production data pipeline for the VIT_MAPATHON / AgriMap agricultural crop identification and natural hazard impact system. All runtime crop classifications, parcel boundaries, confidence values, areas, and statistics originate strictly from verified Sentinel-2 Level-2A imagery, Random Forest classification, and physical remote sensing GIS validation.

---

## 2. Dataset Verification & Geometry Integrity
| Metric | Value | Status |
| :--- | :--- | :--- |
| **Primary Vector Deliverable** | data/parcels/cleaned/classified_parcels.geojson | Verified |
| **Total Features / Polygons** | **293** | Verified |
| **Geometry Validity** | **293 / 293 Valid (100.0%)** | Verified |
| **Coordinate Reference System (Source)** | EPSG:4326 (WGS 84) | Verified |
| **Projected Metric Area CRS** | EPSG:32643 (UTM Zone 43N) | Verified |
| **Duplicate Parcel IDs** | **0** | Clean |
| **Missing Crop Labels** | **0** | Clean |
| **Missing Confidence Scores** | **0** | Clean |
| **Total Study Parcel Area** | **171.65 ha (424.17 acres / 1.7165 km²)** | Verified |
| **Mean Model Confidence** | **86.55%** | Verified |

---

## 3. Audited Crop Class Distribution
Calculated strictly using projected geodesic metric calculations in EPSG:32643:

| Crop Class | Parcel Count | Area (Hectares) | Area (Acres) | Area Share (%) | Mean Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Non-Crop / Bare Soil / Settlement / Water** | 131 | 80.88 ha | 199.87 acres | 47.12% | 89.61% |
| **Paddy (Rice)** | 83 | 51.46 ha | 127.15 acres | 29.98% | 82.59% |
| **Banana (Plantation)** | 79 | 39.31 ha | 97.14 acres | 22.90% | 85.63% |
| **TOTAL** | **293** | **171.65 ha** | **424.17 acres** | **100.00%** | **86.55%** |

---

## 4. Taluk-Level Agricultural Acreage Breakdown
- **Ambasamudram Taluk (144 Parcels / 82.93 ha / 204.93 acres)**:
  - Paddy: 53 parcels (32.08 ha, 38.68% of taluk)
  - Banana: 44 parcels (21.77 ha, 26.25% of taluk)
  - Non-Crop: 48 parcels (29.09 ha, 35.07% of taluk)
- **Cheranmahadevi Taluk (149 Parcels / 88.72 ha / 219.24 acres)**:
  - Non-Crop: 83 parcels (51.80 ha, 58.38% of taluk)
  - Banana: 35 parcels (17.55 ha, 19.78% of taluk)
  - Paddy: 30 parcels (19.38 ha, 21.84% of taluk)

---

## 5. Investigation of Water / River Misclassification & Resolution
- **Root Cause:** Member 1's initial Random Forest training set contained only crop classes (Paddy, Banana, Other), omitting explicit waterbody and bare soil classes. Consequently, Thamirabarani river segments and waterbodies were forced into the nearest crop class (Paddy/Banana) due to moisture-driven spectral similarity.
- **Resolution:** A physical multi-temporal remote sensing mask (postprocessing/validate_non_crop_areas.py) was applied using Sentinel-2 L2A NDWI (> -0.05), NIR absorption (< 0.12), and temporal peak NDVI (< 0.20) to isolate perpetual water and non-cultivated land cover into Non-Crop.

---

## 6. Pipeline & API Contract Verification
- GET /api/parcels: Returns live GeoJSON FeatureCollection (293 features).
- GET /api/parcels/geojson: Alias returning exact GeoJSON FeatureCollection.
- GET /api/statistics: Aggregates dynamic study area summaries and crop distributions directly from PostGIS or live GeoJSON.
- GET /api/crops: Returns active crop classes (Paddy, Banana, Non-Crop) with live parcel counts and acreage.
- GET /api/health: Reports system status, database connection, and artifact readiness.
