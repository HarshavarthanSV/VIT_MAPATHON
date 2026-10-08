"""
Tests for Dataset Builder and Spatial Group Splitting.
Verifies prevention of spatial autocorrelation leakage.
"""

import pytest
import numpy as np

from preprocessing.feature_loader import FeatureLoader
from preprocessing.label_loader import LabelLoader
from preprocessing.dataset_builder import DatasetBuilder


def test_dataset_builder_spatial_split(synthetic_raster_environment, synthetic_labels_file):
    feature_loader = FeatureLoader(features_dir=synthetic_raster_environment["dir"])
    label_loader = LabelLoader(labels_path=synthetic_labels_file)

    builder = DatasetBuilder(
        feature_loader=feature_loader,
        label_loader=label_loader,
        test_size=0.33,
        val_size=0.0,
        random_state=42
    )
    df = builder.build_dataset()

    assert len(df) == 6
    assert "parcel_id" in df.columns
    assert "crop_type" in df.columns
    assert "NDVI" in df.columns
    assert len(builder.feature_names) >= 4

    # Perform split
    X_train, X_val, X_test, y_train, y_val, y_test = builder.create_spatial_splits(df)

    assert len(X_train) > 0
    assert len(X_test) > 0

    # Critical Check: Verify NO parcel group overlap between train and test indices
    train_parcels = set(df.loc[X_train.index, "parcel_id"])
    test_parcels = set(df.loc[X_test.index, "parcel_id"])

    assert len(train_parcels.intersection(test_parcels)) == 0, (
        f"Spatial leakage detected! Parcels {train_parcels.intersection(test_parcels)} present in both train and test."
    )
