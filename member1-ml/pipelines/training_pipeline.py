"""
Member 1 — AI / ML & Backend Systems
Module: Dedicated Offline Model Training Pipeline
Component: Training Pipeline (Decoupled from Inference)

Historical Verified Labels + Multi-Temporal Features
        ↓
Feature Preprocessing & Validation
        ↓
Stratified K-Fold CV & Holdout Test
        ↓
Versioned Model Artifact (models/crop_classifier/{version}/)
        ↓
Register in Model Registry as Candidate / Production

CRITICAL: This pipeline is executed ONLY during scheduled retraining or verified model maintenance.
It is NEVER called during normal satellite data ingestion or inference.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Ensure paths
curr_dir = os.path.dirname(os.path.abspath(__file__))
member1_dir = os.path.dirname(curr_dir)
repo_root = os.path.abspath(os.path.join(member1_dir, ".."))
if member1_dir not in sys.path:
    sys.path.insert(0, member1_dir)
if os.path.join(member1_dir, "models") not in sys.path:
    sys.path.insert(0, os.path.join(member1_dir, "models"))

from model_registry import ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrainingPipeline")


class ModelTrainingPipeline:
    """
    Standardized, reproducible model training pipeline.
    Produces versioned artifacts and registers them into ModelRegistry.
    """

    def __init__(
        self,
        registry_path: Optional[str] = None,
        models_root: Optional[str] = None
    ):
        self.models_root = models_root or os.path.join(repo_root, "models", "crop_classifier")
        self.registry = ModelRegistry(registry_path)

    def train_model_version(
        self,
        dataset_csv: str,
        model_version: str,
        training_start_date: str,
        training_end_date: str,
        training_dataset_version: str,
        status: str = "candidate",
        notes: str = "",
        n_estimators: int = 200,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Executes offline training on verified dataset, validates metrics,
        saves artifact to models/crop_classifier/{model_version}/, and registers model.
        """
        logger.info("=" * 70)
        logger.info(f"STARTING OFFLINE MODEL TRAINING FOR VERSION: {model_version}")
        logger.info(f"Dataset: {dataset_csv} (Version: {training_dataset_version})")
        logger.info("=" * 70)

        if not os.path.exists(dataset_csv):
            raise FileNotFoundError(f"Training dataset not found: {dataset_csv}")

        df = pd.read_csv(dataset_csv)
        meta_cols = ["parcel_id", "crop_class", "crop_name"]
        feature_cols = [c for c in df.columns if c not in meta_cols]

        X = df[feature_cols].copy().fillna(df[feature_cols].median())
        y = df["crop_name"].copy()

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=random_state, stratify=y
        )

        # 5-Fold Stratified Cross Validation
        rf_cv = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=15, min_samples_split=4,
            min_samples_leaf=2, class_weight="balanced", random_state=random_state, n_jobs=-1
        )
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        cv_res = cross_validate(rf_cv, X_train, y_train, cv=skf, scoring=["accuracy", "f1_macro"])

        cv_acc_mean = float(np.mean(cv_res["test_accuracy"]))
        cv_f1_mean = float(np.mean(cv_res["test_f1_macro"]))

        # Train final model
        rf_final = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=15, min_samples_split=4,
            min_samples_leaf=2, class_weight="balanced", random_state=random_state, n_jobs=-1
        )
        rf_final.fit(X_train, y_train)

        # Holdout test metrics
        y_pred = rf_final.predict(X_test)
        classes = list(rf_final.classes_)

        test_acc = float(accuracy_score(y_test, y_pred))
        test_f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        test_prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        test_rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))

        # Per-class metrics
        prec_pc = precision_score(y_test, y_pred, labels=classes, average=None, zero_division=0)
        rec_pc = recall_score(y_test, y_pred, labels=classes, average=None, zero_division=0)
        f1_pc = f1_score(y_test, y_pred, labels=classes, average=None, zero_division=0)

        per_class_dict = {}
        for i, c in enumerate(classes):
            per_class_dict[c] = {
                "precision": round(float(prec_pc[i]), 4),
                "recall": round(float(rec_pc[i]), 4),
                "f1_score": round(float(f1_pc[i]), 4),
                "support": int(np.sum(y_test == c))
            }

        cm = confusion_matrix(y_test, y_pred, labels=classes)

        val_metrics = {
            "overall": {
                "accuracy": round(test_acc, 4),
                "test_accuracy": round(test_acc, 4),
                "test_f1_macro": round(test_f1_macro, 4),
                "test_precision_macro": round(test_prec_macro, 4),
                "test_recall_macro": round(test_rec_macro, 4),
                "cv_5fold_accuracy_mean": round(cv_acc_mean, 4),
                "cv_5fold_f1_macro_mean": round(cv_f1_mean, 4),
                "n_train_samples": len(X_train),
                "n_test_samples": len(X_test),
                "n_total_parcels": len(df),
                "n_features": len(feature_cols)
            },
            "per_class": per_class_dict,
            "confusion_matrix": {
                "classes": classes,
                "raw_matrix": cm.tolist()
            }
        }

        # Save versioned artifact
        version_dir = os.path.join(self.models_root, model_version)
        os.makedirs(version_dir, exist_ok=True)
        artifact_path = os.path.join(version_dir, "crop_classifier.joblib")
        joblib.dump(rf_final, artifact_path)
        logger.info(f"Saved versioned model artifact to: {artifact_path}")

        # Relative path for registry
        rel_artifact_path = os.path.relpath(artifact_path, repo_root).replace("\\", "/")

        # Register in model registry
        registered_entry = self.registry.register_model(
            model_version=model_version,
            artifact_path=rel_artifact_path,
            training_start_date=training_start_date,
            training_end_date=training_end_date,
            training_dataset_version=training_dataset_version,
            features_used=feature_cols,
            classes=classes,
            validation_metrics=val_metrics,
            status=status,
            notes=notes
        )

        logger.info(f"Model {model_version} successfully trained and registered (Status: {status})")
        logger.info(f"Test Accuracy: {test_acc:.2%}, Macro-F1: {test_f1_macro:.2%}")
        logger.info("=" * 70)
        return registered_entry


if __name__ == "__main__":
    pipeline = ModelTrainingPipeline()
    # Can be run to train candidate versions
