# Team Workflow & Directory Ownership (2-Member Architecture)

## Member Roles and Directory Ownership

| Member | Focus Area | Primary Directory | Working Git Branch | Key Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1** | AI / Machine Learning & Backend Systems | `member1-ml/` | `member1-ml` | Input data validation, spatial train/test splitting, Random Forest classifier training, metrics evaluation, parcel inference, GeoJSON generation, crop statistics, FastAPI REST API backend (`member1-ml/backend/`), PostGIS schema & data ingestion (`member1-ml/database/`), automated PDF report generation, and automated backend test suite. |
| **Member 2** | GIS / Remote Sensing & Web GIS Frontend | `member2-gis/`, `data/` | `member2-gis` | AOI definition, Sentinel-2 L2A acquisition, cloud masking, resampling to 10m in EPSG:32643, spectral index calculation (NDVI, EVI, SAVI, NDWI), 60-layer multi-temporal stacks, ground truth label digitization, React + Leaflet frontend dashboard (`member2-gis/frontend/`), interactive map layers, temporal comparisons, and AI chatbot UI. |

---

## Parallel Development Rules

1. **Folder Ownership**:
   - Member 1 modifies `member1-ml/` (ML algorithms, training, models, backend API, database scripts, and backend tests).
   - Member 2 modifies `member2-gis/` (GIS preprocessing, spectral indices, vector layers, and React frontend dashboard) and preprocessing scripts.
   - Shared documentation and project-level configs are maintained collaboratively.

2. **Git Discipline**:
   - Work on your designated branch (`member1-ml` or `member2-gis`).
   - Do NOT force push (`git push -f`) or rewrite commit history (`git reset --hard`).
   - When ready for team integration, submit a Pull Request to merge into `main`.

3. **Data Contract Compliance**:
   - Member 2 deposits processed datasets in `data/features/tabular/ml_training_dataset.csv` and vector layers in `member2-gis/inputs/` & `data/parcels/`.
   - Member 1 trains the model, outputs `classified_parcels.geojson` and `crop_statistics.json` in `member1-ml/outputs/`, and serves them via the FastAPI backend (`member1-ml/backend/`).
   - Member 2's React frontend accesses the backend REST endpoints at `/api/parcels`, `/api/statistics`, `/api/metrics`, `/api/temporal-comparison`, etc.

4. **No-Fake-Data & No-Hardcoding Policy**:
   - Never hardcode accuracy, confusion matrix, NDVI thresholds, or polygon geometries.
   - All analytics, statistics, and metrics are computed dynamically from real Sentinel-2 satellite data and the trained Random Forest model.
