"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Main Pipeline Orchestrator

Executes full end-to-end computer-vision pipeline:
1. Verifies georeferencing and spatial CRS
2. Runs inference across orthomosaic tiles
3. Performs spatial deduplication (Spatial NMS)
4. Fuses Sentinel-2 macro crop classification with high-res plant detections
5. Computes parcel-level plant densities (plants/ha) and handles mixed-crop fields
6. Evaluates counting accuracy and detection metrics
7. Exports deliverables to results/tree_count/:
   - tree_detections.geojson
   - parcel_tree_counts.csv
   - tree_count_summary.json
   - tree_detection_map.png
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Ensure project root and tree_counting dir are in sys.path
tree_counting_dir = os.path.dirname(os.path.abspath(__file__))
if tree_counting_dir not in sys.path:
    sys.path.insert(0, tree_counting_dir)

repo_root = os.path.abspath(os.path.join(tree_counting_dir, "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from parcel_aggregator import ParcelTreeAggregator
from evaluator import TreeCountEvaluator
from export_deliverables import DeliverablesExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TreeCountingPipeline")


def run_full_pipeline(
    model_path: str = "models/tree_counter/best.pt",
    manifest_path: str = "data/tree_counting/tile_manifest.json",
    imagery_meta_path: str = "data/imagery/high_resolution/imagery_metadata.json",
    dataset_yaml: str = "data/tree_counting/dataset.yaml",
    parcels_path: str = "data/parcels/cleaned/classified_parcels.geojson",
    results_dir: str = "results/tree_count",
    conf_thresh: float = 0.25
) -> Dict[str, Any]:
    """
    Executes the complete Tree & Plant Counting Pipeline.
    """
    logger.info("=" * 75)
    logger.info("VIT MAPATHON — MEMBER 1: INDIVIDUAL TREE & PLANT COUNTING MODULE")
    logger.info("Study Area: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District")
    logger.info("Spatial Resolution: 0.25m / pixel (Sub-meter Aerial / Drone GSD)")
    logger.info("=" * 75)

    # 1. Verification of inputs
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained model not found at: {model_path}")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Tile manifest not found at: {manifest_path}")

    # Load metadata
    imagery_meta = {}
    if os.path.exists(imagery_meta_path):
        with open(imagery_meta_path, "r", encoding="utf-8") as f:
            imagery_meta = json.load(f)

    # 2. Evaluation on holdout test set
    logger.info("\n--- STEP 1: Evaluating Model Detection & Counting Accuracy ---")
    evaluator = TreeCountEvaluator(
        model_path=model_path,
        dataset_yaml=dataset_yaml,
        confidence_threshold=conf_thresh
    )
    eval_metrics = evaluator.evaluate_model()

    # 3. Full survey inference and spatial deduplication
    logger.info("\n--- STEP 2: Running Full Survey Inference & Spatial Deduplication ---")
    aggregator = ParcelTreeAggregator(
        model_path=model_path,
        manifest_path=manifest_path,
        parcels_path=parcels_path,
        conf_thresh=conf_thresh
    )

    raw_detections = aggregator.run_inference_on_tiles()
    dedup_detections = aggregator.spatial_deduplication(raw_detections)

    # 4. Spatially fuse with cadastral parcels
    logger.info("\n--- STEP 3: Cadastral Parcel Spatial Intersection & Density Fusion ---")
    fused_parcels, detections_wgs84, fusion_summary = aggregator.fuse_with_parcels(dedup_detections)

    # 5. Export deliverables
    logger.info("\n--- STEP 4: Exporting Final Standard Deliverables ---")
    exporter = DeliverablesExporter(results_dir=results_dir)

    csv_path = exporter.export_csv(fused_parcels)
    geojson_path = exporter.export_geojson(detections_wgs84)

    # Load training metadata from config
    training_meta = {}
    cfg_path = os.path.join(os.path.dirname(model_path), "training_config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            training_meta = json.load(f)

    summary_json_path = exporter.export_summary_json(
        imagery_meta=imagery_meta,
        training_meta=training_meta,
        eval_metrics=eval_metrics,
        fusion_summary=fusion_summary
    )

    # Re-project parcels and detections to UTM for accurate metric cartographic plotting
    fused_utm = fused_parcels.to_crs("EPSG:32643")
    detections_utm = detections_wgs84.to_crs("EPSG:32643")
    map_png_path = exporter.generate_detection_map(fused_utm, detections_utm)

    logger.info("\n" + "=" * 75)
    logger.info("TREE & PLANT COUNTING PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f"1. Detections GeoJSON:  {geojson_path}")
    logger.info(f"2. Parcel Counts CSV:   {csv_path}")
    logger.info(f"3. Summary JSON:        {summary_json_path}")
    logger.info(f"4. Publication Map:     {map_png_path}")
    logger.info("=" * 75)

    return {
        "geojson": geojson_path,
        "csv": csv_path,
        "summary": summary_json_path,
        "map": map_png_path,
        "metrics": eval_metrics,
        "fusion": fusion_summary
    }


if __name__ == "__main__":
    run_full_pipeline()
