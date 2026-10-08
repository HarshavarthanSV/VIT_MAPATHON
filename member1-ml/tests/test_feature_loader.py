"""
Tests for Feature Loader and Multi-temporal Discovery.
"""

import os
import pytest
from shapely.geometry import box

from preprocessing.feature_loader import FeatureLoader
from preprocessing.validation import DataNotAvailableError


def test_feature_loader_missing_dir():
    loader = FeatureLoader(features_dir="non_existent_folder")
    with pytest.raises(DataNotAvailableError):
        loader.discover_features()


def test_feature_loader_discovery_and_extraction(synthetic_raster_environment):
    loader = FeatureLoader(
        features_dir=synthetic_raster_environment["dir"],
        expected_crs="EPSG:32643"
    )
    discovered = loader.discover_features()
    
    # Check that core bands and indices are identified
    assert "B02" in discovered
    assert "B08" in discovered
    assert "NDVI" in discovered
    assert "SAVI" in discovered

    # Extract for a polygon inside the raster extent
    sample_poly = box(350100, 959800, 350200, 959900)
    feat_dict = loader.extract_polygon_features(sample_poly, aggregation="mean")

    assert len(feat_dict) > 0
    assert "NDVI" in feat_dict
    assert not pytest.approx(feat_dict["NDVI"]) == 0.0
