"""
Member 1 — AI / ML & Backend Systems
Module: Model Versioning & Registry Management
Handles model registry, version tracking, model comparison, drift detection, and candidate evaluation.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ModelRegistry")


class ModelRegistry:
    """
    Manages production, candidate, and retired models for the agricultural monitoring system.
    Strictly guarantees that only one model is marked 'production' at any time.
    """

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            # Resolve relative to repo root
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(curr_dir, "..", ".."))
            self.registry_path = os.path.join(repo_root, "models", "crop_classifier", "model_registry.json")
        else:
            self.registry_path = registry_path

        self._ensure_registry_exists()

    def _ensure_registry_exists(self) -> None:
        """Creates an initial registry if none exists."""
        if not os.path.exists(self.registry_path):
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            initial_data = {
                "registry_name": "VIT_MAPATHON Crop Classification Model Registry",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "production_model_version": None,
                "models": []
            }
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_registry(self) -> Dict[str, Any]:
        """Loads the registry JSON document."""
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_registry(self, data: Dict[str, Any]) -> None:
        """Persists the registry JSON document."""
        data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_production_model_meta(self) -> Dict[str, Any]:
        """Returns metadata for the currently active production model."""
        registry = self.load_registry()
        prod_ver = registry.get("production_model_version")
        for m in registry.get("models", []):
            if m.get("model_version") == prod_ver and m.get("status") == "production":
                return m
        # Fallback to any model with status == production
        for m in registry.get("models", []):
            if m.get("status") == "production":
                return m
        raise FileNotFoundError("No active production model found in registry.")

    def load_production_model(self) -> Tuple[Any, Dict[str, Any]]:
        """Loads the production model object (e.g. RandomForest) and its metadata."""
        meta = self.get_production_model_meta()
        artifact_path = meta.get("artifact_path")
        
        # Resolve path
        if not os.path.isabs(artifact_path):
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(curr_dir, "..", ".."))
            full_path = os.path.join(repo_root, artifact_path)
        else:
            full_path = artifact_path

        if not os.path.exists(full_path):
            # Check fallback in member1-ml/models
            fallback = os.path.join(os.path.dirname(self.registry_path), "..", "..", "member1-ml", "models", "crop_classifier.joblib")
            if os.path.exists(fallback):
                full_path = fallback
            else:
                raise FileNotFoundError(f"Production model artifact not found at: {full_path}")

        logger.info(f"Loading production model {meta['model_version']} from {full_path}")
        model = joblib.load(full_path)
        return model, meta

    def get_model_by_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Returns metadata for a specific model version."""
        registry = self.load_registry()
        for m in registry.get("models", []):
            if m.get("model_version") == version:
                return m
        return None

    def register_model(
        self,
        model_version: str,
        artifact_path: str,
        training_start_date: str,
        training_end_date: str,
        training_dataset_version: str,
        features_used: List[str],
        classes: List[str],
        validation_metrics: Dict[str, Any],
        status: str = "candidate",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Registers a new model version (candidate or production)."""
        registry = self.load_registry()

        # Check if version exists
        for m in registry.get("models", []):
            if m.get("model_version") == model_version:
                logger.warning(f"Model version {model_version} already registered. Updating entry.")
                m["artifact_path"] = artifact_path
                m["training_start_date"] = training_start_date
                m["training_end_date"] = training_end_date
                m["training_dataset_version"] = training_dataset_version
                m["features_used"] = features_used
                m["n_features"] = len(features_used)
                m["classes"] = classes
                m["validation_metrics"] = validation_metrics
                m["status"] = status
                m["notes"] = notes
                m["updated_at"] = datetime.utcnow().isoformat() + "Z"
                if status == "production":
                    registry["production_model_version"] = model_version
                    # Demote any other production model
                    for other in registry.get("models", []):
                        if other.get("model_version") != model_version and other.get("status") == "production":
                            other["status"] = "retired"
                self.save_registry(registry)
                return m

        new_entry = {
            "model_version": model_version,
            "model_name": f"CropClassifier_{model_version}",
            "artifact_path": artifact_path,
            "training_start_date": training_start_date,
            "training_end_date": training_end_date,
            "training_dataset_version": training_dataset_version,
            "features_used": features_used,
            "n_features": len(features_used),
            "classes": classes,
            "validation_metrics": validation_metrics,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "notes": notes
        }

        if status == "production":
            registry["production_model_version"] = model_version
            for other in registry.get("models", []):
                if other.get("status") == "production":
                    other["status"] = "retired"

        registry["models"].append(new_entry)
        self.save_registry(registry)
        logger.info(f"Registered model {model_version} with status '{status}'.")
        return new_entry

    def compare_models(
        self,
        candidate_version: str,
        production_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compares candidate model validation metrics against production model.
        Returns detailed metric diffs, per-class F1 comparisons, and recommendation.
        """
        registry = self.load_registry()
        if production_version is None:
            production_version = registry.get("production_model_version", "v1.0")

        cand_meta = self.get_model_by_version(candidate_version)
        prod_meta = self.get_model_by_version(production_version)

        if not cand_meta:
            raise ValueError(f"Candidate model '{candidate_version}' not found in registry.")
        if not prod_meta:
            raise ValueError(f"Production model '{production_version}' not found in registry.")

        p_metrics = prod_meta.get("validation_metrics", {}).get("overall", {})
        c_metrics = cand_meta.get("validation_metrics", {}).get("overall", {})

        p_acc = p_metrics.get("accuracy", p_metrics.get("test_accuracy", 0.0))
        c_acc = c_metrics.get("accuracy", c_metrics.get("test_accuracy", 0.0))

        p_f1 = p_metrics.get("test_f1_macro", 0.0)
        c_f1 = c_metrics.get("test_f1_macro", 0.0)

        acc_delta = round(c_acc - p_acc, 4)
        f1_delta = round(c_f1 - p_f1, 4)

        # Decide promotion recommendation
        is_superior = (c_f1 >= p_f1) and (c_acc >= (p_acc - 0.01))
        
        comparison = {
            "candidate_version": candidate_version,
            "production_version": production_version,
            "metrics_comparison": {
                "accuracy": {
                    "production": p_acc,
                    "candidate": c_acc,
                    "delta": acc_delta,
                    "improved": acc_delta > 0
                },
                "macro_f1": {
                    "production": p_f1,
                    "candidate": c_f1,
                    "delta": f1_delta,
                    "improved": f1_delta > 0
                }
            },
            "per_class_f1_comparison": {},
            "recommendation": "PROMOTE_TO_PRODUCTION" if is_superior else "REJECT_OR_REFINE",
            "justification": (
                f"Candidate {candidate_version} Macro-F1 ({c_f1:.4f}) vs Production {production_version} ({p_f1:.4f}). "
                f"Accuracy delta: {acc_delta:+.4f}."
            )
        }

        # Compare per-class metrics
        p_pc = prod_meta.get("validation_metrics", {}).get("per_class", {})
        c_pc = cand_meta.get("validation_metrics", {}).get("per_class", {})
        all_classes = set(list(p_pc.keys()) + list(c_pc.keys()))

        for cls in all_classes:
            pf1 = p_pc.get(cls, {}).get("f1_score", 0.0)
            cf1 = c_pc.get(cls, {}).get("f1_score", 0.0)
            comparison["per_class_f1_comparison"][cls] = {
                "production_f1": pf1,
                "candidate_f1": cf1,
                "delta": round(cf1 - pf1, 4)
            }

        return comparison

    def promote_to_production(self, candidate_version: str) -> Dict[str, Any]:
        """
        Promotes a candidate model to production.
        Demotes the previous production model to 'retired'.
        """
        registry = self.load_registry()
        cand_found = False

        for m in registry.get("models", []):
            if m.get("model_version") == candidate_version:
                m["status"] = "production"
                cand_found = True
            elif m.get("status") == "production":
                m["status"] = "retired"

        if not cand_found:
            raise ValueError(f"Model version '{candidate_version}' not found in registry.")

        registry["production_model_version"] = candidate_version
        self.save_registry(registry)
        logger.info(f"Successfully promoted model '{candidate_version}' to production.")
        return self.get_production_model_meta()
