"""
Prediction Module
Handles inference and confidence estimation using the trained Random Forest model.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


def predict_crop_classes(
    model: RandomForestClassifier,
    X: pd.DataFrame,
    expected_features: Optional[List[str]] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Runs model inference on feature matrix X.
    
    Args:
        model: Trained RandomForestClassifier.
        X: Feature matrix.
        expected_features: List of required feature names to ensure alignment.
        
    Returns:
        Tuple of:
          - predictions: Array of predicted crop class strings
          - max_confidence: Array of maximum class probability scores (0.0 - 1.0)
          - all_probabilities: 2D array of probabilities for each class
    """
    if expected_features:
        missing = [f for f in expected_features if f not in X.columns]
        if missing:
            raise ValueError(f"Input features missing required model columns: {missing}")
        X_aligned = X[expected_features].copy()
    else:
        X_aligned = X.copy()

    # Fill NaNs with 0.0 if any remaining at inference time
    X_aligned = X_aligned.fillna(0.0)

    predictions = model.predict(X_aligned)
    probabilities = model.predict_proba(X_aligned)
    max_confidence = np.max(probabilities, axis=1)

    return predictions, max_confidence, probabilities
