"""
Feature Importance Module
Extracts relative spectral and temporal band importances from the trained Random Forest model.
Exports numerical rankings and visual bar charts.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def extract_feature_importance(
    model: RandomForestClassifier,
    feature_names: List[str],
    output_json_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts Gini-based feature importances from the fitted Random Forest.
    
    Args:
        model: Fitted RandomForestClassifier.
        feature_names: List of feature names matching model input columns.
        output_json_path: Optional destination path for JSON export.
        
    Returns:
        Dictionary mapping feature name to importance score, sorted descending.
    """
    if len(model.feature_importances_) != len(feature_names):
        raise ValueError(
            f"Mismatch between number of model features ({len(model.feature_importances_)}) "
            f"and provided feature names ({len(feature_names)})."
        )

    importances = model.feature_importances_
    sorted_indices = np.argsort(importances)[::-1]

    ranked_features = []
    for rank, idx in enumerate(sorted_indices, 1):
        ranked_features.append({
            "rank": rank,
            "feature": feature_names[idx],
            "importance": round(float(importances[idx]), 6)
        })

    importance_dict = {
        "features": ranked_features,
        "n_features": len(feature_names),
        "top_feature": ranked_features[0]["feature"] if ranked_features else None
    }

    if output_json_path:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(importance_dict, f, indent=2)
        logger.info(f"Saved feature importance JSON to: {output_json_path}")

    return importance_dict


def plot_feature_importance(
    importance_dict: Dict[str, Any],
    output_path: str,
    top_n: int = 15,
    title: str = "Random Forest Feature Importance (MDI)"
) -> str:
    """
    Renders and saves a horizontal bar chart of the top N most discriminative features.
    
    Args:
        importance_dict: Dictionary returned by extract_feature_importance.
        output_path: Path to output PNG image.
        top_n: Number of top features to include in visualization.
        title: Plot title.
        
    Returns:
        Output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    items = importance_dict["features"][:top_n]
    names = [item["feature"] for item in items][::-1]
    scores = [item["importance"] for item in items][::-1]

    fig, ax = plt.subplots(figsize=(8, max(5, len(names) * 0.4)))
    bars = ax.barh(names, scores, color="#2e7d32", edgecolor="#1b5e20", alpha=0.85)

    ax.set_xlabel("Mean Decrease in Impurity (Gini Importance)")
    ax.set_title(title, fontsize=12, pad=12)
    ax.grid(axis="x", linestyle="--", alpha=0.6)

    # Value labels on bars
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{width:.4f}", ha="left", va="center", fontsize=9, color="#1b5e20"
        )

    fig.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    logger.info(f"Saved feature importance plot to: {output_path}")
    return output_path
