"""
Sample Sentinel-2 L2A & Training Data Generator.
Creates a small synthetic 10m/20m test dataset covering a sample agricultural landscape
in Tirunelveli (EPSG:32643) with realistic spectral properties for:
- Paddy (Rice)
- Banana (Plantation)
- Water Body (River / Canal)
- Bare Soil / Road
This allows immediate end-to-end testing of the GIS pipeline without downloading gigabytes of satellite imagery.
"""

from pathlib import Path
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Polygon, box

def generate_sample_dataset(output_dir: Path = Path("data/sample")):
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating sample GIS test dataset in {output_dir.resolve()}...")

    # Spatial definition in UTM Zone 43N (EPSG:32643) - Tirunelveli coordinates
    # Top-left origin: X ~ 340000 m E, Y ~ 962000 m N (~8.7° N, 77.5° E)
    x_origin = 340000.0
    y_origin = 962000.0
    res_10m = 10.0
    res_20m = 20.0
    rows_10m = 100  # 1 km extent
    cols_10m = 100
    rows_20m = 50
    cols_20m = 50

    transform_10m = from_origin(x_origin, y_origin, res_10m, res_10m)
    transform_20m = from_origin(x_origin, y_origin, res_20m, res_20m)
    crs = "EPSG:32643"

    # Synthetic landscape ground truth mask (100x100)
    # 0-30: Paddy fields (wet, high NIR, low Red)
    # 30-65: Banana plantation (dense perennial vegetation)
    # 65-75: River / irrigation canal
    # 75-100: Bare soil / fallow land
    gt = np.zeros((rows_10m, cols_10m), dtype=np.uint8)
    gt[0:35, :] = 1    # Paddy
    gt[35:70, :] = 2   # Banana
    gt[70:78, :] = 3   # Water
    gt[78:100, :] = 4  # Bare Soil / Fallow

    # Define realistic surface reflectance scaled by 10000 (standard Sentinel-2 L2A BOA DN)
    # Band signatures: [B02_Blue, B03_Green, B04_Red, B08_NIR, B11_SWIR1, B12_SWIR2]
    signatures = {
        1: {"B02": 350,  "B03": 650,  "B04": 420,  "B08": 4200, "B11": 1800, "B12": 1100, "SCL": 4},  # Paddy
        2: {"B02": 280,  "B03": 750,  "B04": 380,  "B08": 5800, "B11": 1400, "B12": 850,  "SCL": 4},  # Banana
        3: {"B02": 600,  "B03": 550,  "B04": 300,  "B08": 150,  "B11": 80,   "B12": 50,   "SCL": 6},  # Water
        4: {"B02": 950,  "B03": 1300, "B04": 1600, "B08": 2100, "B11": 3100, "B12": 2600, "SCL": 5},  # Bare Soil
    }

    # Generate 10m bands (B02, B03, B04, B08)
    for b_name in ["B02", "B03", "B04", "B08"]:
        band_data = np.zeros((rows_10m, cols_10m), dtype=np.uint16)
        for class_id, sig in signatures.items():
            mask = (gt == class_id)
            noise = np.random.normal(0, sig[b_name] * 0.05, mask.shape).astype(np.int16)
            vals = np.clip(sig[b_name] + noise, 10, 10000).astype(np.uint16)
            band_data[mask] = vals[mask]

        out_path = output_dir / f"sample_{b_name}.tif"
        with rasterio.open(
            out_path, "w",
            driver="GTiff", height=rows_10m, width=cols_10m, count=1,
            dtype=np.uint16, crs=crs, transform=transform_10m, nodata=0, compress="lzw"
        ) as dst:
            dst.write(band_data, 1)
        print(f"  Created 10m band: {out_path.name}")

    # Generate 20m bands (B11, B12, SCL)
    gt_20m = gt[::2, ::2]
    for b_name in ["B11", "B12", "SCL"]:
        dtype = np.uint8 if b_name == "SCL" else np.uint16
        band_data = np.zeros((rows_20m, cols_20m), dtype=dtype)
        for class_id, sig in signatures.items():
            mask = (gt_20m == class_id)
            if b_name == "SCL":
                band_data[mask] = sig[b_name]
            else:
                noise = np.random.normal(0, sig[b_name] * 0.05, mask.shape).astype(np.int16)
                vals = np.clip(sig[b_name] + noise, 10, 10000).astype(np.uint16)
                band_data[mask] = vals[mask]

        out_path = output_dir / f"sample_{b_name}.tif"
        with rasterio.open(
            out_path, "w",
            driver="GTiff", height=rows_20m, width=cols_20m, count=1,
            dtype=dtype, crs=crs, transform=transform_20m, nodata=0, compress="lzw"
        ) as dst:
            dst.write(band_data, 1)
        print(f"  Created 20m band: {out_path.name}")

    # Create Sample Study Area AOI (GeoJSON)
    # Extent covering central 800m x 800m
    minx = x_origin + 100.0
    maxx = x_origin + 900.0
    maxy = y_origin - 100.0
    miny = y_origin - 900.0
    aoi_box = box(minx, miny, maxx, maxy)

    aoi_gdf = gpd.GeoDataFrame(
        [{"taluk": "Ambasamudram_Cheranmahadevi_Sample", "state": "Tamil Nadu", "district": "Tirunelveli", "geometry": aoi_box}],
        crs=crs
    )
    aoi_path = output_dir / "study_area.geojson"
    aoi_gdf.to_file(aoi_path, driver="GeoJSON")
    print(f"  Created Sample AOI: {aoi_path.name}")

    # Create Sample Training Parcel Polygons
    paddy_poly = Polygon([
        (x_origin + 150, y_origin - 150),
        (x_origin + 400, y_origin - 150),
        (x_origin + 400, y_origin - 300),
        (x_origin + 150, y_origin - 300),
    ])
    banana_poly = Polygon([
        (x_origin + 150, y_origin - 450),
        (x_origin + 450, y_origin - 450),
        (x_origin + 450, y_origin - 600),
        (x_origin + 150, y_origin - 600),
    ])
    water_poly = Polygon([
        (x_origin + 100, y_origin - 720),
        (x_origin + 800, y_origin - 720),
        (x_origin + 800, y_origin - 760),
        (x_origin + 100, y_origin - 760),
    ])

    parcels_gdf = gpd.GeoDataFrame([
        {"parcel_id": "P001", "crop_name": "Paddy", "class_id": 1, "geometry": paddy_poly},
        {"parcel_id": "P002", "crop_name": "Banana", "class_id": 2, "geometry": banana_poly},
        {"parcel_id": "P003", "crop_name": "Water", "class_id": 3, "geometry": water_poly},
    ], crs=crs)

    parcels_path = output_dir / "sample_training_parcels.geojson"
    parcels_gdf.to_file(parcels_path, driver="GeoJSON")
    print(f"  Created Sample Training Parcels: {parcels_path.name}")
    print("Sample data generation complete!")

if __name__ == "__main__":
    generate_sample_dataset()
