# Member 2 — GIS, Remote Sensing & Web GIS Frontend Module

## Responsibilities
### 1. Geospatial & Remote Sensing Engineering
- AOI Definition for Ambasamudram Taluk and Cheranmahadevi Taluk ($\ge 20 \text{ km}^2$, total $240.65\text{ km}^2$).
- Sentinel-2 L2A acquisition (openly available data via Copernicus / Planetary Computer / Google Earth Engine).
- Cloud and cloud-shadow masking via SCL (Scene Classification Layer, $>99.9\%$ valid pixels).
- Band resampling to standard 10m spatial resolution in `EPSG:32643`.
- Radiometric indices computation:
  - $\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$
  - $\text{EVI} = 2.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + 6 \times \text{B04} - 7.5 \times \text{B02} + 1}$
  - $\text{SAVI} = 1.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 0.5}$
  - $\text{NDWI} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$
- Target Coordinate Reference System: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- Export training ground-truth polygons and 293 delineated agricultural parcels with 240 tabular features.

### 2. Interactive Web GIS Frontend Dashboard (`member2-gis/frontend/`)
- React + Vite + React-Leaflet interactive cartographic dashboard.
- Dynamic color-coded parcel boundaries:
  - **Paddy**: Forest Green (`#16a34a`)
  - **Banana**: Vivid Amber/Gold (`#d97706`)
  - **Other**: Slate Neutral (`#64748b`)
- Real-time parcel inspection popup (ID, predicted crop, confidence score %, computed hectare area, centroid coordinates).
- Filter panel for multi-crop toggling and confidence threshold slider.
- Bi-seasonal temporal comparison modal (Kuruvai vs Samba season comparison, NDVI deltas, AI agronomic advisory).
- Agri-AI interactive chatbot drawer.
- Basemap switcher (Esri World Imagery, OpenStreetMap, CartoDB Light).

## Quickstart (Frontend Development)
```bash
cd member2-gis/frontend
npm install
npm run dev
```
Access dashboard at `http://localhost:5173`.
