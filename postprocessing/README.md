# GIS Postprocessing & Spatial Validation Module

**Role**: MEMBER 2 — GIS / Remote Sensing Engineer  
**Project**: Agricultural Land Parcel and Crop Identification (Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District)

---

## 1. Overview
The `postprocessing/` package provides automated GIS validation, multi-temporal physical masking (Water and Non-Crop), spatial auditing, taluk-level crop acreage aggregation, and publication-ready cartographic visualization for the classified agricultural parcels.

---

## 2. Directory & Module Structure

```
postprocessing/
├── validate_non_crop_areas.py       # Sentinel-2 physical Water (NDWI) and Non-Crop (Peak NDVI < 0.20) masking and parcel audit
├── validate_classification.py        # End-to-end GIS integrity, confusion cross-tabulation, and classification validation
├── generate_validation_map.py       # 300 DPI 4-panel GIS validation map (RGB + Water/Non-Crop Mask + Validated Parcels + Summary)
├── validate_classified_parcels.py   # Spatial topology audit, CRS conversion (EPSG:32643), and parcel metrics
├── calculate_taluk_acreage.py       # Spatial join between parcels and Taluk boundaries (Ambasamudram & Cheranmahadevi)
├── generate_classification_map.py   # Publication-quality final classified parcels map
├── vectorize_and_validate.py        # Raster-to-polygon vectorization utility
└── README.md                        # Documentation
```

---

## 3. Workflow & Physical Masking Pipeline

```
Sentinel-2 Level-2A Multi-Temporal Bands (2026-03-20, 2026-04-02, 2026-04-22, 2026-09-09)
                                   │
                                   ▼
    [1. Multi-Temporal Physical Masking (validate_non_crop_areas.py)]
    - Water Mask: NDWI > -0.05, NIR BOA < 0.12, Green > NIR (Traps Thamirabarani river/canals)
    - Non-Crop Mask: Temporal peak NDVI < 0.20 across all dates (Traps bare soil, roads, urban, fallow)
    - Crop Vegetation Mask: Peak NDVI >= 0.28 with active phenological vigor
                                   │
                                   ▼
    [2. Cadastral Parcel Zonal Audit]
    - Rasterizes all 293 cadastral parcels and audits pixel composition against physical masks
    - Parcels with >= 40% water -> Reclassified to 'Water' / 'Non-Crop'
    - Parcels with >= 50% non-crop -> Reclassified to 'Non-Crop'
    - Active vegetative parcels -> Verified as 'Paddy' or 'Banana'
    - Updates: data/parcels/cleaned/classified_parcels.geojson & results/non_crop_water_audit.csv
                                   │
                                   ▼
    [3. Comprehensive GIS & Accuracy Validation (validate_classification.py)]
    - Standardizes CRS to EPSG:32643 (UTM Zone 43N)
    - Validates geometry topology with Shapely make_valid (0 invalid, 0 nulls, 0 empty)
    - Computes confusion cross-tabulation against physical ground truth
    - Outputs: results/gis_classification_validation_report.txt, results/crop_statistics.csv,
      and results/taluk_crop_acreage_summary.csv
                                   │
                                   ▼
    [4. High-Resolution Cartographic Rendering]
    - Panel map: results/validation_maps/classification_validation_map.png (300 DPI)
    - Final crop map: results/validation_maps/final_crop_classification_map.png (300 DPI)
```

---

## 4. How to Execute

Run the complete validation pipeline:

```bash
# 1. Audit parcels against physical Water and Non-Crop masks
.venv\Scripts\python.exe postprocessing/validate_non_crop_areas.py

# 2. Run comprehensive GIS & remote sensing classification validation
.venv\Scripts\python.exe postprocessing/validate_classification.py

# 3. Generate 4-panel GIS classification validation map (300 DPI)
.venv\Scripts\python.exe postprocessing/generate_validation_map.py

# 4. Generate final classified crop acreage map (300 DPI)
.venv\Scripts\python.exe postprocessing/generate_classification_map.py
```

---

## 5. Output Deliverables

| File | Description |
|---|---|
| [`results/validation_maps/classification_validation_map.png`](../results/validation_maps/classification_validation_map.png) | 300 DPI 4-panel GIS validation map (RGB + Water/Non-Crop Mask + Validated Parcels + Summary) |
| [`results/validation_maps/final_crop_classification_map.png`](../results/validation_maps/final_crop_classification_map.png) | 300 DPI final classified parcels thematic map with taluk divisions |
| [`results/gis_classification_validation_report.txt`](../results/gis_classification_validation_report.txt) | Comprehensive GIS topology, remote sensing accuracy, and spatial audit report |
| [`results/non_crop_water_audit.csv`](../results/non_crop_water_audit.csv) | Per-parcel physical water %, non-crop %, vegetation %, and reclassification audit |
| [`results/taluk_crop_acreage_summary.csv`](../results/taluk_crop_acreage_summary.csv) | Taluk-level crop acreage breakdown for Ambasamudram and Cheranmahadevi |
| [`results/crop_statistics.csv`](../results/crop_statistics.csv) | Overall crop acreage and parcel distribution table |
