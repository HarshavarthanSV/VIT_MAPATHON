# Team Workflow & Directory Ownership

## Member Roles and Directory Ownership

| Member | Role | Primary Directory | Working Git Branch | Key Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Member 2** | GIS / Remote Sensing | `member2-gis/` | `member2-gis` | AOI definition, Sentinel-2 L2A acquisition, cloud masking, resampling to 10m in EPSG:32643, spectral index calculation (NDVI, EVI, SAVI, NDWI), multi-temporal stacks, ground truth label digitization. |
| **Member 1** | ML / AI Engineer | `member1-ml/` | `member1-ml` | Input data validation, spatial train/test splitting (GroupShuffleSplit), Random Forest classifier training, metrics evaluation, parcel inference, GeoJSON generation, crop statistics. |
| **Member 3** | Full Stack / GIS App | `member3-fullstack/` | `member3-fullstack` | PostGIS schema design & data loading, FastAPI REST API backend, React + Leaflet frontend dashboard, interactive map layers & statistics charts. |

---

## Parallel Development Rules

1. **Strict Folder Isolation**:
   - Member 1 modifies ONLY `member1-ml/` (and shared documentation when updating contracts).
   - Member 2 modifies ONLY `member2-gis/`.
   - Member 3 modifies ONLY `member3-fullstack/`.
   - Never delete or overwrite another member's code or directories.

2. **Git Discipline**:
   - Work on your designated branch (`member1-ml`, `member2-gis`, or `member3-fullstack`).
   - Do NOT work directly on `main`.
   - Do NOT force push (`git push -f`) or rewrite commit history (`git reset --hard`).
   - When ready for team integration, submit a Pull Request to merge into `main`.

3. **Data Contract Compliance**:
   - All modules communicate exclusively via agreed file contracts in well-known directory locations.
   - Member 2 deposits data in `member2-gis/outputs/` (or via external shared storage path configured in `config.yaml`).
   - Member 1 deposits ML results in `member1-ml/outputs/`.
   - Member 3 ingests directly from `member1-ml/outputs/`.

4. **No-Fake-Data & No-Hardcoding Policy**:
   - Never hardcode accuracy, confusion matrix, NDVI thresholds, or polygon geometries.
   - If real upstream data is not yet generated, pipelines must halt cleanly at the data boundary with informative messages.
   - Synthetic data is strictly restricted to isolated automated unit tests (`tests/`).
