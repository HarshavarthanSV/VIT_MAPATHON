"""
VIT MAPATHON — Member 1 ML / AI Pipeline Entrypoint
Problem Statement: Agricultural Land Parcel and Crop Identification (Paddy vs. Banana vs. Other)
Location: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any
import yaml

# Add member1-ml directory to sys.path
member1_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, member1_dir)
sys.path.insert(0, os.path.abspath(os.path.join(member1_dir, "..")))

from preprocessing.validation import (
    DataNotAvailableError,
    GeospatialValidationError,
    validate_study_area,
)
from preprocessing.feature_loader import FeatureLoader
from preprocessing.label_loader import LabelLoader
from preprocessing.dataset_builder import DatasetBuilder
from classification.train import train_crop_classifier, save_model_artifacts
from classification.parcel_classifier import ParcelClassifier
from evaluation.metrics import calculate_model_metrics, export_metrics_json
from evaluation.confusion_matrix import generate_confusion_matrix, plot_confusion_matrix
from evaluation.feature_importance import extract_feature_importance, plot_feature_importance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Member1_ML_Pipeline")


def load_config(config_path: str) -> Dict[str, Any]:
    """Loads YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(config_path: str, args: argparse.Namespace) -> int:
    """
    Executes the end-to-end Machine Learning pipeline.
    """
    logger.info("=" * 70)
    logger.info("VIT MAPATHON — MEMBER 1 (ML / AI ENGINEER) PIPELINE")
    logger.info("Study Area: Ambasamudram & Cheranmahadevi Taluks (>= 20 sq. km)")
    logger.info("Target Crops: Paddy | Banana | Other")
    logger.info("=" * 70)

    cfg = load_config(config_path)

    # Resolve paths (support command-line overrides)
    features_dir = args.features_dir or cfg["paths"]["feature_dir"]
    temporal_dir = args.temporal_dir or cfg["paths"].get("temporal_dir")
    labels_file = args.labels_file or cfg["paths"]["labels_file"]
    parcels_file = args.parcels_file or cfg["paths"].get("parcels_file")
    
    model_artifact = cfg["paths"]["model_artifact"]
    model_metadata = cfg["paths"]["model_metadata"]
    classified_parcels = cfg["paths"]["classified_parcels"]
    crop_statistics = cfg["paths"]["crop_statistics"]
    model_metrics = cfg["paths"]["model_metrics"]
    feature_importance_json = cfg["paths"]["feature_importance_json"]
    feature_importance_plot = cfg["paths"]["feature_importance_plot"]
    confusion_matrix_plot = cfg["paths"]["confusion_matrix_plot"]

    target_crs = cfg["geospatial"]["target_crs"]

    logger.info(f"Target CRS: {target_crs}")
    logger.info(f"Features Directory: {features_dir}")
    logger.info(f"Temporal Directory: {temporal_dir}")
    logger.info(f"Training Labels: {labels_file}")
    logger.info(f"Parcel Boundaries: {parcels_file}")

    # =========================================================================
    # STEP 1: Upstream Data Boundary Check
    # =========================================================================
    logger.info("\n--- STEP 1: Verifying Member 2 Data Availability ---")
    if not os.path.exists(features_dir) or not os.path.exists(labels_file):
        msg = (
            "Member 2 feature data is not available.\n"
            f"Expected raster features at: '{features_dir}'\n"
            f"Expected training labels at: '{labels_file}'\n"
            "The ML pipeline is fully built, validated, and ready to ingest Member 2 handoff data."
        )
        if args.strict:
            logger.error(msg)
            raise DataNotAvailableError(msg)
        else:
            logger.warning(msg)
            print("\n[DATA BOUNDARY STATUS] " + msg)
            return 0

    # =========================================================================
    # STEP 2: Feature & Label Discovery and Ingestion
    # =========================================================================
    logger.info("\n--- STEP 2: Ingesting Sentinel-2 Features and Labels ---")
    try:
        feature_loader = FeatureLoader(
            features_dir=features_dir,
            temporal_dir=temporal_dir,
            expected_crs=target_crs,
            core_bands=cfg["features"]["core_bands"],
            spectral_indices=cfg["features"]["spectral_indices"]
        )
        feature_loader.discover_features()
        feature_loader.discover_temporal_stacks()

        label_loader = LabelLoader(
            labels_path=labels_file,
            target_classes=cfg["classes"]["target_classes"],
            label_col=cfg["classes"]["label_column"],
            id_col=cfg["classes"]["parcel_id_column"],
            target_crs=target_crs,
            normalization_map=cfg["classes"].get("normalization_map")
        )
        labels_gdf = label_loader.load_and_normalize()

    except DataNotAvailableError as e:
        logger.warning(f"Data boundary check: {e}")
        return 0

    # =========================================================================
    # STEP 3: Dataset Construction & Spatial-Aware Split
    # =========================================================================
    logger.info("\n--- STEP 3: Building Dataset & Spatial Group Splitting ---")
    dataset_builder = DatasetBuilder(
        feature_loader=feature_loader,
        label_loader=label_loader,
        sampling_strategy=cfg["dataset"]["sampling_strategy"],
        handle_nan=cfg["dataset"]["handle_nan"],
        test_size=cfg["split"]["test_size"],
        val_size=cfg["split"]["val_size"],
        random_state=cfg["split"]["random_state"]
    )
    df = dataset_builder.build_dataset()
    X_train, X_val, X_test, y_train, y_val, y_test = dataset_builder.create_spatial_splits(df)

    # =========================================================================
    # STEP 4: Random Forest Model Training
    # =========================================================================
    logger.info("\n--- STEP 4: Training Random Forest Crop Classifier ---")
    rf_model = train_crop_classifier(
        X_train=X_train,
        y_train=y_train,
        rf_params=cfg["random_forest"]
    )

    # =========================================================================
    # STEP 5: Dynamic Model Evaluation & Metrics Export
    # =========================================================================
    logger.info("\n--- STEP 5: Evaluating Model on Unseen Spatial Test Parcels ---")
    y_test_pred = rf_model.predict(X_test)
    metrics = calculate_model_metrics(
        y_true=y_test,
        y_pred=y_test_pred,
        labels=list(rf_model.classes_)
    )
    export_metrics_json(metrics, model_metrics)

    # Confusion matrix
    cm_dict = generate_confusion_matrix(
        y_true=y_test,
        y_pred=y_test_pred,
        labels=list(rf_model.classes_)
    )
    plot_confusion_matrix(cm_dict, confusion_matrix_plot)

    # Feature importance
    importance_dict = extract_feature_importance(
        model=rf_model,
        feature_names=dataset_builder.feature_names,
        output_json_path=feature_importance_json
    )
    plot_feature_importance(importance_dict, feature_importance_plot)

    # Save trained model artifact
    save_model_artifacts(
        model=rf_model,
        feature_names=dataset_builder.feature_names,
        model_path=model_artifact,
        metadata_path=model_metadata,
        extra_metadata={"metrics": metrics["overall"]}
    )

    # =========================================================================
    # STEP 6: Parcel-Level Classification & Member 3 Handoff Generation
    # =========================================================================
    if parcels_file and os.path.exists(parcels_file):
        logger.info("\n--- STEP 6: Performing Inference on Agricultural Parcels ---")
        parcel_classifier = ParcelClassifier(
            model=rf_model,
            feature_loader=feature_loader,
            feature_names=dataset_builder.feature_names,
            target_crs=target_crs
        )
        classified_gdf = parcel_classifier.classify_parcels(parcels_file)
        parcel_classifier.export_classified_geojson(classified_gdf, classified_parcels)
        parcel_classifier.compute_crop_statistics(classified_gdf, crop_statistics)
    else:
        logger.warning(
            f"Parcels file '{parcels_file}' not found. "
            "Skipping full study area parcel classification until Member 2 provides parcel boundaries."
        )

    logger.info("\n" + "=" * 70)
    logger.info("MEMBER 1 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    logger.info(f"Model Artifact: {model_artifact}")
    logger.info(f"Metrics Output: {model_metrics}")
    logger.info(f"Classified GeoJSON: {classified_parcels}")
    logger.info(f"Crop Statistics: {crop_statistics}")
    logger.info("=" * 70)
    return 0


def main():
    parser = argparse.ArgumentParser(description="VIT MAPATHON Member 1 ML / AI Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="member1-ml/config/config.yaml",
        help="Path to pipeline configuration YAML"
    )
    parser.add_argument("--features-dir", type=str, default=None, help="Override features directory")
    parser.add_argument("--temporal-dir", type=str, default=None, help="Override temporal directory")
    parser.add_argument("--labels-file", type=str, default=None, help="Override labels file")
    parser.add_argument("--parcels-file", type=str, default=None, help="Override parcels file")
    parser.add_argument("--outputs-dir", type=str, default=None, help="Override outputs directory")
    parser.add_argument("--strict", action="store_true", help="Raise error if Member 2 data is missing")

    args = parser.parse_args()
    sys.exit(run_pipeline(args.config, args))


if __name__ == "__main__":
    main()
