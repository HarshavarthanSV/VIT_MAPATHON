"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: YOLOv8 Plant Detection Model Training

Trains a deep convolutional object detector (Ultralytics YOLOv8) on georeferenced
high-resolution image patches to recognize individual Banana plants, Coconut palms,
and other agricultural trees. Utilizes GPU/CUDA acceleration.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("YOLOTrainer")


def train_tree_counting_model(
    dataset_yaml: str = "data/tree_counting/dataset.yaml",
    models_dir: str = "models/tree_counter",
    base_model: str = "yolov8n.pt",
    epochs: int = 25,
    imgsz: int = 640,
    batch: int = 8,
    device: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trains YOLOv8 on agricultural plant crowns and saves artifacts to models/tree_counter/.
    """
    os.makedirs(models_dir, exist_ok=True)

    if device is None:
        device = "0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Initiating YOLOv8 training on device: {device} (CUDA Available: {torch.cuda.is_available()})")

    if not os.path.exists(dataset_yaml):
        raise FileNotFoundError(f"Dataset configuration not found: {dataset_yaml}")

    # Load pretrained YOLOv8 model
    model = YOLO(base_model)
    logger.info(f"Loaded base model: {base_model}")

    # Train model
    results = model.train(
        data=dataset_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=2,
        optimizer="AdamW",
        lr0=0.001,
        patience=10,
        save=True,
        project=models_dir,
        name="training_run",
        exist_ok=True,
        verbose=True
    )

    # Copy / locate best model weights
    best_pt_src = os.path.join(models_dir, "training_run", "weights", "best.pt")
    target_best_pt = os.path.join(models_dir, "best.pt")

    if os.path.exists(best_pt_src):
        import shutil
        shutil.copy2(best_pt_src, target_best_pt)
        logger.info(f"Saved primary best model checkpoint to: {target_best_pt}")
    else:
        # Fallback to model's default save
        target_best_pt = best_pt_src

    # Save training configuration & metadata
    config_record = {
        "architecture": "YOLOv8-Nano (Object Detection)",
        "base_model": base_model,
        "epochs": epochs,
        "imgsz": imgsz,
        "batch_size": batch,
        "device": str(device),
        "classes": {
            0: "banana",
            1: "coconut",
            2: "other_tree"
        },
        "target_model_path": target_best_pt
    }

    config_path = os.path.join(models_dir, "training_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_record, f, indent=2)

    logger.info(f"Training configuration saved to: {config_path}")
    return config_record


if __name__ == "__main__":
    train_tree_counting_model()
