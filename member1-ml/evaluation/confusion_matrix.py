"""
Confusion Matrix Module
Computes multi-class confusion matrix and generates visual heatmaps.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def generate_confusion_matrix(
    y_true: Any,
    y_pred: Any,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Computes confusion matrix as raw numbers and normalized percentages.
    
    Args:
        y_true: True class labels.
        y_pred: Predicted class labels.
        labels: Ordered list of class labels.
        
    Returns:
        Dictionary with confusion matrix rows, columns, and numeric matrix.
    """
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    target_labels = labels or sorted(list(np.unique(np.concatenate([y_true_arr, y_pred_arr]))))

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=target_labels)

    # Normalize by true label row sums (recall-oriented)
    with np.errstate(divide="ignore", invalid="ignore"):
        cm_norm = np.true_divide(cm, cm.sum(axis=1, keepdims=True))
        cm_norm = np.nan_to_num(cm_norm)

    result = {
        "classes": target_labels,
        "raw_matrix": cm.tolist(),
        "normalized_matrix": np.round(cm_norm, 4).tolist(),
    }
    return result


def plot_confusion_matrix(
    cm_dict: Dict[str, Any],
    output_path: str,
    title: str = "Crop Classification Confusion Matrix"
) -> str:
    """
    Renders and saves a confusion matrix heatmap using matplotlib.
    
    Args:
        cm_dict: Output dictionary from generate_confusion_matrix.
        output_path: Path to output PNG image.
        title: Title of plot.
        
    Returns:
        Output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    classes = cm_dict["classes"]
    raw_matrix = np.array(cm_dict["raw_matrix"])
    norm_matrix = np.array(cm_dict["normalized_matrix"])

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(norm_matrix, interpolation="nearest", cmap=plt.cm.Greens, vmin=0, vmax=1)
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Normalized Rate", rotation=-90, va="bottom")

    ax.set(
        xticks=np.arange(len(classes)),
        yticks=np.arange(len(classes)),
        xticklabels=classes,
        yticklabels=classes,
        title=title,
        ylabel="True Ground Truth Class",
        xlabel="Predicted Crop Class"
    )

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate cells with raw count and percentage
    thresh = 0.5
    for i in range(len(classes)):
        for j in range(len(classes)):
            val_norm = norm_matrix[i, j]
            val_raw = raw_matrix[i, j]
            text_color = "white" if val_norm > thresh else "black"
            ax.text(
                j, i, f"{val_raw}\n({val_norm:.1%})",
                ha="center", va="center", color=text_color, fontsize=10
            )

    fig.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    logger.info(f"Saved confusion matrix plot to: {output_path}")
    return output_path
