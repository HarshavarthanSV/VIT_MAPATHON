"""
Tests for Data Validation and Geospatial Integrity Checking.
"""

import os
import pytest
import geopandas as gpd
from shapely.geometry import box, Point

from preprocessing.validation import (
    validate_raster_metadata,
    validate_raster_alignment,
    validate_labels_file,
    validate_study_area,
    DataNotAvailableError,
    GeospatialValidationError,
)


def test_missing_raster_raises_data_not_available():
    with pytest.raises(DataNotAvailableError):
        validate_raster_metadata("non_existent_band.tif")


def test_validate_raster_metadata_success(synthetic_raster_environment):
    b02_path = synthetic_raster_environment["files"]["B02"]
    meta = validate_raster_metadata(b02_path, expected_crs="EPSG:32643")
    
    assert meta["width"] == 50
    assert meta["height"] == 50
    assert meta["crs_valid"] is True
    assert meta["valid_pixel_count"] > 0
    assert meta["min_val"] >= 0


def test_validate_raster_alignment_success(synthetic_raster_environment):
    paths = list(synthetic_raster_environment["files"].values())
    assert validate_raster_alignment(paths) is True


def test_validate_labels_file_success(synthetic_labels_file):
    gdf = validate_labels_file(
        labels_path=synthetic_labels_file,
        label_col="crop_type",
        id_col="parcel_id",
        target_crs="EPSG:32643"
    )
    assert len(gdf) == 6
    assert "parcel_id" in gdf.columns
    assert "crop_type" in gdf.columns
    assert gdf.crs.to_string() == "EPSG:32643"


def test_validate_labels_reproject_from_wgs84(tmp_path):
    wgs_file = tmp_path / "wgs84_labels.geojson"
    gdf_wgs = gpd.GeoDataFrame({
        "crop": ["Paddy"],
        "id": [1],
        "geometry": [box(77.40, 8.65, 77.41, 8.66)]
    }, crs="EPSG:4326")
    gdf_wgs.to_file(str(wgs_file), driver="GeoJSON")

    gdf_projected = validate_labels_file(
        str(wgs_file),
        label_col="crop",
        id_col="id",
        target_crs="EPSG:32643"
    )
    assert gdf_projected.crs.to_string() == "EPSG:32643"


def test_validate_study_area():
    # Create polygon of roughly 25 sq. km (5km x 5km = 5000m x 5000m = 25,000,000 m2)
    large_poly = box(350000, 960000, 355000, 965000)
    gdf_large = gpd.GeoDataFrame({"geometry": [large_poly]}, crs="EPSG:32643")
    
    sq_km, meets = validate_study_area(gdf_large, min_area_sq_km=20.0)
    assert round(sq_km, 1) == 25.0
    assert meets is True

    # Small polygon of 5 sq km
    small_poly = box(350000, 960000, 352236, 962236)
    gdf_small = gpd.GeoDataFrame({"geometry": [small_poly]}, crs="EPSG:32643")
    sq_km_small, meets_small = validate_study_area(gdf_small, min_area_sq_km=20.0)
    assert round(sq_km_small, 1) == 5.0
    assert meets_small is False
