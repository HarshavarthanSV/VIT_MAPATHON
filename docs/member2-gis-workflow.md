# Member 2 — GIS & Remote Sensing Workflow & ML Handoff Specification

## 1. Project Overview & Role Definition
- **Project**: Agricultural Land Parcel and Crop Identification
- **Objective**: Differentiate agricultural land parcels and identify/differentiate **paddy** (rice) and **banana** plantations in Tirunelveli District, Tamil Nadu (specifically **Ambasamudram Taluk** and **Cheranmahadevi Taluk**), covering a minimum study area of **20 sq. km**.
- **Role**: **MEMBER 2 — GIS / REMOTE SENSING ENGINEER**
- **Responsibilities**:
  - Sentinel-2 Level-2A data acquisition, cataloging, and organization.
  - AOI boundary preparation and spatial validation.
  - Raster preprocessing: cloud/shadow masking via SCL/QA60, AOI clipping, CRS standardization (`EPSG:32643`), and 20m-to-10m spatial resampling.
  - Robust calculation of spectral indices (**NDVI**, **EVI**, **SAVI**, **NDWI**, **MNDWI**).
  - Multi-temporal feature stacking with comprehensive metadata tracking.
  - Training dataset / parcel polygon mask extraction.
  - QGIS visual validation and clean data handoff to **Member 1 (ML / AI Engineer)**.

---

## 2. Geospatial Standards & Sensor Specifications

### 2.1 Coordinate Reference System (CRS)
- **Standard CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N)
- All rasters, vector boundaries, and intermediate feature layers are strictly projected and aligned to `EPSG:32643` to ensure sub-meter spatial consistency and area computations in metric units ($m^2$, hectares).

### 2.2 Satellite Data Source: Sentinel-2 Level-2A (Surface Reflectance)
| Band | Description | Native Resolution | Central Wavelength ($\mu m$) | Purpose in Crop Discrimination |
|---|---|---|---|---|
| **B02** | Blue | 10 m | 0.490 | Atmosphere correction, EVI computation |
| **B03** | Green | 10 m | 0.560 | Crop vigor, MNDWI water body delineation |
| **B04** | Red | 10 m | 0.665 | Chlorophyll absorption, NDVI/EVI/SAVI |
| **B08** | NIR (Broad) | 10 m | 0.842 | Canopy biomass, cell structure reflection |
| **B11** | SWIR-1 | 20 m *(resampled to 10 m)* | 1.610 | Canopy moisture, NDWI, soil moisture |
| **B12** | SWIR-2 | 20 m *(resampled to 10 m)* | 2.190 | Soil background differentiation, crop residue |
| **SCL** | Scene Classification | 20 m *(resampled to 10 m)* | — | Cloud, cloud shadow, water, snow masking |

---

## 3. Spectral Indices Formulations

| Index | Mathematical Formula | Key Application for Paddy vs Banana |
|---|---|---|
| **NDVI** | $\frac{B08 - B04}{B08 + B04}$ | General greenness and biomass dynamics over the growth cycle. |
| **EVI** | $2.5 \times \frac{B08 - B04}{B08 + 6.0 \cdot B04 - 7.5 \cdot B02 + 1.0}$ | High biomass sensitivity; prevents saturation over dense perennial banana canopies. |
| **SAVI** | $\frac{B08 - B04}{B08 + B04 + 0.5} \times 1.5$ | Minimizes soil background reflection during early transplanting / flooded paddy stages. |
| **NDWI** (Gao) | $\frac{B08 - B11}{B08 + B11}$ | Measures canopy moisture content. Crucial for detecting flooded paddy fields vs upland banana. |
| **MNDWI** (Xu) | $\frac{B03 - B11}{B03 + B11}$ | Delineates irrigation canals, ponds, and the Tamirabarani River network. |

*Note: All divisions are protected against division-by-zero, negative/saturated anomalies, and NoData pixels.*

---

## 4. Storage & Repository Policy

To keep GitHub light and efficient, large geospatial datasets reside on **Google Drive**, while scripts, configurations, and documentation reside in **GitHub**:

