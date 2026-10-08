# Member 2 — Copernicus Sentinel-2 L2A Acquisition & Preprocessing Guide

## Problem Statement 1: Ambasamudram & Cheranmahadevi Taluks (Tirunelveli District)
- **Target Area**: Ambasamudram Taluk + Cheranmahadevi Taluk ($\ge 20 \text{ sq. km}$).
- **Target Crops**: Paddy vs. Banana vs. Other.
- **Required Metric CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- **Required Resolution**: 10.0 meters.

---

## Pre-Defined AOI
The validated bounding polygon for Ambasamudram and Cheranmahadevi has already been defined for you at:
`member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson`
- Total Area: **119.41 sq. km** (safely exceeds the 20 sq. km requirement).
- Bounding Box: `[77.420, 8.660, 77.560, 8.730]` (Lon/Lat).

---

## Acquisition Options

### Option A: Copernicus Browser (Web UI)
1. Go to [Copernicus Browser](https://browser.dataspace.copernicus.eu/).
2. Login with your Copernicus Data Space Ecosystem (CDSE) credentials.
3. Click the **Upload AOI** icon on the right toolbar and upload:
   `member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson`.
4. In the Search tab:
   - Data Source: **Sentinel-2**.
   - Processing Level: **Level-2A (L2A)** (Bottom of Atmosphere reflectance).
   - Cloud coverage filter: **< 10%**.
   - Date range: Select dates corresponding to Tirunelveli crop seasons:
     * *Pishanam / Samba Season*: November to January (Peak vegetative greenness for Paddy).
     * *Post-harvest / Pre-planting*: February to March or September (Distinguishes perennial Banana from harvested seasonal Paddy).
5. Identify 2–3 clear scenes across dates to enable multi-temporal differentiation.
6. Download the product `.zip` files (or export individual bands cropped to the AOI).

---

### Option B: Automated Cloud-Optimized Fetch (No 1GB Zips Needed!)
Instead of downloading gigabyte-sized zip files and extracting them manually, you can use the automated script:
`member2-gis/scripts/acquire_sentinel2_l2a.py`

This script streams only the clipped bounding box over Ambasamudram and Cheranmahadevi directly, resamples bands to 10m, calculates spectral indices, and saves them straight into `member2-gis/outputs/features/`!

Run:
```bash
python member2-gis/scripts/acquire_sentinel2_l2a.py --aoi member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson
```

---

## Required Handoff Output Checklist for Member 1

Once processing is complete, your outputs must reside in:

```
member2-gis/outputs/
├── features/
│   ├── B02.tif   (10m Blue)
│   ├── B03.tif   (10m Green)
│   ├── B04.tif   (10m Red)
│   ├── B08.tif   (10m NIR)
│   ├── B11.tif   (10m SWIR-1 - resampled from 20m)
│   ├── B12.tif   (10m SWIR-2 - resampled from 20m)
│   ├── NDVI.tif  ((B08 - B04) / (B08 + B04))
│   ├── EVI.tif   (2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1))
│   ├── SAVI.tif  (1.5 * (B08 - B04) / (B08 + B04 + 0.5))
│   └── NDWI.tif  ((B03 - B08) / (B03 + B08))
├── temporal/
│   ├── date_01/  (same bands for date 1)
│   ├── date_02/  (same bands for date 2)
│   └── ...
├── labels/
│   └── training_polygons.geojson  (properties: parcel_id, crop_type: Paddy|Banana|Other)
└── parcels/
    └── parcel_boundaries.geojson  (properties: parcel_id, total area >= 20 sq km)
```

---

## Verifying Compatibility with Member 1
Run Member 1's validation test to ensure your rasters and labels are 100% compliant:
```bash
python member1-ml/main.py --config member1-ml/config/config.yaml
```
If your data meets the contract, Member 1's pipeline will automatically train the Random Forest model and produce `classified_parcels.geojson` without errors!
