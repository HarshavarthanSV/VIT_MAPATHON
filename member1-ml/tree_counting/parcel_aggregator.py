"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: Parcel-Level Aggregator & Spatial Fusion

Performs full inference across high-resolution orthomosaics, projects pixel boxes
into metric UTM (EPSG:32643) and geographic WGS84 (EPSG:4326), performs spatial
Non-Maximum Suppression (deduplication) across tile overlaps, intersects with
cadastral parcels, calculates plant densities (plants/ha), handles mixed-crop
environments, and fuses Sentinel-2 crop classifications with micro-level tree counts.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, box, Polygon
from shapely.strtree import STRtree
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ParcelTreeAggregator")


class ParcelTreeAggregator:
    """
    Fuses Sentinel-2 macro-level crop classifications with high-resolution
    computer-vision individual plant/tree detections.
    """

    CLASS_NAMES = {
        0: "banana",
        1: "coconut",
        2: "other_tree"
    }

    # Minimum spatial deduplication distance (meters) to suppress overlapping tile duplicates
    DEDUP_DISTANCES = {
        "banana": 1.2,
        "coconut": 3.0,
        "other_tree": 2.2
    }

    def __init__(
        self,
        model_path: str = "models/tree_counter/best.pt",
        manifest_path: str = "data/tree_counting/tile_manifest.json",
        parcels_path: str = "data/parcels/cleaned/classified_parcels.geojson",
        conf_thresh: float = 0.25,
        target_crs: str = "EPSG:32643"
    ):
        self.model_path = model_path
        self.manifest_path = manifest_path
        self.parcels_path = parcels_path
        self.conf_thresh = conf_thresh
        self.target_crs = target_crs

    def run_inference_on_tiles(self) -> List[Dict[str, Any]]:
        """
        Runs YOLO model across all georeferenced tiles and converts pixel predictions
        into metric UTM Zone 43N coordinates (EPSG:32643).
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Trained YOLO model not found: {self.model_path}")
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Tile manifest not found: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        logger.info(f"Loading YOLO model from: {self.model_path}")
        model = YOLO(self.model_path)

        raw_detections = []
        det_id = 1

        logger.info(f"Running inference across {len(manifest)} orthomosaic tiles...")
        for tile in manifest:
            img_path = tile["image_path"]
            if not os.path.exists(img_path):
                continue

            preds = model.predict(img_path, conf=self.conf_thresh, verbose=False)
            boxes = preds[0].boxes
            if len(boxes) == 0:
                continue

            xyxy = boxes.xyxy.cpu().numpy()
            conf = boxes.conf.cpu().numpy()
            classes = boxes.cls.cpu().numpy().astype(int)

            tile_minx = tile["tile_minx"]
            tile_maxy = tile["tile_maxy"]
            pixel_size = tile["pixel_size"]

            for i in range(len(boxes)):
                cls_id = int(classes[i])
                cls_name = self.CLASS_NAMES.get(cls_id, "other_tree")
                c_score = float(conf[i])

                # Pixel center coordinates
                x0, y0, x1, y1 = xyxy[i]
                cx_px = (x0 + x1) / 2.0
                cy_px = (y0 + y1) / 2.0
                width_px = (x1 - x0)
                height_px = (y1 - y0)

                # Geographic metric UTM coordinates
                utm_x = tile_minx + (cx_px * pixel_size)
                utm_y = tile_maxy - (cy_px * pixel_size)
                crown_dia_m = float(max(width_px, height_px) * pixel_size)

                raw_detections.append({
                    "raw_id": det_id,
                    "class_name": cls_name,
                    "class_id": cls_id,
                    "confidence": round(c_score, 4),
                    "utm_x": round(float(utm_x), 3),
                    "utm_y": round(float(utm_y), 3),
                    "crown_diameter_m": round(crown_dia_m, 2),
                    "tile_id": tile["tile_id"]
                })
                det_id += 1

        logger.info(f"Raw detections generated before deduplication: {len(raw_detections)}")
        return raw_detections

    def spatial_deduplication(
        self,
        raw_detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Suppresses duplicate detections across overlapping tile boundaries
        using spatial Non-Maximum Suppression (NMS).
        """
        if len(raw_detections) == 0:
            return []

        # Sort detections by confidence descending
        sorted_dets = sorted(raw_detections, key=lambda x: x["confidence"], reverse=True)
        geoms = [Point(d["utm_x"], d["utm_y"]) for d in sorted_dets]
        tree = STRtree(geoms)

        suppressed = set()
        kept_detections = []

        for idx, det in enumerate(sorted_dets):
            if idx in suppressed:
                continue

            kept_detections.append(det)
            pt = geoms[idx]
            cls_name = det["class_name"]
            threshold = self.DEDUP_DISTANCES.get(cls_name, 1.5)

            # Find neighbors within threshold distance
            nearby_indices = tree.query(pt.buffer(threshold))
            for near_idx in nearby_indices:
                if near_idx != idx and near_idx not in suppressed:
                    if sorted_dets[near_idx]["class_name"] == cls_name:
                        suppressed.add(near_idx)

        logger.info(f"Deduplicated detections: {len(kept_detections)} kept ({len(suppressed)} overlapping duplicates removed)")
        return kept_detections

    def fuse_with_parcels(
        self,
        dedup_detections: List[Dict[str, Any]]
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Dict[str, Any]]:
        """
        Spatially intersects detections with agricultural parcels and fuses
        Sentinel-2 crop classification with tree counts.
        """
        # Load parcels
        parcels_gdf = gpd.read_file(self.parcels_path)
        if parcels_gdf.crs != self.target_crs:
            parcels_utm = parcels_gdf.to_crs(self.target_crs)
        else:
            parcels_utm = parcels_gdf.copy()

        # Build GeoDataFrame for detections
        det_points = [Point(d["utm_x"], d["utm_y"]) for d in dedup_detections]
        det_gdf = gpd.GeoDataFrame(dedup_detections, geometry=det_points, crs=self.target_crs)

        # Spatial Join: point in parcel
        joined = gpd.sjoin(det_gdf, parcels_utm[["parcel_id", "geometry"]], how="inner", predicate="intersects")
        logger.info(f"Detections situated inside cadastral parcels: {len(joined)} / {len(det_gdf)}")

        # Assign final clean detection ID
        joined["detection_id"] = [f"TREE_{i+1:06d}" for i in range(len(joined))]

        # Group by parcel and compute counts
        parcel_stats = {}
        for _, row in parcels_utm.iterrows():
            pid = row["parcel_id"]
            parcel_stats[pid] = {
                "banana_count": 0,
                "coconut_count": 0,
                "other_tree_count": 0,
                "total_tree_count": 0,
                "confidences": []
            }

        for _, det in joined.iterrows():
            pid = det["parcel_id"]
            cls_name = det["class_name"]
            if pid in parcel_stats:
                if cls_name == "banana":
                    parcel_stats[pid]["banana_count"] += 1
                elif cls_name == "coconut":
                    parcel_stats[pid]["coconut_count"] += 1
                elif cls_name == "other_tree":
                    parcel_stats[pid]["other_tree_count"] += 1
                parcel_stats[pid]["total_tree_count"] += 1
                parcel_stats[pid]["confidences"].append(det["confidence"])

        # Populate parcels GeoDataFrame with fused columns
        fused_records = []
        for _, row in parcels_gdf.iterrows():
            pid = row["parcel_id"]
            stats = parcel_stats.get(pid, {
                "banana_count": 0,
                "coconut_count": 0,
                "other_tree_count": 0,
                "total_tree_count": 0,
                "confidences": []
            })

            area_ha = float(row.get("area_ha", row.get("area_sq_km", 0.01) * 100.0))
            if area_ha <= 0.001:
                area_ha = 0.5  # fallback reasonable default
            total_trees = stats["total_tree_count"]
            density = round(total_trees / area_ha, 1)

            mean_det_conf = round(float(np.mean(stats["confidences"])), 4) if len(stats["confidences"]) > 0 else 0.0

            # List active detected object classes
            obj_classes = []
            if stats["banana_count"] > 0:
                obj_classes.append("banana")
            if stats["coconut_count"] > 0:
                obj_classes.append("coconut")
            if stats["other_tree_count"] > 0:
                obj_classes.append("other_tree")

            fused_records.append({
                "parcel_id": pid,
                "taluk": row.get("taluk", "Ambasamudram"),
                "crop_type": row.get("predicted_crop", "Other"),
                "crop_confidence": round(float(row.get("confidence", 0.85)), 4),
                "area_ha": round(area_ha, 3),
                "banana_count": stats["banana_count"],
                "coconut_count": stats["coconut_count"],
                "other_tree_count": stats["other_tree_count"],
                "total_tree_count": total_trees,
                "plant_density": density,
                "object_classes": ", ".join(obj_classes) if obj_classes else "none",
                "object_detection_confidence": mean_det_conf
            })

        fused_df = parcels_gdf.copy()
        for col in ["crop_type", "crop_confidence", "banana_count", "coconut_count", "other_tree_count", "total_tree_count", "plant_density", "object_classes", "object_detection_confidence"]:
            fused_df[col] = [r[col] for r in fused_records]

        # Convert detections to WGS84 for GeoJSON delivery
        joined_wgs84 = joined.to_crs("EPSG:4326")
        joined_wgs84["latitude"] = joined_wgs84.geometry.y.round(6)
        joined_wgs84["longitude"] = joined_wgs84.geometry.x.round(6)

        summary = {
            "total_parcels_evaluated": len(parcels_gdf),
            "parcels_with_detections": sum(1 for r in fused_records if r["total_tree_count"] > 0),
            "total_plants_detected": len(joined),
            "banana_count": sum(r["banana_count"] for r in fused_records),
            "coconut_count": sum(r["coconut_count"] for r in fused_records),
            "other_tree_count": sum(r["other_tree_count"] for r in fused_records),
            "mean_plant_density_banana_parcels": round(float(np.mean([r["plant_density"] for r in fused_records if r["crop_type"] == "Banana" and r["total_tree_count"] > 0])), 1) if any(r["crop_type"] == "Banana" and r["total_tree_count"] > 0 for r in fused_records) else 0.0,
            "mean_detection_confidence": round(float(joined["confidence"].mean()), 4) if len(joined) > 0 else 0.0
        }

        logger.info(f"Fusion Summary: {summary}")
        return fused_df, joined_wgs84, summary


if __name__ == "__main__":
    aggregator = ParcelTreeAggregator()
    raw_dets = aggregator.run_inference_on_tiles()
    dedup_dets = aggregator.spatial_deduplication(raw_dets)
    aggregator.fuse_with_parcels(dedup_dets)
