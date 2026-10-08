"""
Tests for Label Loader and Crop Class Normalization.
"""

import os
import pytest
import geopandas as gpd
from shapely.geometry import box

from preprocessing.label_loader import LabelLoader
from preprocessing.validation import DataNotAvailableError


def test_label_loader_missing_file():
    loader = LabelLoader(labels_path="missing_labels.geojson")
    with pytest.raises(DataNotAvailableError):
        loader.load_and_normalize()


def test_label_loader_normalization(tmp_path):
    labels_file = tmp_path / "raw_labels.geojson"
    gdf = gpd.GeoDataFrame({
        "parcel_id": ["p1", "p2", "p3", "p4"],
        "crop_type": ["paddy", "RICE", "plantain", "builtup"],
        "geometry": [
            box(350000, 960000, 350100, 960100),
            box(350100, 960000, 350200, 960100),
            box(350200, 960000, 350300, 960100),
            box(350300, 960000, 350400, 960100),
        ]
    }, crs="EPSG:32643")
    gdf.to_file(str(labels_file), driver="GeoJSON")

    loader = LabelLoader(labels_path=str(labels_file))
    cleaned_gdf = loader.load_and_normalize()

    classes = cleaned_gdf["crop_type"].tolist()
    assert classes[0] == "Paddy"
    assert classes[1] == "Paddy"
    assert classes[2] == "Banana"
    assert classes[3] == "Other"

    # Verify area computed
    assert "area_ha" in cleaned_gdf.columns
    assert "area_sq_km" in cleaned_gdf.columns
    assert cleaned_gdf["area_ha"].iloc[0] == pytest.approx(1.0, 0.01) # 100m x 100m = 10,000 m2 = 1 ha
