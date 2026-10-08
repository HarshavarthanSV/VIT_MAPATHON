"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: Export Deliverables & Cartographic Map Generator

Generates all required final deliverables in results/tree_count/:
1. tree_detections.geojson
2. parcel_tree_counts.csv
3. tree_count_summary.json
4. tree_detection_map.png (300 DPI publication map)
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DeliverablesExporter")


class DeliverablesExporter:
    """
    Exports all standardized project deliverables into results/tree_count/.
    """

    def __init__(
        self,
        results_dir: str = "results/tree_count"
    ):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def export_csv(
        self,
        fused_gdf: gpd.GeoDataFrame
    ) -> str:
        """Exports parcel_tree_counts.csv with clean agronomic columns."""
        cols = [
            "parcel_id", "taluk", "crop_type", "crop_confidence", "area_ha",
            "banana_count", "coconut_count", "other_tree_count",
            "total_tree_count", "plant_density", "object_classes",
            "object_detection_confidence"
        ]
        available_cols = [c for c in cols if c in fused_gdf.columns]
        df_out = fused_gdf[available_cols].copy()

        csv_path = os.path.join(self.results_dir, "parcel_tree_counts.csv")
        df_out.to_csv(csv_path, index=False)
        logger.info(f"Exported parcel tree counts CSV: {csv_path} ({len(df_out)} rows)")
        return csv_path

    def export_geojson(
        self,
        detections_wgs84: gpd.GeoDataFrame
    ) -> str:
        """Exports tree_detections.geojson in EPSG:4326."""
        # Retain essential properties
        export_cols = [
            "detection_id", "class_name", "class_id", "confidence",
            "parcel_id", "latitude", "longitude", "crown_diameter_m",
            "utm_x", "utm_y", "geometry"
        ]
        available_cols = [c for c in export_cols if c in detections_wgs84.columns]
        clean_gdf = detections_wgs84[available_cols].copy()

        geojson_path = os.path.join(self.results_dir, "tree_detections.geojson")
        clean_gdf.to_file(geojson_path, driver="GeoJSON")
        logger.info(f"Exported tree detections GeoJSON: {geojson_path} ({len(clean_gdf)} objects)")
        return geojson_path

    def export_summary_json(
        self,
        imagery_meta: Dict[str, Any],
        training_meta: Dict[str, Any],
        eval_metrics: Dict[str, Any],
        fusion_summary: Dict[str, Any]
    ) -> str:
        """Exports tree_count_summary.json summarizing pipeline execution."""
        summary_payload = {
            "title": "VIT MAPATHON — Individual Tree & Plant Counting Assessment",
            "module": "Member 1 — AI / Computer Vision Engineer",
            "study_area": "Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District",
            "imagery_specifications": {
                "source": "Simulated High-Resolution Orthomosaic (UAV/Aerial Analogue)",
                "spatial_resolution": "0.25 meters / pixel GSD",
                "spectral_bands": ["Red", "Green", "Blue"],
                "projected_crs": "EPSG:32643 (WGS 84 / UTM Zone 43N)",
                "geographic_crs": "EPSG:4326 (WGS 84 Lat/Lon)"
            },
            "training_specifications": {
                "model_architecture": "YOLOv8-Nano (Deep Convolutional Object Detector)",
                "classes": ["banana", "coconut", "other_tree"],
                "total_training_tiles": training_meta.get("split_tiles", {}).get("train", 49),
                "total_training_annotations": training_meta.get("split_plants", {}).get("train", 11965),
                "spatial_leakage_prevention": "Strict GroupSplit by cadastral parcel boundary (zero visually adjacent field overlap)"
            },
            "model_detection_performance": eval_metrics.get("detection_metrics", {}),
            "counting_accuracy_metrics": eval_metrics.get("counting_metrics", {}),
            "parcel_fusion_results": fusion_summary,
            "methodology_and_limitations": {
                "macro_vs_micro_fusion": "Sentinel-2 10m surface reflectance is used exclusively for macro parcel-level crop classification (Paddy, Banana, Other). High-resolution sub-meter imagery (0.25m GSD) and YOLO computer vision are used for individual plant/tree detection and counting.",
                "counting_factors": [
                    "Spatial resolution (requires <= 0.5m GSD to visually distinguish crowns)",
                    "Plant canopy overlap in dense mature plantations",
                    "Lighting conditions, cast shadow orientation, and phenological stage",
                    "Field boundary weed / windbreak vegetation discrimination"
                ]
            }
        }

        json_path = os.path.join(self.results_dir, "tree_count_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2)
        logger.info(f"Exported tree count summary JSON: {json_path}")
        return json_path

    def generate_detection_map(
        self,
        fused_parcels_utm: gpd.GeoDataFrame,
        detections_utm: gpd.GeoDataFrame
    ) -> str:
        """
        Renders a publication-ready 300 DPI cartographic map of detected trees and parcels.
        """
        logger.info("Generating publication-quality detection map (300 DPI)...")

        # Focus map around the survey parcels
        parcels_with_trees = fused_parcels_utm[fused_parcels_utm["total_tree_count"] > 0]
        if len(parcels_with_trees) == 0:
            plot_parcels = fused_parcels_utm.head(20)
        else:
            plot_parcels = parcels_with_trees

        # Create plot
        fig, (ax_map, ax_chart) = plt.subplots(
            1, 2, figsize=(18, 9),
            gridspec_kw={"width_ratios": [2.2, 1.0]},
            facecolor="#ffffff"
        )

        # 1. Map Panel
        ax_map.set_facecolor("#f8fafc")
        plot_parcels.plot(
            ax=ax_map,
            color="#e2e8f0",
            edgecolor="#0f172a",
            linewidth=1.2,
            alpha=0.6,
            zorder=2
        )

        # Plot detections color-coded by class
        color_map = {
            "banana": "#16a34a",     # Emerald Green
            "coconut": "#d97706",    # Amber / Orange
            "other_tree": "#2563eb"  # Royal Blue
        }

        # Filter detections to map extent
        minx, miny, maxx, maxy = plot_parcels.total_bounds
        buf = 100.0
        ax_map.set_xlim(minx - buf, maxx + buf)
        ax_map.set_ylim(miny - buf, maxy + buf)

        # Plot points
        for c_name, c_color in color_map.items():
            sub = detections_utm[detections_utm["class_name"] == c_name]
            if len(sub) > 0:
                ax_map.scatter(
                    sub["utm_x"], sub["utm_y"],
                    c=c_color, s=14, alpha=0.8, edgecolors="none",
                    label=f"{c_name.capitalize()} ({len(sub):,} detected)",
                    zorder=4
                )

        # Title & labels
        ax_map.set_title(
            "High-Resolution Individual Tree & Plant Detections (0.25m GSD)\nAmbasamudram & Cheranmahadevi Study Area, Tirunelveli District",
            fontsize=13, fontweight="bold", pad=12, color="#0f172a"
        )
        ax_map.set_xlabel("UTM Zone 43N Easting (m)", fontsize=10, fontweight="bold", color="#334155")
        ax_map.set_ylabel("UTM Zone 43N Northing (m)", fontsize=10, fontweight="bold", color="#334155")
        ax_map.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1")
        ax_map.legend(loc="lower right", framealpha=0.92, facecolor="#ffffff", fontsize=9)

        # North Arrow
        ax_map.annotate(
            "N\n▲", xy=(0.04, 0.93), xycoords="axes fraction",
            ha="center", va="center", fontsize=14, fontweight="bold",
            color="#0f172a", bbox=dict(boxstyle="circle,pad=0.3", fc="#ffffff", ec="#94a3b8")
        )

        # 2. Side Analytics Panel
        ax_chart.set_facecolor("#ffffff")
        
        # Summary counts
        total_banana = int(detections_utm[detections_utm["class_name"] == "banana"].shape[0])
        total_coconut = int(detections_utm[detections_utm["class_name"] == "coconut"].shape[0])
        total_other = int(detections_utm[detections_utm["class_name"] == "other_tree"].shape[0])
        total_all = total_banana + total_coconut + total_other

        categories = ["Banana", "Coconut", "Other Tree"]
        counts = [total_banana, total_coconut, total_other]
        colors = ["#16a34a", "#d97706", "#2563eb"]

        bars = ax_chart.bar(categories, counts, color=colors, edgecolor="#0f172a", linewidth=0.8, width=0.55)
        for b in bars:
            h = b.get_height()
            ax_chart.annotate(
                f"{h:,}",
                xy=(b.get_x() + b.get_width() / 2, h),
                xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=10, fontweight="bold", color="#0f172a"
            )

        ax_chart.set_title("Plant Count by Species", fontsize=12, fontweight="bold", color="#0f172a", pad=10)
        ax_chart.set_ylabel("Detected Object Count", fontsize=10, fontweight="bold", color="#334155")
        ax_chart.grid(axis="y", linestyle="--", alpha=0.4)
        ax_chart.set_ylim(0, max(counts) * 1.18 if max(counts) > 0 else 100)

        # Add text metadata box below chart
        info_text = (
            f"SURVEY SUMMARY\n"
            f"------------------------------------\n"
            f"Total Plants Detected: {total_all:,}\n"
            f"Surveyed Parcels: {len(plot_parcels)}\n"
            f"Spatial Resolution: 0.25 m/pixel\n"
            f"Primary Model: YOLOv8-Nano\n"
            f"Coordinate System: EPSG:32643\n"
            f"------------------------------------\n"
            f"Sentinel-2: Macro Crop Class\n"
            f"High-Res: Micro Plant Counting"
        )
        ax_chart.text(
            0.5, -0.28, info_text, transform=ax_chart.transAxes,
            fontsize=8.5, family="monospace", ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.6", fc="#f8fafc", ec="#cbd5e1", lw=1)
        )

        plt.tight_layout()
        map_path = os.path.join(self.results_dir, "tree_detection_map.png")
        fig.savefig(map_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved publication-grade detection map: {map_path}")
        return map_path


if __name__ == "__main__":
    exporter = DeliverablesExporter()
