"""
Model Evaluation Metrics Module
Dynamically computes multi-class classification metrics: Accuracy, Precision, Recall, and F1-score.
Strictly calculates metrics from actual model predictions. No hardcoding permitted.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

logger = logging.getLogger(__name__)


def calculate_model_metrics(
    y_true: Any,
    y_pred: Any,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes comprehensive evaluation metrics dynamically from predictions.
    
    Args:
        y_true: Ground truth class labels array or series.
        y_pred: Predicted class labels array.
        labels: Optional ordered list of target class labels.
        
    Returns:
        Dictionary containing overall and per-class metrics.
    """
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    if len(y_true_arr) == 0:
        raise ValueError("Cannot calculate metrics on empty ground truth.")

    target_labels = labels or sorted(list(np.unique(np.concatenate([y_true_arr, y_pred_arr]))))

    # Overall metrics
    accuracy = float(accuracy_score(y_true_arr, y_pred_arr))
    precision_macro = float(precision_score(y_true_arr, y_pred_arr, labels=target_labels, average="macro", zero_division=0))
    precision_weighted = float(precision_score(y_true_arr, y_pred_arr, labels=target_labels, average="weighted", zero_division=0))
    recall_macro = float(recall_score(y_true_arr, y_pred_arr, labels=target_labels, average="macro", zero_division=0))
    recall_weighted = float(recall_score(y_true_arr, y_pred_arr, labels=target_labels, average="weighted", zero_division=0))
    f1_macro = float(f1_score(y_true_arr, y_pred_arr, labels=target_labels, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true_arr, y_pred_arr, labels=target_labels, average="weighted", zero_division=0))

    # Per-class metrics
    prec_per_class = precision_score(y_true_arr, y_pred_arr, labels=target_labels, average=None, zero_division=0)
    rec_per_class = recall_score(y_true_arr, y_pred_arr, labels=target_labels, average=None, zero_division=0)
    f1_per_class = f1_score(y_true_arr, y_pred_arr, labels=target_labels, average=None, zero_division=0)

    per_class_dict = {}
    for i, cls_name in enumerate(target_labels):
        support = int(np.sum(y_true_arr == cls_name))
        per_class_dict[cls_name] = {
            "precision": round(float(prec_per_class[i]), 4),
            "recall": round(float(rec_per_class[i]), 4),
            "f1_score": round(float(f1_per_class[i]), 4),
            "support": support
        }

    metrics = {
        "overall": {
            "accuracy": round(accuracy, 4),
            "precision_macro": round(precision_macro, 4),
            "precision_weighted": round(precision_weighted, 4),
            "recall_macro": round(recall_macro, 4),
            "recall_weighted": round(recall_weighted, 4),
            "f1_score_macro": round(f1_macro, 4),
            "f1_score_weighted": round(f1_weighted, 4),
            "total_test_samples": len(y_true_arr)
        },
        "per_class": per_class_dict
    }

    logger.info(
        f"Model Evaluation: Accuracy={accuracy:.4f}, F1-macro={f1_macro:.4f}, "
        f"Precision-macro={precision_macro:.4f}, Recall-macro={recall_macro:.4f}"
    )

    return metrics


def export_metrics_json(metrics: Dict[str, Any], output_path: str) -> str:
    """
    Exports computed metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary.
        output_path: Path to output JSON.
        
    Returns:
        Output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved model metrics to: {output_path}")
    return output_path
