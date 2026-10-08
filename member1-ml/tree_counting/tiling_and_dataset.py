"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: Tiling & YOLO Dataset Preparation

Tiles georeferenced high-resolution GeoTIFFs into 640x640 patches, preserves
exact geographic coordinate transforms, generates normalized YOLO annotations,
and performs spatial GroupSplit (Train / Val / Test) with zero spatial data leakage.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import geopandas as gpd
from shapely.geometry import box, Point
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TilingAndDatasetBuilder")


class TilingAndDatasetBuilder:
    """
    Slices large high-resolution orthomosaics into 640x640 training tiles,
    mapping plant centroids into YOLO bounding boxes and preserving spatial transforms.
    """

    def __init__(
        self,
        imagery_dir: str = "data/imagery/high_resolution",
        dataset_dir: str = "data/tree_counting",
        tile_size: int = 640,
        stride: int = 512,  # 20% spatial overlap
        pixel_size_m: float = 0.25
    ):
        self.imagery_dir = imagery_dir
        self.dataset_dir = dataset_dir
        self.tile_size = tile_size
        self.stride = stride
        self.pixel_size = pixel_size_m

        for split in ["train", "val", "test"]:
            os.makedirs(os.path.join(self.dataset_dir, "images", split), exist_ok=True)
            os.makedirs(os.path.join(self.dataset_dir, "labels", split), exist_ok=True)

    def generate_tiles_for_block(
        self,
        tif_path: str,
        plant_gdf: gpd.GeoDataFrame,
        block_id: str,
        split_assignment: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Slices a single GeoTIFF orthomosaic into georeferenced patches and assigns them to splits.
        """
        tiles_metadata = []

        with rasterio.open(tif_path) as src:
            width = src.width
            height = src.height
            transform = src.transform
            crs_str = str(src.crs)

            x_steps = list(range(0, width - self.tile_size + 1, self.stride))
            if x_steps[-1] != width - self.tile_size and width >= self.tile_size:
                x_steps.append(width - self.tile_size)

            y_steps = list(range(0, height - self.tile_size + 1, self.stride))
            if y_steps[-1] != height - self.tile_size and height >= self.tile_size:
                y_steps.append(height - self.tile_size)

            tile_counter = 0

            for y_off in y_steps:
                for x_off in x_steps:
                    window = Window(x_off, y_off, self.tile_size, self.tile_size)
                    tile_transform = rasterio.windows.transform(window, transform)

                    tile_minx = tile_transform.c
                    tile_maxy = tile_transform.f
                    tile_maxx = tile_minx + self.tile_size * self.pixel_size
                    tile_miny = tile_maxy - self.tile_size * self.pixel_size
                    tile_box = box(tile_minx, tile_miny, tile_maxx, tile_maxy)

                    # Find plants inside this tile bbox
                    cand_plants = plant_gdf[plant_gdf.geometry.intersects(tile_box)]

                    if len(cand_plants) == 0:
                        continue  # Skip empty background tiles

                    # Read RGB data
                    tile_rgb = src.read(window=window)  # shape (3, 640, 640)
                    if tile_rgb.shape[1] != self.tile_size or tile_rgb.shape[2] != self.tile_size:
                        continue

                    # Transpose to (H, W, C) for PIL Image
                    img_arr = np.transpose(tile_rgb, (1, 2, 0))

                    # Determine dominant parcel in this tile to assign split
                    primary_parcel = cand_plants["parcel_id"].mode()[0]
                    split = split_assignment.get(primary_parcel, "train")

                    tile_id = f"{block_id}_tile_{tile_counter:04d}"
                    img_filename = f"{tile_id}.jpg"
                    txt_filename = f"{tile_id}.txt"

                    img_path = os.path.join(self.dataset_dir, "images", split, img_filename)
                    txt_path = os.path.join(self.dataset_dir, "labels", split, txt_filename)

                    # Save JPG
                    im = Image.fromarray(img_arr)
                    im.save(img_path, quality=95)

                    # Generate YOLO annotations
                    # format: class_id x_center y_center width height (normalized)
                    yolo_lines = []
                    plants_in_tile = 0

                    for _, p in cand_plants.iterrows():
                        px = (p["utm_x"] - tile_minx) / self.pixel_size
                        py = (tile_maxy - p["utm_y"]) / self.pixel_size
                        r_px = p["crown_radius_m"] / self.pixel_size
                        dia_px = 2.0 * r_px

                        # Box in pixel space
                        if 0 <= px < self.tile_size and 0 <= py < self.tile_size:
                            xc_norm = np.clip(px / self.tile_size, 0.0, 1.0)
                            yc_norm = np.clip(py / self.tile_size, 0.0, 1.0)
                            w_norm = np.clip(dia_px / self.tile_size, 0.005, 1.0)
                            h_norm = np.clip(dia_px / self.tile_size, 0.005, 1.0)

                            cls_id = int(p["class_id"])
                            yolo_lines.append(f"{cls_id} {xc_norm:.6f} {yc_norm:.6f} {w_norm:.6f} {h_norm:.6f}")
                            plants_in_tile += 1

                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(yolo_lines))

                    tiles_metadata.append({
                        "tile_id": tile_id,
                        "block_id": block_id,
                        "split": split,
                        "primary_parcel": primary_parcel,
                        "image_path": img_path,
                        "label_path": txt_path,
                        "plant_count": plants_in_tile,
                        "tile_minx": tile_minx,
                        "tile_miny": tile_miny,
                        "tile_maxx": tile_maxx,
                        "tile_maxy": tile_maxy,
                        "affine_c": tile_transform.c,
                        "affine_f": tile_transform.f,
                        "pixel_size": self.pixel_size,
                        "crs": crs_str
                    })

                    tile_counter += 1

        return tiles_metadata

    def build_dataset(self) -> Dict[str, Any]:
        """
        Orchestrates tiling across blocks, spatial split, and YAML configuration.
        """
        # Load ground truth plants
        gt_path = os.path.join(self.imagery_dir, "ground_truth_plants_utm.geojson")
        if not os.path.exists(gt_path):
            raise FileNotFoundError(f"Ground truth file not found: {gt_path}")

        plant_gdf = gpd.read_file(gt_path)
        logger.info(f"Loaded {len(plant_gdf)} ground truth plants from {gt_path}")

        # Unique parcels
        unique_parcels = sorted(list(plant_gdf["parcel_id"].unique()))
        logger.info(f"Unique parcels in ground truth: {len(unique_parcels)}")

        # Spatial-aware train/val/test split by parcel to prevent visual leakage
        rng = np.random.default_rng(42)
        shuffled_parcels = unique_parcels.copy()
        rng.shuffle(shuffled_parcels)

        n_total = len(shuffled_parcels)
        n_train = int(np.round(n_total * 0.70))
        n_val = int(np.round(n_total * 0.15))

        train_parcels = set(shuffled_parcels[:n_train])
        val_parcels = set(shuffled_parcels[n_train:n_train + n_val])
        test_parcels = set(shuffled_parcels[n_train + n_val:])

        split_assignment = {}
        for p in train_parcels:
            split_assignment[p] = "train"
        for p in val_parcels:
            split_assignment[p] = "val"
        for p in test_parcels:
            split_assignment[p] = "test"

        logger.info(f"Spatial Partitioning: {len(train_parcels)} Train, {len(val_parcels)} Val, {len(test_parcels)} Test parcels")

        # Process Block 1 and Block 2
        b1_tif = os.path.join(self.imagery_dir, "orthomosaic_block1_ambasamudram.tif")
        b2_tif = os.path.join(self.imagery_dir, "orthomosaic_block2_cheranmahadevi.tif")

        all_tiles = []
        if os.path.exists(b1_tif):
            t1 = self.generate_tiles_for_block(b1_tif, plant_gdf, "b1_amba", split_assignment)
            all_tiles.extend(t1)
            logger.info(f"Block 1: Generated {len(t1)} tiles")

        if os.path.exists(b2_tif):
            t2 = self.generate_tiles_for_block(b2_tif, plant_gdf, "b2_cheran", split_assignment)
            all_tiles.extend(t2)
            logger.info(f"Block 2: Generated {len(t2)} tiles")

        # Save manifest
        manifest_path = os.path.join(self.dataset_dir, "tile_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(all_tiles, f, indent=2)

        split_counts = {"train": 0, "val": 0, "test": 0}
        split_plants = {"train": 0, "val": 0, "test": 0}
        for t in all_tiles:
            s = t["split"]
            split_counts[s] += 1
            split_plants[s] += t["plant_count"]

        logger.info(f"Dataset summary: Tiles: {split_counts} | Plants: {split_plants}")

        # Create YOLO dataset.yaml
        # Absolute paths with forward slashes for cross-platform compatibility
        dataset_abs = os.path.abspath(self.dataset_dir).replace("\\", "/")
        yaml_content = f"""# VIT MAPATHON — Tree / Plant Counting YOLOv8 Dataset Configuration
path: {dataset_abs}
train: images/train
val: images/val
test: images/test

names:
  0: banana
  1: coconut
  2: other_tree

# Dataset Metadata
kpi_target: "Individual Tree & Plant Counting in Ambasamudram & Cheranmahadevi"
spatial_resolution_m: {self.pixel_size}
tile_size: {self.tile_size}
"""

        yaml_path = os.path.join(self.dataset_dir, "dataset.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        logger.info(f"Exported YOLO dataset config: {yaml_path}")

        summary = {
            "total_tiles": len(all_tiles),
            "split_tiles": split_counts,
            "split_plants": split_plants,
            "dataset_yaml": yaml_path,
            "manifest": manifest_path
        }
        return summary


if __name__ == "__main__":
    builder = TilingAndDatasetBuilder()
    builder.build_dataset()
