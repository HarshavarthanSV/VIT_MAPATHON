"""
Tests for Random Forest Training, Evaluation Metrics, and Feature Importance.
"""

import os
import pytest
import numpy as np
import pandas as pd
import joblib

from classification.train import train_crop_classifier, save_model_artifacts
from classification.predict import predict_crop_classes
from evaluation.metrics import calculate_model_metrics, export_metrics_json
from evaluation.confusion_matrix import generate_confusion_matrix
from evaluation.feature_importance import extract_feature_importance


def test_train_and_predict_random_forest():
    np.random.seed(42)
    feature_names = ["NDVI", "EVI", "SAVI", "NDWI", "B02", "B04", "B08"]
    
    # Create synthetic training set
    n_samples = 60
    X_train = pd.DataFrame(
        np.random.randn(n_samples, len(feature_names)),
        columns=feature_names
    )
    y_train = pd.Series(
        np.random.choice(["Paddy", "Banana", "Other"], size=n_samples)
    )

    model = train_crop_classifier(
        X_train, y_train,
        rf_params={"n_estimators": 20, "max_depth": 5, "random_state": 42}
    )

    assert set(model.classes_) == {"Banana", "Other", "Paddy"}

    # Test prediction
    X_test = pd.DataFrame(
        np.random.randn(10, len(feature_names)),
        columns=feature_names
    )
    preds, conf, probs = predict_crop_classes(model, X_test, expected_features=feature_names)

    assert len(preds) == 10
    assert len(conf) == 10
    assert probs.shape == (10, 3)
    assert np.all(conf >= 0.0) and np.all(conf <= 1.0)
    assert np.allclose(np.sum(probs, axis=1), 1.0)


def test_evaluation_metrics_and_confusion_matrix():
    y_true = ["Paddy", "Paddy", "Banana", "Other", "Banana"]
    y_pred = ["Paddy", "Other", "Banana", "Other", "Banana"]

    metrics = calculate_model_metrics(y_true, y_pred, labels=["Paddy", "Banana", "Other"])

    assert "overall" in metrics
    assert "accuracy" in metrics["overall"]
    assert metrics["overall"]["accuracy"] == 0.8  # 4 out of 5 correct
    assert "Paddy" in metrics["per_class"]
    assert "Banana" in metrics["per_class"]
    assert metrics["per_class"]["Banana"]["precision"] == 1.0

    cm_dict = generate_confusion_matrix(y_true, y_pred, labels=["Paddy", "Banana", "Other"])
    assert cm_dict["classes"] == ["Paddy", "Banana", "Other"]
    assert np.sum(cm_dict["raw_matrix"]) == 5


def test_feature_importance_and_artifact_saving(tmp_path):
    feature_names = ["NDVI", "EVI", "B08"]
    X = pd.DataFrame(np.random.rand(30, 3), columns=feature_names)
    y = pd.Series(np.random.choice(["Paddy", "Banana"], size=30))

    model = train_crop_classifier(X, y, rf_params={"n_estimators": 10, "random_state": 42})
    
    # Feature importance
    json_path = tmp_path / "feat_imp.json"
    imp_dict = extract_feature_importance(model, feature_names, str(json_path))
    assert len(imp_dict["features"]) == 3
    assert os.path.exists(str(json_path))

    # Artifact saving
    model_path = tmp_path / "model.joblib"
    meta_path = tmp_path / "metadata.json"
    save_model_artifacts(model, feature_names, str(model_path), str(meta_path))

    assert os.path.exists(str(model_path))
    assert os.path.exists(str(meta_path))

    # Verify reload
    loaded_model = joblib.load(str(model_path))
    assert list(loaded_model.classes_) == list(model.classes_)
