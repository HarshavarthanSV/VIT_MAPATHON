"""
Test Fixtures and Synthetic Generators for Isolated Automated Tests.
Note: Per project guidelines, synthetic data is strictly isolated inside tests/ and never used as project output.
"""

import os
import sys
import tempfile
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import box, Polygon

# Ensure member1-ml is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
member1_dir = os.path.dirname(current_dir)
if member1_dir not in sys.path:
    sys.path.insert(0, member1_dir)


@pytest.fixture
def synthetic_raster_environment(tmp_path):
    """
    Creates a temporary directory with aligned synthetic Sentinel-2 GeoTIFFs (EPSG:32643).
    Extent: 50 x 50 pixels at 10m resolution (500m x 500m).
    """
    features_dir = tmp_path / "features"
    features_dir.mkdir()

    width, height = 50, 50
    transform = from_origin(350000, 960000, 10, 10)
    crs = "EPSG:32643"

    bands = ["B02", "B03", "B04", "B08", "B11", "B12", "NDVI", "EVI", "SAVI", "NDWI"]
    
    np.random.seed(42)
    created_files = {}

    for band in bands:
        fpath = features_dir / f"{band}.tif"
        if band.startswith("B"):
            # Surface reflectance values (e.g. 0.05 to 0.45)
            data = (np.random.uniform(0.05, 0.45, (height, width)) * 10000).astype(np.uint16)
            dtype = rasterio.uint16
            nodata = 0
        else:
            # Normalized difference index values (-1.0 to 1.0)
            data = np.random.uniform(0.1, 0.85, (height, width)).astype(np.float32)
            dtype = rasterio.float32
            nodata = -9999.0

        with rasterio.open(
            str(fpath),
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=dtype,
            crs=crs,
            transform=transform,
            nodata=nodata
        ) as dst:
            dst.write(data, 1)

        created_files[band] = str(fpath)

    return {
        "dir": str(features_dir),
        "files": created_files,
        "width": width,
        "height": height,
        "crs": crs,
        "transform": transform
    }


@pytest.fixture
def synthetic_labels_file(tmp_path):
    """
    Creates a temporary GeoJSON with training polygons in EPSG:32643 covering Paddy, Banana, Other.
    """
    labels_file = tmp_path / "training_polygons.geojson"
    
    # Create distinct bounding boxes within the 500m x 500m raster extent (350000 to 350500, 959500 to 960000)
    polys = [
        box(350050, 959800, 350150, 959950), # Poly 1
        box(350200, 959800, 350300, 959950), # Poly 2
        box(350350, 959800, 350450, 959950), # Poly 3
        box(350050, 959600, 350150, 959750), # Poly 4
        box(350200, 959600, 350300, 959750), # Poly 5
        box(350350, 959600, 350450, 959750), # Poly 6
    ]

    crops = ["Paddy", "Paddy", "Banana", "Banana", "Other", "Other"]
    ids = [f"parcel_{i+1:03d}" for i in range(len(polys))]

    gdf = gpd.GeoDataFrame({
        "parcel_id": ids,
        "crop_type": crops,
        "geometry": polys
    }, crs="EPSG:32643")

    gdf.to_file(str(labels_file), driver="GeoJSON")
    return str(labels_file)


@pytest.fixture
def synthetic_parcels_file(tmp_path):
    """
    Creates a temporary GeoJSON with candidate agricultural parcels for inference.
    """
    parcels_file = tmp_path / "parcel_boundaries.geojson"
    
    polys = [
        box(350020, 959520, 350140, 959640),
        box(350160, 959520, 350280, 959640),
        box(350300, 959520, 350420, 959640),
    ]
    ids = [f"target_parcel_{i+1:03d}" for i in range(len(polys))]

    gdf = gpd.GeoDataFrame({
        "parcel_id": ids,
        "geometry": polys
    }, crs="EPSG:32643")

    gdf.to_file(str(parcels_file), driver="GeoJSON")
    return str(parcels_file)
