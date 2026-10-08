"""
Random Forest Training Module
Trains the core crop classifier (Paddy vs. Banana vs. Other) using scikit-learn.
Serializes trained model artifact (.joblib) and comprehensive training metadata.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
import joblib

logger = logging.getLogger(__name__)


def train_crop_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    rf_params: Optional[Dict[str, Any]] = None
) -> RandomForestClassifier:
    """
    Trains a Random Forest classifier using scikit-learn.
    
    Args:
        X_train: Training features matrix.
        y_train: Target class labels.
        rf_params: Hyperparameters for RandomForestClassifier.
        
    Returns:
        Fitted RandomForestClassifier model.
    """
    default_params = {
        "n_estimators": 150,
        "max_depth": 16,
        "min_samples_split": 4,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": -1
    }
    
    params = default_params.copy()
    if rf_params:
        params.update(rf_params)

    logger.info(f"Training RandomForestClassifier on {len(X_train)} samples with params: {params}")

    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    logger.info(f"Model trained successfully. Detected classes: {list(model.classes_)}")
    return model


def save_model_artifacts(
    model: RandomForestClassifier,
    feature_names: List[str],
    model_path: str,
    metadata_path: str,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Saves the trained model to a joblib file and exports a JSON metadata descriptor.
    
    Args:
        model: Trained RandomForestClassifier.
        feature_names: List of feature names used during training.
        model_path: Path to save the .joblib file.
        metadata_path: Path to save the metadata JSON file.
        extra_metadata: Additional metrics or run info to record.
        
    Returns:
        Metadata dictionary.
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

    # 1. Save model weights
    joblib.dump(model, model_path)
    logger.info(f"Saved trained Random Forest model artifact to: {model_path}")

    # 2. Compile model metadata
    metadata = {
        "model_type": "RandomForestClassifier",
        "classes": [str(c) for c in model.classes_],
        "n_classes": len(model.classes_),
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "hyperparameters": {
            k: v for k, v in model.get_params().items()
            if isinstance(v, (int, float, str, bool)) or v is None
        },
        "training_timestamp": datetime.utcnow().isoformat() + "Z",
        "framework_versions": {
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "numpy": np.__version__,
        }
    }

    if extra_metadata:
        metadata.update(extra_metadata)

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved model metadata descriptor to: {metadata_path}")
    return metadata
