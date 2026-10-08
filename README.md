# Agricultural Land Parcel and Crop Identification (VIT MAPATHON)

Automated identification and differentiation of agricultural land parcels, **paddy** (rice), and **banana** plantations in **Tirunelveli District** (Ambasamudram & Cheranmahadevi Taluks), Tamil Nadu, India, using Sentinel-2 Level-2A surface reflectance satellite imagery.

---

## 👥 Team Roles & Responsibilities

| Role | Member | Responsibilities |
|---|---|---|
| **Member 1** | ML / AI Engineer | Random Forest classification, U-Net/CNN segmentation, model training, cross-validation, and crop prediction model. |
| **Member 2** | **GIS / Remote Sensing Engineer** *(This Branch)* | Sentinel-2 acquisition, AOI boundary preparation, cloud masking (SCL/QA60), CRS standardization (`EPSG:32643`), 20m $\rightarrow$ 10m resampling, spectral indices (NDVI, EVI, SAVI, NDWI, MNDWI), multi-temporal feature stacking, training data preparation, and QGIS validation. |
| **Member 3** | Full-Stack Engineer | FastAPI backend, PostgreSQL/PostGIS database, React + TypeScript + React-Leaflet frontend dashboard, and interactive parcel visualization. |

---

## 📂 Repository Structure

```
VIT_MAPATHON/
├── .venv/                         # Project-local Python virtual environment
├── data/
│   ├── sample/                    # Small testable samples (AOI, sample bands, parcels)
│   └── processed/                 # Local outputs (git-ignored)
├── preprocessing/
│   ├── download/                  # Granule discovery & cataloging utilities
│   ├── cloud_mask/                # SCL and QA60 cloud/shadow masking
│   ├── clipping/                  # Vector AOI clipping with reprojection
│   ├── resampling/                # 20m to 10m grid alignment (B11, B12, SCL)
│   ├── indices/                   # NDVI, EVI, SAVI, NDWI, MNDWI calculations
│   └── feature_stack/             # Multi-band/multi-temporal stacking & ML exports
├── postprocessing/
│   └── vectorize_and_validate.py  # Raster mask to vector polygon conversion
├── scripts/
│   ├── verify_environment.py      # Dependency & GDAL/PROJ verification
│   ├── create_sample_data.py      # Synthetic test scene generator
│   └── run_gis_pipeline.py        # End-to-end GIS pipeline CLI runner
├── docs/
│   └── member2-gis-workflow.md    # Member 2 workflow & ML handoff contract
├── requirements.txt               # GIS dependencies
├── .gitignore                     # Excludes large rasters (*.tif), archives, and .venv
└── README.md
```

---

## 🚀 Quickstart (Member 2 — GIS Pipeline)

### 1. Activate Environment & Verify
```bash
# Verify all GIS dependencies and GDAL/PROJ bindings
.venv\Scripts\python.exe scripts/verify_environment.py
```

### 2. Generate Sample Test Fixture (Optional)
```bash
# Creates 10m/20m sample rasters and AOI in data/sample/
.venv\Scripts\python.exe scripts/create_sample_data.py
```

### 3. Run End-to-End Preprocessing Pipeline
```bash
# Executes clipping, cloud masking, resampling, indices, and ML feature stacking
.venv\Scripts\python.exe scripts/run_gis_pipeline.py --data-dir data/sample --output-dir data/processed --date 2024-01-15
```

---

## 🗺️ Geospatial Standards
- **Study Area**: Ambasamudram Taluk & Cheranmahadevi Taluk, Tirunelveli District, Tamil Nadu (Minimum study area: $\ge 20\text{ km}^2$).
- **Coordinate Reference System (CRS)**: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- **Core Sentinel-2 Bands**:
  - **10 m**: `B02` (Blue), `B03` (Green), `B04` (Red), `B08` (NIR).
  - **20 m**: `B11` (SWIR-1), `B12` (SWIR-2), `SCL` (Scene Classification).
- **Spectral Indices**:
  - $\text{NDVI} = (B08 - B04) / (B08 + B04)$
  - $\text{EVI} = 2.5 \cdot (B08 - B04) / (B08 + 6 \cdot B04 - 7.5 \cdot B02 + 1)$
  - $\text{SAVI} = ((B08 - B04) / (B08 + B04 + 0.5)) \cdot 1.5$
  - $\text{NDWI} = (B08 - B11) / (B08 + B11)$
  - $\text{MNDWI} = (B03 - B11) / (B03 + B11)$

---

## 🌿 Git & Collaboration Rules
- **Dedicated Branch**: `member2-gis`
- Do not commit large satellite datasets or `.tif` files to Git. Large datasets are managed via the shared Google Drive.
- Check [docs/member2-gis-workflow.md](docs/member2-gis-workflow.md) for full ML handoff specifications.
