"""
Feature Selection and Pruning Module.
Phase 11 of the Crop Classification Upgrade Pipeline.
Implements variance filtering, correlation pruning, Random Forest MDI,
and permutation importance to identify the most discriminative, non-redundant feature subsets.
"""

from typing import List, Tuple, Dict, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance


def remove_low_variance_features(
    df: pd.DataFrame,
    feature_cols: List[str],
    threshold: float = 1e-5
) -> Tuple[List[str], List[str]]:
    """
    Identifies and removes constant and near-zero variance features.
    """
    variances = df[feature_cols].var()
    keep_cols = variances[variances > threshold].index.tolist()
    dropped_cols = [c for c in feature_cols if c not in keep_cols]
    return keep_cols, dropped_cols


def remove_collinear_features(
    df: pd.DataFrame,
    feature_cols: List[str],
    correlation_threshold: float = 0.985
) -> Tuple[List[str], List[str]]:
    """
    Prunes redundant features having pairwise correlation above threshold.
    Preserves the feature with higher overall variance.
    """
    corr_matrix = df[feature_cols].corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    to_drop = set()
    for col in upper_tri.columns:
        high_corr_partners = upper_tri.index[upper_tri[col] > correlation_threshold].tolist()
        for partner in high_corr_partners:
            if partner not in to_drop and col not in to_drop:
                # Keep the one with higher standard deviation
                var_col = df[col].var()
                var_partner = df[partner].var()
                if var_col >= var_partner:
                    to_drop.add(partner)
                else:
                    to_drop.add(col)

    kept_cols = [c for c in feature_cols if c not in to_drop]
    dropped_cols = list(to_drop)
    return kept_cols, dropped_cols


def rank_features_by_importance(
    X: pd.DataFrame,
    y: pd.Series,
    rf_model: Optional[RandomForestClassifier] = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Ranks features by Mean Decrease in Impurity (Gini Importance) using Random Forest.
    """
    if rf_model is None:
        rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=4,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        )
        rf_model.fit(X, y)

    importances = rf_model.feature_importances_
    ranks_df = pd.DataFrame({
        "feature": X.columns,
        "importance": importances
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    ranks_df["rank"] = np.arange(1, len(ranks_df) + 1)
    return ranks_df


def compute_permutation_importance(
    model: Any,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    n_repeats: int = 5,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Computes permutation importance on held-out validation data.
    Measures the decrease in model macro-F1 when a feature's values are randomly permuted.
    """
    result = permutation_importance(
        model, X_val, y_val,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring="f1_macro",
        n_jobs=-1
    )
    pi_df = pd.DataFrame({
        "feature": X_val.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std
    }).sort_values(by="importance_mean", ascending=False).reset_index(drop=True)

    return pi_df
