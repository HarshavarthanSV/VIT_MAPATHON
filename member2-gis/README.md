# Member 2 — GIS & Remote Sensing Module

## Responsibilities
- AOI Definition for Ambasamudram Taluk and Cheranmahadevi Taluk ($\ge 20 \text{ km}^2$).
- Sentinel-2 L2A acquisition (openly available data via Copernicus / Planetary Computer / Google Earth Engine).
- Cloud and cloud-shadow masking via SCL (Scene Classification Layer).
- Band resampling to standard 10m spatial resolution.
- Radiometric indices computation:
  - $\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$
  - $\text{EVI} = 2.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + 6 \times \text{B04} - 7.5 \times \text{B02} + 1}$
  - $\text{SAVI} = 1.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 0.5}$
  - $\text{NDWI} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$
- Target Coordinate Reference System: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- Export handoff GeoTIFFs to `outputs/features/` and `outputs/temporal/`.
- Export training ground-truth polygons to `outputs/labels/training_polygons.geojson`.
- Export study area parcel boundaries to `outputs/parcels/parcel_boundaries.geojson`.
