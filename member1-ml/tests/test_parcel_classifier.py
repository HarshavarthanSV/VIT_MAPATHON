"""
Tests for Parcel Inference, GeoJSON Export, and Crop Statistics Aggregation.
"""

import os
import json
import pytest
import geopandas as gpd

from preprocessing.feature_loader import FeatureLoader
from preprocessing.label_loader import LabelLoader
from preprocessing.dataset_builder import DatasetBuilder
from classification.train import train_crop_classifier
from classification.parcel_classifier import ParcelClassifier


def test_parcel_classifier_pipeline(synthetic_raster_environment, synthetic_labels_file, synthetic_parcels_file, tmp_path):
    # 1. Prepare features & model
    feature_loader = FeatureLoader(features_dir=synthetic_raster_environment["dir"])
    label_loader = LabelLoader(labels_path=synthetic_labels_file)
    builder = DatasetBuilder(feature_loader, label_loader, test_size=0.2, random_state=42)
    df = builder.build_dataset()
    X_train, _, _, y_train, _, _ = builder.create_spatial_splits(df)

    model = train_crop_classifier(X_train, y_train, rf_params={"n_estimators": 10, "random_state": 42})

    # 2. Parcel Classifier
    classifier = ParcelClassifier(
        model=model,
        feature_loader=feature_loader,
        feature_names=builder.feature_names,
        target_crs="EPSG:32643"
    )

    classified_gdf = classifier.classify_parcels(synthetic_parcels_file)

    assert len(classified_gdf) == 3
    assert "predicted_crop" in classified_gdf.columns
    assert "confidence" in classified_gdf.columns
    assert "area_sq_km" in classified_gdf.columns

    # 3. GeoJSON Export
    geojson_out = tmp_path / "classified_parcels.geojson"
    classifier.export_classified_geojson(classified_gdf, str(geojson_out))

    assert os.path.exists(str(geojson_out))
    exported_gdf = gpd.read_file(str(geojson_out))
    assert exported_gdf.crs.to_string() == "EPSG:4326"  # Must be WGS84 for Web GIS Leaflet compatibility
    assert "predicted_crop" in exported_gdf.columns
    assert "confidence" in exported_gdf.columns

    # 4. Crop Statistics Export
    stats_out = tmp_path / "crop_statistics.json"
    stats = classifier.compute_crop_statistics(classified_gdf, str(stats_out))

    assert os.path.exists(str(stats_out))
    assert "study_area_summary" in stats
    assert "crop_distribution" in stats
    assert stats["study_area_summary"]["total_parcels"] == 3
    assert "Paddy" in stats["crop_distribution"]
    assert "Banana" in stats["crop_distribution"]
    assert "Other" in stats["crop_distribution"]
