# Member 2 → Member 1 Data Contract

## 1. Overview
This document specifies the exact interface and requirements that **Member 2 (GIS / Remote Sensing Engineer)** must satisfy when providing processed satellite data to **Member 1 (ML / AI Engineer)**.

The ML pipeline is automated, data-driven, and strictly validates all inputs against this specification.

---

## 2. Directory Layout & File Locations
Member 2 outputs must be placed in `member2-gis/outputs/` (or configured via `config.yaml`):

```
member2-gis/outputs/
├── features/                          # Baseline single-scene GeoTIFF rasters (10m)
│   ├── B02.tif                        # Blue band (10m)
│   ├── B03.tif                        # Green band (10m)
│   ├── B04.tif                        # Red band (10m)
│   ├── B08.tif                        # NIR band (10m)
│   ├── B11.tif                        # SWIR-1 (20m resampled to 10m)
│   ├── B12.tif                        # SWIR-2 (20m resampled to 10m)
│   ├── NDVI.tif                       # (B08 - B04) / (B08 + B04)
│   ├── EVI.tif                        # 2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)
│   ├── SAVI.tif                       # 1.5 * (B08 - B04) / (B08 + B04 + 0.5)
│   └── NDWI.tif                       # (B03 - B08) / (B03 + B08)
├── temporal/                          # Optional multi-temporal dates
│   ├── date_01/                       # e.g., 2023-01-15 or date_01
│   │   ├── B02.tif, B04.tif, B08.tif, NDVI.tif, ...
│   │   └── ...
│   ├── date_02/
│   │   └── ...
│   └── date_03/
│       └── ...
├── labels/                            # Ground truth training polygons
│   └── training_polygons.geojson      # Polygons with crop_type and parcel_id
└── parcels/                           # Agricultural parcel boundaries for inference
    └── parcel_boundaries.geojson      # Candidate parcels across >= 20 sq. km
```

---

## 3. Coordinate Reference System (CRS) Standard
- **Required Metric CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N).
- **Reason**: UTM Zone 43N covers Tirunelveli District (Ambasamudram and Cheranmahadevi Taluks). Units are in meters, which allows accurate spatial resolution (10.0m) and exact polygon area calculations ($m^2$ and $km^2$).
- If GeoJSON vector files are provided in `EPSG:4326` (WGS 84 lat/lon), the pipeline will automatically detect and reproject them to `EPSG:32643`.

---

## 4. Raster Requirements & Alignment
1. **Resolution**: 10.0 meters per pixel. Bands B11 and B12 (native 20m) MUST be resampled (bilinear or cubic) to match the 10m pixel grid of B02, B03, B04, and B08.
2. **Alignment**: All rasters in `features/` MUST have identical:
   - Pixel dimensions: `(height, width)`
   - Affine transform: `(west, res_x, 0, north, 0, -res_y)`
   - Coordinate Reference System: `EPSG:32643`
   - Bounding box
3. **Data Types & Values**:
   - Bands B02, B03, B04, B08, B11, B12: Surface reflectance scaled (e.g. `uint16` 0 to 10000 or `float32` 0.0 to 1.0).
   - Indices (NDVI, EVI, SAVI, NDWI): `float32` values ranging from -1.0 to 1.0.
   - Nodata: Consistent nodata value (e.g. 0 for reflectance uint16, -9999.0 for float32).
4. **Cloud Masking**: SCL (Scene Classification Layer) or cloud mask must be applied prior to computing indices. Masked cloudy pixels should be set to nodata.

---

## 5. Training Labels Vector Contract (`training_polygons.geojson`)
1. **Format**: GeoJSON FeatureCollection (or GeoPackage).
2. **Required Attributes**:
   - `parcel_id` (or `id`): Unique string identifier per training polygon (e.g., `parcel_0001`).
   - `crop_type` (or `crop`): Class label string.
3. **Canonical Class Names**:
   - `Paddy` (also accepted: `paddy`, `rice`, `RICE`)
   - `Banana` (also accepted: `banana`, `plantain`, `BANANA`)
   - `Other` (also accepted: `other`, `fallow`, `scrub`, `builtup`, `water`)
4. **Geometry Integrity**:
   - Geometries must be valid `Polygon` or `MultiPolygon`.
   - Polygons must fall strictly within the spatial bounds of the raster imagery.

---

## 6. Agricultural Parcels Vector Contract (`parcel_boundaries.geojson`)
1. **Purpose**: Represents all agricultural parcel boundaries in Ambasamudram and Cheranmahadevi Taluks that will be classified by the model and ingested into PostGIS for Web GIS serving.
2. **Required Area**:
   - Total study area covered must be **$\ge 20 \text{ sq. km}$**.
3. **Required Properties**:
   - `parcel_id`: Unique identifier per parcel.