### 4.1 GitHub Repository (`member2-gis` branch)
- Source code under `preprocessing/`, `postprocessing/`, and `scripts/`.
- Small sample test fixtures under `data/sample/`.
- Configuration files (`requirements.txt`, `.gitignore`, `README.md`).
- Workflow documentation (`docs/`).

### 4.2 Google Drive Shared Directory Structure
```
Shared_Google_Drive/
├── 01_RAW/
│   └── Sentinel2_L2A/
│       ├── 2023-11-15_T43KGS/
│       ├── 2023-12-20_T43KGS/
│       ├── 2024-01-15_T43KGS/
│       └── 2024-02-15_T43KGS/
├── 02_AOI_BOUNDARIES/
│   ├── Tirunelveli_District.geojson
│   ├── Ambasamudram_Taluk.geojson
│   └── Cheranmahadevi_Taluk.geojson
├── 03_PROCESSED/
│   ├── clipped/
│   ├── cloud_masked/
│   └── resampled_10m/
├── 04_FEATURES/
│   ├── NDVI/
│   ├── EVI/
│   ├── SAVI/
│   ├── NDWI/
│   └── feature_stacks/
└── 05_TRAINING_DATA/
    ├── images/
    ├── labels/
    └── sample_tables/
```

---

## 5. Member 2 $\rightarrow$ Member 1 Handoff Contract (ML / AI Engineer)

Member 1 consumes the preprocessed GIS deliverables for training **Random Forest** and **U-Net / CNN** models:

### 5.1 Deliverables Provided by Member 2
1. **Multi-Band Feature Stack GeoTIFFs (`*_feature_stack_10m.tif`)**:
   - 10-meter spatial resolution, CRS `EPSG:32643`.
   - Channels include: `B02`, `B03`, `B04`, `B08`, `B11` (resampled), `B12` (resampled), `NDVI`, `SAVI`, `EVI`, `NDWI`, `MNDWI`.
2. **Companion Metadata JSON (`*_feature_stack_10m.json`)**:
   - Explicit channel index to band name mapping.
   - Acquisition date(s), affine transform matrix, bounding box, dimensions, and NoData value (`-9999.0`).
3. **Tabular Training Pixel Feature CSV (`*_training_features.csv`)**:
   - Extracted pixel values mapped to ground truth classes:
     - `1`: Paddy
     - `2`: Banana
     - `3`: Water
     - `4`: Other Vegetation
     - `5`: Bare Soil / Built-up
4. **Parcel Boundary Masks & Vector GeoDataFrames**:
   - Clean polygon shapes for spatial cross-validation and U-Net patch generation.

---

## 6. QGIS Visual Validation Guide
To verify preprocessed outputs visually in QGIS:
1. **Load AOI**: Drag `data/sample/study_area.geojson` or official taluk boundary into QGIS.
2. **Load False Color Composite**:
   - Add `sample_B08.tif` (Red channel), `sample_B04.tif` (Green channel), `sample_B03.tif` (Blue channel).
   - Dense banana will appear deep red/burgundy; active paddy appears bright red/orange; flooded fields appear dark/cyan.
3. **Inspect Spectral Indices**:
   - Load `2024-01-15_NDVI.tif` and apply a `RdYlGn` or `Viridis` color ramp (values 0.2 to 0.9).
   - Load `2024-01-15_NDWI.tif` and verify moisture contrast in irrigated paddy vs upland orchards.
4. **Validate Parcels**: Overlay `sample_training_parcels.geojson` to ensure pixel alignment with field boundaries.

---

## 7. Running the GIS Pipeline

### 7.1 Verify Environment
```bash
.venv\Scripts\python.exe scripts/verify_environment.py
```

### 7.2 Run Preprocessing on Sample Dataset
```bash
.venv\Scripts\python.exe scripts/run_gis_pipeline.py --data-dir data/sample --output-dir data/processed --date 2024-01-15
```

### 7.3 Run Preprocessing on Full Sentinel-2 Granule
```bash
.venv\Scripts\python.exe scripts/run_gis_pipeline.py --data-dir path/to/raw_s2_bands --aoi data/sample/study_area.geojson --output-dir data/processed --date 2024-01-15
```
