"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: Model & Counting Evaluator

Computes standard object detection metrics (Precision, Recall, F1, mAP50, mAP50-95)
as well as rigorous agronomic counting metrics (Actual Count, Predicted Count,
Absolute Count Error, Percentage Count Error) on holdout test imagery.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
import numpy as np
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TreeCountEvaluator")


class TreeCountEvaluator:
    """
    Evaluates YOLO object detection performance and agricultural plant counting accuracy.
    """

    CLASS_NAMES = {
        0: "banana",
        1: "coconut",
        2: "other_tree"
    }

    def __init__(
        self,
        model_path: str = "models/tree_counter/best.pt",
        dataset_yaml: str = "data/tree_counting/dataset.yaml",
        dataset_dir: str = "data/tree_counting",
        confidence_threshold: float = 0.25
    ):
        self.model_path = model_path
        self.dataset_yaml = dataset_yaml
        self.dataset_dir = dataset_dir
        self.conf_thresh = confidence_threshold

    def evaluate_model(self) -> Dict[str, Any]:
        """
        Runs YOLO validation on test set and computes detection + counting metrics.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Trained model not found at: {self.model_path}")

        logger.info(f"Loading trained YOLO model from: {self.model_path}")
        model = YOLO(self.model_path)

        # 1. Standard Object Detection Validation on Test Set
        logger.info("Running YOLO validation on test split...")
        val_results = model.val(
            data=self.dataset_yaml,
            split="test",
            conf=self.conf_thresh,
            save_json=False,
            verbose=False
        )

        # Extract standard detection metrics
        box_p = float(val_results.box.p.mean()) if hasattr(val_results.box.p, 'mean') else float(val_results.box.p)
        box_r = float(val_results.box.r.mean()) if hasattr(val_results.box.r, 'mean') else float(val_results.box.r)
        box_map50 = float(val_results.box.map50)
        box_map50_95 = float(val_results.box.map)
        f1_score = float(2 * (box_p * box_r) / (box_p + box_r + 1e-6))

        # 2. Agronomic Counting Metrics Calculation
        test_images_dir = os.path.join(self.dataset_dir, "images", "test")
        test_labels_dir = os.path.join(self.dataset_dir, "labels", "test")

        image_files = [f for f in os.listdir(test_images_dir) if f.endswith((".jpg", ".png"))] if os.path.exists(test_images_dir) else []
        logger.info(f"Evaluating counting accuracy on {len(image_files)} test patches...")

        total_actual = 0
        total_predicted = 0

        class_counts_actual = {name: 0 for name in self.CLASS_NAMES.values()}
        class_counts_pred = {name: 0 for name in self.CLASS_NAMES.values()}
        per_patch_errors = []

        for img_name in image_files:
            img_path = os.path.join(test_images_dir, img_name)
            txt_name = os.path.splitext(img_name)[0] + ".txt"
            txt_path = os.path.join(test_labels_dir, txt_name)

            # Ground truth count
            actual_in_patch = 0
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            cls_name = self.CLASS_NAMES.get(cls_id, "other_tree")
                            class_counts_actual[cls_name] += 1
                            actual_in_patch += 1

            # Model prediction
            preds = model.predict(img_path, conf=self.conf_thresh, verbose=False)
            boxes = preds[0].boxes
            pred_in_patch = len(boxes)

            if len(boxes) > 0:
                pred_classes = boxes.cls.cpu().numpy().astype(int)
                for c in pred_classes:
                    c_name = self.CLASS_NAMES.get(int(c), "other_tree")
                    class_counts_pred[c_name] += 1

            total_actual += actual_in_patch
            total_predicted += pred_in_patch

            patch_abs_err = abs(actual_in_patch - pred_in_patch)
            patch_pct_err = (patch_abs_err / max(actual_in_patch, 1)) * 100.0
            per_patch_errors.append({
                "patch": img_name,
                "actual": actual_in_patch,
                "predicted": pred_in_patch,
                "abs_error": patch_abs_err,
                "pct_error": round(patch_pct_err, 2)
            })

        # Overall counting error
        abs_count_error = abs(total_actual - total_predicted)
        pct_count_error = (abs_count_error / max(total_actual, 1)) * 100.0
        count_accuracy_pct = max(0.0, 100.0 - pct_count_error)

        per_class_counting = {}
        for c_name in self.CLASS_NAMES.values():
            act = class_counts_actual[c_name]
            prd = class_counts_pred[c_name]
            err = abs(act - prd)
            pct = (err / max(act, 1)) * 100.0
            per_class_counting[c_name] = {
                "actual_count": act,
                "predicted_count": prd,
                "absolute_error": err,
                "percentage_error": round(pct, 2),
                "accuracy_pct": round(max(0.0, 100.0 - pct), 2)
            }

        metrics_summary = {
            "detection_metrics": {
                "precision": round(box_p, 4),
                "recall": round(box_r, 4),
                "f1_score": round(f1_score, 4),
                "mAP50": round(box_map50, 4),
                "mAP50_95": round(box_map50_95, 4),
            },
            "counting_metrics": {
                "total_actual_count": total_actual,
                "total_predicted_count": total_predicted,
                "absolute_count_error": abs_count_error,
                "percentage_count_error": round(pct_count_error, 2),
                "overall_count_accuracy_pct": round(count_accuracy_pct, 2),
                "test_patches_evaluated": len(image_files),
                "per_class_counting": per_class_counting
            }
        }

        # Save metrics to models directory
        out_path = os.path.join(os.path.dirname(self.model_path), "evaluation_metrics.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metrics_summary, f, indent=2)

        logger.info("=" * 60)
        logger.info("EVALUATION & COUNTING ACCURACY REPORT")
        logger.info(f"Precision:         {box_p:.4f}")
        logger.info(f"Recall:            {box_r:.4f}")
        logger.info(f"F1-Score:          {f1_score:.4f}")
        logger.info(f"mAP@50:            {box_map50:.4f}")
        logger.info(f"Actual Count:      {total_actual}")
        logger.info(f"Predicted Count:   {total_predicted}")
        logger.info(f"Absolute Error:    {abs_count_error}")
        logger.info(f"Percentage Error:  {pct_count_error:.2f}%")
        logger.info(f"Count Accuracy:    {count_accuracy_pct:.2f}%")
        logger.info("=" * 60)

        return metrics_summary


if __name__ == "__main__":
    evaluator = TreeCountEvaluator()
    evaluator.evaluate_model()
