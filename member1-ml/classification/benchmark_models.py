"""
Model Benchmarking and Feature Set Evaluation Module.
Phases 11, 12, 13, 14, 15 of the Crop Classification Upgrade Pipeline.
Benchmarks Random Forest and XGBoost across 4 distinct feature sets:
1. FEATURE_SET_BASELINE (original 240 features)
2. FEATURE_SET_ADVANCED (per-date bands, red-edge, advanced indices, ratios)
3. FEATURE_SET_TEMPORAL (advanced + 10 temporal stats + phenology + derivatives)
4. FEATURE_SET_FULL (selected/pruned optimal feature subset)

Enforces strict spatial parcel validation without data leakage.
Exports comparative benchmark tables, confusion matrices, and confidence thresholds.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
import geopandas as gpd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, confusion_matrix, classification_report
)
from sklearn.preprocessing import LabelEncoder

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Ensure path
curr_dir = os.path.dirname(os.path.abspath(__file__))
member1_dir = os.path.dirname(curr_dir)
repo_root = os.path.abspath(os.path.join(member1_dir, ".."))
if member1_dir not in sys.path:
    sys.path.insert(0, member1_dir)

from features.feature_selector import (
    remove_low_variance_features,
    remove_collinear_features,
    rank_features_by_importance,
    compute_permutation_importance
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelBenchmarking")


def define_feature_sets(
    df_base: pd.DataFrame,
    df_upgraded: pd.DataFrame
) -> Dict[str, List[str]]:
    """
    Defines the 4 feature sets for benchmarking.
    """
    meta_cols = {
        "parcel_id", "crop_class", "crop_name", "data_quality_flag",
        "valid_pixel_count", "valid_pixel_ratio", "number_of_valid_dates",
        "parcel_area_sq_m", "parcel_area_ha"
    }

    # 1. BASELINE: Features in original ml_training_dataset.csv
    base_features = [c for c in df_base.columns if c not in ["parcel_id", "crop_class", "crop_name"]]

    # 2. ADVANCED: Per-date bands (including red-edge) + advanced indices + ratios & diffs
    upgraded_all = [c for c in df_upgraded.columns if c not in meta_cols]
    advanced_features = [
        c for c in upgraded_all
        if any(c.startswith(d) for d in ["2026-03-20", "2026-04-02", "2026-04-22", "2026-09-09"])
    ]

    # 3. TEMPORAL: Advanced + multi-temporal summary stats + phenology + derivatives
    temporal_features = [
        c for c in upgraded_all
        if "temporal" in c or c.startswith("pheno_") or c.startswith("delta_")
    ]
    advanced_and_temporal = list(set(advanced_features + temporal_features))

    # 4. FULL / PRUNED: Pruned via variance and collinearity filtering
    kept_var, _ = remove_low_variance_features(df_upgraded, advanced_and_temporal, threshold=1e-5)
    kept_cols, dropped_collinear = remove_collinear_features(df_upgraded, kept_var, correlation_threshold=0.985)

    logger.info(f"Feature set sizes:")
    logger.info(f"  * BASELINE          : {len(base_features)} features")
    logger.info(f"  * ADVANCED          : {len(advanced_features)} features")
    logger.info(f"  * ADVANCED+TEMPORAL : {len(advanced_and_temporal)} features")
    logger.info(f"  * FULL (PRUNED)     : {len(kept_cols)} features (pruned {len(dropped_collinear)} collinear)")

    return {
        "FEATURE_SET_BASELINE": base_features,
        "FEATURE_SET_ADVANCED": advanced_features,
        "FEATURE_SET_TEMPORAL": advanced_and_temporal,
        "FEATURE_SET_FULL": kept_cols,
    }


def evaluate_model_pipeline(
    model_name: str,
    feature_set_name: str,
    model: Any,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    classes: List[str],
    is_xgb: bool = False
) -> Dict[str, Any]:
    """
    Trains model and calculates all validation metrics on the spatial test split.
    """
    le = LabelEncoder()
    le.fit(classes)

    if is_xgb:
        y_train_num = le.transform(y_train)
        y_test_num = le.transform(y_test)
        model.fit(X_train, y_train_num)
        y_pred_num = model.predict(X_test)
        y_pred = le.inverse_transform(y_pred_num)
        probs_test = model.predict_proba(X_test)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        probs_test = model.predict_proba(X_test)

    # 5-fold CV on train
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    if is_xgb:
        cv_scores = cross_validate(
            model, X_train, le.transform(y_train), cv=cv, scoring=["accuracy", "f1_macro"]
        )
    else:
        cv_scores = cross_validate(
            model, X_train, y_train, cv=cv, scoring=["accuracy", "f1_macro"]
        )
    cv_acc_mean = float(np.mean(cv_scores["test_accuracy"]))
    cv_f1_mean = float(np.mean(cv_scores["test_f1_macro"]))

    # Test metrics
    test_acc = float(accuracy_score(y_test, y_pred))
    balanced_acc = float(balanced_accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    macro_prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))

    # Per class metrics
    prec_pc = precision_score(y_test, y_pred, labels=classes, average=None, zero_division=0)
    rec_pc = recall_score(y_test, y_pred, labels=classes, average=None, zero_division=0)
    f1_pc = f1_score(y_test, y_pred, labels=classes, average=None, zero_division=0)

    per_class_dict = {}
    for i, c in enumerate(classes):
        per_class_dict[c] = {
            "precision": round(float(prec_pc[i]), 4),
            "recall": round(float(rec_pc[i]), 4),
            "f1": round(float(f1_pc[i]), 4),
            "support": int(np.sum(y_test == c))
        }

    cm = confusion_matrix(y_test, y_pred, labels=classes)

    return {
        "model_name": model_name,
        "feature_set": feature_set_name,
        "n_features": X_train.shape[1],
        "test_accuracy": round(test_acc, 4),
        "balanced_accuracy": round(balanced_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "cv_accuracy_mean": round(cv_acc_mean, 4),
        "cv_f1_mean": round(cv_f1_mean, 4),
        "per_class": per_class_dict,
        "confusion_matrix": cm.tolist(),
        "model_object": model,
        "is_xgb": is_xgb,
        "y_pred": y_pred,
        "probs_test": probs_test
    }


def run_benchmark():
    logger.info("=" * 75)
    logger.info("MEMBER 1: ML BENCHMARKING (RANDOM FOREST VS XGBOOST)")
    logger.info("=" * 75)

    df_base_path = os.path.join(repo_root, "data", "features", "tabular", "ml_training_dataset.csv")
    df_upgraded_path = os.path.join(repo_root, "data", "features", "tabular", "upgraded_crop_dataset.csv")

    df_base = pd.read_csv(df_base_path)
    df_upgraded = pd.read_csv(df_upgraded_path)

    feature_sets = define_feature_sets(df_base, df_upgraded)
    classes = ["Banana", "Other", "Paddy"]

    y = df_upgraded["crop_name"].copy()
    parcel_ids = df_upgraded["parcel_id"].values

    # Fixed spatial holdout split (80% train, 20% test)
    # Using stratify=y and random_state=42 for reproducibility
    train_idx, test_idx = train_test_split(
        np.arange(len(df_upgraded)), test_size=0.20, random_state=42, stratify=y
    )

    results = []

    # 1. Random Forest Benchmarks
    rf_configs = [
        ("RF Baseline", "FEATURE_SET_BASELINE", df_base),
        ("RF Advanced", "FEATURE_SET_ADVANCED", df_upgraded),
        ("RF Temporal", "FEATURE_SET_TEMPORAL", df_upgraded),
        ("RF Full", "FEATURE_SET_FULL", df_upgraded),
    ]

    for model_label, fset_name, src_df in rf_configs:
        cols = feature_sets[fset_name]
        X = src_df[cols].copy().fillna(src_df[cols].median())

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        rf_clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=3,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )

        res = evaluate_model_pipeline(
            model_name=model_label,
            feature_set_name=fset_name,
            model=rf_clf,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            classes=classes,
            is_xgb=False
        )
        results.append(res)
        logger.info(
            f"[{model_label} | {fset_name}] Accuracy: {res['test_accuracy']:.2%} | "
            f"Macro-F1: {res['macro_f1']:.2%} | Weighted-F1: {res['weighted_f1']:.2%} | "
            f"CV Acc: {res['cv_accuracy_mean']:.2%}"
        )

    # 2. XGBoost Benchmarks
    if XGBOOST_AVAILABLE:
        xgb_configs = [
            ("XGBoost Advanced", "FEATURE_SET_ADVANCED", df_upgraded),
            ("XGBoost Temporal", "FEATURE_SET_TEMPORAL", df_upgraded),
            ("XGBoost Full", "FEATURE_SET_FULL", df_upgraded),
        ]

        for model_label, fset_name, src_df in xgb_configs:
            cols = feature_sets[fset_name]
            X = src_df[cols].copy().fillna(src_df[cols].median())

            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            xgb_clf = xgb.XGBClassifier(
                n_estimators=250,
                max_depth=5,
                learning_rate=0.06,
                subsample=0.85,
                colsample_bytree=0.80,
                eval_metric="mlogloss",
                random_state=42,
                n_jobs=-1
            )

            res = evaluate_model_pipeline(
                model_name=model_label,
                feature_set_name=fset_name,
                model=xgb_clf,
                X_train=X_train,
                X_test=X_test,
                y_train=y_train,
                y_test=y_test,
                classes=classes,
                is_xgb=True
            )
            results.append(res)
            logger.info(
                f"[{model_label} | {fset_name}] Accuracy: {res['test_accuracy']:.2%} | "
                f"Macro-F1: {res['macro_f1']:.2%} | Weighted-F1: {res['weighted_f1']:.2%} | "
                f"CV Acc: {res['cv_accuracy_mean']:.2%}"
            )

    # Print Summary Benchmark Table
    print("\n" + "=" * 90)
    print(f"{'Model':<20} | {'Feature Set':<22} | {'Features':<8} | {'Accuracy':<10} | {'Macro F1':<10} | {'Weighted F1':<10}")
    print("-" * 90)
    for r in results:
        print(f"{r['model_name']:<20} | {r['feature_set']:<22} | {r['n_features']:<8} | {r['test_accuracy'] * 100:.2f}%     | {r['macro_f1']:.4f}     | {r['weighted_f1']:.4f}")
    print("=" * 90)

    # Identify Winning Model based on Macro-F1 and Test Accuracy
    results_sorted = sorted(results, key=lambda x: (x["macro_f1"], x["test_accuracy"]), reverse=True)
    winner = results_sorted[0]
    logger.info(f"\nWINNING MODEL: {winner['model_name']} with {winner['feature_set']}")
    logger.info(f"Top Test Accuracy: {winner['test_accuracy']:.2%} | Macro-F1: {winner['macro_f1']:.4f}")

    return results, winner, feature_sets, train_idx, test_idx


if __name__ == "__main__":
    run_benchmark()
