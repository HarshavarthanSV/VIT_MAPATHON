# GIS Postprocessing & Spatial Integration Module

**Role**: MEMBER 2 — GIS / Remote Sensing Engineer  
**Project**: Agricultural Land Parcel and Crop Identification (Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District)

---

## 1. Overview
The `postprocessing/` package provides automated GIS validation, spatial joining, taluk-level crop acreage aggregation, and publication-ready cartographic visualization for the classified agricultural parcels produced by **Member 1 (ML / AI Engineer)**.

---

## 2. Directory & Module Structure

```
postprocessing/
├── validate_classified_parcels.py   # Spatial integrity audit, CRS conversion, and acreage stats
├── calculate_taluk_acreage.py       # Spatial join between parcels and Taluk boundaries
├── generate_classification_map.py   # 300 DPI high-resolution final crop classification map
├── vectorize_and_validate.py        # Raster-to-polygon vectorization utility
└── README.md                        # Documentation
```

---

## 3. Workflow & Processing Steps

```
Member 1 Classification (classified_parcels.geojson)
                        │
                        ▼
   [1. Spatial Integrity & Topology Audit]
   - Validates geometries with Shapely make_valid
   - Checks null/empty features and overlap pairs
   - Reprojects coordinates to EPSG:32643
                        │
                        ▼
   [2. Metric Acreage & Zonal Calculations]
   - Area in m², hectares (1 ha = 10,000 m²), and acres (1 acre = 4,046.86 m²)
   - Outputs: results/crop_statistics.csv & results/gis_validation_report.txt
                        │
                        ▼
   [3. Taluk-Level Spatial Join & Aggregation]
   - Point-in-polygon / intersection join with Ambasamudram & Cheranmahadevi
   - Computes Paddy, Banana, Other parcel counts, hectares, and % of taluk
   - Outputs: results/taluk_crop_acreage_summary.csv
                        │
                        ▼
   [4. Cartographic Map Rendering]
   - Publication-quality thematic rendering with color palette:
     * Paddy  -> Vivid Green (#27ae60)
     * Banana -> Golden Orange (#e67e22)
     * Other  -> Neutral Slate Gray (#7f8c8d)
   - Outputs: results/validation_maps/final_crop_classification_map.png
```

---

## 4. How to Execute

Run the modules individually or sequentially:

```bash
# 1. Run GIS validation & crop statistics
.venv\Scripts\python.exe postprocessing/validate_classified_parcels.py

# 2. Compute taluk-level acreage breakdown
.venv\Scripts\python.exe postprocessing/calculate_taluk_acreage.py

# 3. Generate high-resolution classification map
.venv\Scripts\python.exe postprocessing/generate_classification_map.py
```

---

## 5. Output Deliverables

| File | Description |
|---|---|
| [`results/validation_maps/final_crop_classification_map.png`](../results/validation_maps/final_crop_classification_map.png) | 300 DPI final classified parcels map with taluks, legend, and scale bar |
| [`results/taluk_crop_acreage_summary.csv`](../results/taluk_crop_acreage_summary.csv) | Taluk-level crop acreage breakdown for Ambasamudram and Cheranmahadevi |
| [`results/crop_statistics.csv`](../results/crop_statistics.csv) | Overall crop acreage and parcel distribution table |
| [`results/gis_validation_report.txt`](../results/gis_validation_report.txt) | Detailed GIS topology and spatial validation report |
