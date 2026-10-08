"""
Member 1 — AI / Computer Vision Engineer
Module: Individual Tree & Plant Counting Pipeline
Component: High-Resolution Georeferenced Orthomosaic Generator

Generates high-resolution sub-meter imagery (0.25 m/pixel GSD) in EPSG:32643
and precise individual plant/tree ground-truth positions for agricultural parcels
in Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
import rasterio
from rasterio.transform import Affine
from rasterio.crs import CRS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HighResImageryBuilder")


class HighResImageryBuilder:
    """
    Constructs georeferenced 0.25m GSD high-resolution imagery and ground-truth annotations
    across representative aerial flight blocks in Ambasamudram & Cheranmahadevi.
    """

    CLASS_MAPPING = {
        0: "banana",
        1: "coconut",
        2: "other_tree"
    }

    # Physical crown parameters at 0.25m/pixel (radius in meters)
    SPECIES_PARAMS = {
        "banana": {
            "class_id": 0,
            "crown_radius_m": 1.25,     # 2.5m diameter (10 pixels)
            "color_rgb": (56, 172, 60),  # Bright vibrant banana leaf green
            "shadow_rgb": (28, 88, 32),
            "spacing_m": 2.0,           # Standard 2m x 2m spacing (~2500/ha)
        },
        "coconut": {
            "class_id": 1,
            "crown_radius_m": 3.0,      # 6.0m diameter (24 pixels)
            "color_rgb": (32, 118, 50),  # Deeper palm frond green
            "shadow_rgb": (16, 58, 24),
            "spacing_m": 7.5,           # Standard 7.5m plantation spacing
        },
        "other_tree": {
            "class_id": 2,
            "crown_radius_m": 2.5,      # 5.0m diameter (20 pixels)
            "color_rgb": (40, 102, 42),  # Broadleaf canopy
            "shadow_rgb": (20, 56, 22),
            "spacing_m": 6.0,
        }
    }

    def __init__(
        self,
        parcels_path: str = "data/parcels/cleaned/classified_parcels.geojson",
        output_dir: str = "data/imagery/high_resolution",
        pixel_size_m: float = 0.25,
        target_crs: str = "EPSG:32643"
    ):
        self.parcels_path = parcels_path
        self.output_dir = output_dir
        self.pixel_size = pixel_size_m
        self.target_crs = target_crs
        os.makedirs(self.output_dir, exist_ok=True)

    def load_parcels(self) -> gpd.GeoDataFrame:
        """Loads and reprojects parcels into metric UTM Zone 43N (EPSG:32643)."""
        if not os.path.exists(self.parcels_path):
            raise FileNotFoundError(f"Parcels file not found: {self.parcels_path}")
        gdf = gpd.read_file(self.parcels_path)
        if gdf.crs != self.target_crs:
            gdf = gdf.to_crs(self.target_crs)
        return gdf

    def generate_plants_for_parcel(
        self,
        parcel_row: Any,
        rng: np.random.Generator
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes realistic ground-truth plant coordinate locations within parcel geometry
        based on agronomic layout in Tirunelveli district.
        """
        geom = parcel_row.geometry
        minx, miny, maxx, maxy = geom.bounds
        crop_type = parcel_row.get("predicted_crop", "Other")
        plants = []

        # 1. Primary crop generation
        if crop_type == "Banana":
            spacing = self.SPECIES_PARAMS["banana"]["spacing_m"]
            xs = np.arange(minx + 1.5, maxx - 1.5, spacing)
            ys = np.arange(miny + 1.5, maxy - 1.5, spacing)
            for x in xs:
                for y in ys:
                    # Apply natural field planting jitter (+/- 0.20m)
                    jx = x + rng.uniform(-0.20, 0.20)
                    jy = y + rng.uniform(-0.20, 0.20)
                    pt = Point(jx, jy)
                    # Natural gap rate (3% harvest/gap)
                    if geom.contains(pt) and rng.uniform(0, 1) > 0.03:
                        plants.append({
                            "class_name": "banana",
                            "class_id": 0,
                            "utm_x": jx,
                            "utm_y": jy,
                            "radius_m": float(rng.uniform(1.15, 1.35))
                        })

            # Add occasional boundary coconut trees along parcel bunds
            boundary = geom.boundary
            length = boundary.length
            step = 16.0  # every 16m along boundary
            for dist in np.arange(5.0, length - 5.0, step):
                b_pt = boundary.interpolate(dist)
                if rng.uniform(0, 1) > 0.4:
                    plants.append({
                        "class_name": "coconut",
                        "class_id": 1,
                        "utm_x": b_pt.x,
                        "utm_y": b_pt.y,
                        "radius_m": float(rng.uniform(2.8, 3.3))
                    })

        elif crop_type == "Other":
            # Agroforestry / orchard / mixed fruit trees
            spacing = self.SPECIES_PARAMS["other_tree"]["spacing_m"]
            xs = np.arange(minx + 3.0, maxx - 3.0, spacing)
            ys = np.arange(miny + 3.0, maxy - 3.0, spacing)
            for x in xs:
                for y in ys:
                    jx = x + rng.uniform(-0.8, 0.8)
                    jy = y + rng.uniform(-0.8, 0.8)
                    pt = Point(jx, jy)
                    if geom.contains(pt) and rng.uniform(0, 1) > 0.15:
                        cls_name = "coconut" if rng.uniform(0, 1) > 0.55 else "other_tree"
                        cls_id = 1 if cls_name == "coconut" else 2
                        rad = float(rng.uniform(2.7, 3.2)) if cls_name == "coconut" else float(rng.uniform(2.2, 2.8))
                        plants.append({
                            "class_name": cls_name,
                            "class_id": cls_id,
                            "utm_x": jx,
                            "utm_y": jy,
                            "radius_m": rad
                        })

        else:  # Paddy
            # Paddy has zero internal trees, but boundary coconut & shade trees along irrigation bunds
            boundary = geom.boundary
            length = boundary.length
            step = 20.0
            for dist in np.arange(6.0, length - 6.0, step):
                b_pt = boundary.interpolate(dist)
                if rng.uniform(0, 1) > 0.45:
                    cls_name = "coconut" if rng.uniform(0, 1) > 0.35 else "other_tree"
                    cls_id = 1 if cls_name == "coconut" else 2
                    rad = float(rng.uniform(2.7, 3.2)) if cls_name == "coconut" else float(rng.uniform(2.2, 2.7))
                    plants.append({
                        "class_name": cls_name,
                        "class_id": cls_id,
                        "utm_x": b_pt.x,
                        "utm_y": b_pt.y,
                        "radius_m": rad
                    })

        return plants

    def render_block_raster(
        self,
        bounds: Tuple[float, float, float, float],
        plants: List[Dict[str, Any]],
        parcels_gdf: gpd.GeoDataFrame
    ) -> Tuple[np.ndarray, Affine]:
        """
        Renders a 3-band (RGB) high-resolution 0.25m georeferenced raster orthomosaic.
        """
        minx, miny, maxx, maxy = bounds
        width = int(np.ceil((maxx - minx) / self.pixel_size))
        height = int(np.ceil((maxy - miny) / self.pixel_size))
        transform = Affine(self.pixel_size, 0.0, minx, 0.0, -self.pixel_size, maxy)

        # Base soil & field background
        red_band = np.full((height, width), 132, dtype=np.uint8)   # Soil ochre
        green_band = np.full((height, width), 122, dtype=np.uint8)
        blue_band = np.full((height, width), 92, dtype=np.uint8)

        # Add natural soil texture noise
        noise = np.random.normal(0, 7, (height, width)).astype(np.int16)
        red_band = np.clip(red_band.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        green_band = np.clip(green_band.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        blue_band = np.clip(blue_band.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Paint agricultural field backgrounds
        for _, p in parcels_gdf.iterrows():
            crop = p.get("predicted_crop", "Other")
            p_minx, p_miny, p_maxx, p_maxy = p.geometry.bounds
            col_min = max(0, int((p_minx - minx) / self.pixel_size))
            col_max = min(width, int((p_maxx - minx) / self.pixel_size))
            row_min = max(0, int((maxy - p_maxy) / self.pixel_size))
            row_max = min(height, int((maxy - p_miny) / self.pixel_size))

            if col_min < col_max and row_min < row_max:
                if crop == "Paddy":
                    # Inundated wetland / rice vegetative background
                    red_band[row_min:row_max, col_min:col_max] = 68
                    green_band[row_min:row_max, col_min:col_max] = 142
                    blue_band[row_min:row_max, col_min:col_max] = 82
                elif crop == "Banana":
                    # Loamy damp plantation soil under canopy
                    red_band[row_min:row_max, col_min:col_max] = 102
                    green_band[row_min:row_max, col_min:col_max] = 115
                    blue_band[row_min:row_max, col_min:col_max] = 72
                else: # Other
                    red_band[row_min:row_max, col_min:col_max] = 125
                    green_band[row_min:row_max, col_min:col_max] = 130
                    blue_band[row_min:row_max, col_min:col_max] = 88

        # Render individual tree/plant canopies with shadows and physical geometry
        yy, xx = np.mgrid[0:height, 0:width]
        for plant in plants:
            px = int((plant["utm_x"] - minx) / self.pixel_size)
            py = int((maxy - plant["utm_y"]) / self.pixel_size)
            r_px = int(plant["radius_m"] / self.pixel_size)

            if 0 <= px < width and 0 <= py < height:
                y0, y1 = max(0, py - r_px - 2), min(height, py + r_px + 3)
                x0, x1 = max(0, px - r_px - 2), min(width, px + r_px + 3)

                sub_xx = xx[y0:y1, x0:x1] - px
                sub_yy = yy[y0:y1, x0:x1] - py
                dist = np.sqrt(sub_xx**2 + sub_yy**2)

                mask = dist <= r_px
                shadow_mask = (dist <= (r_px * 1.15)) & ((sub_xx > 0) & (sub_yy > 0)) & (~mask)

                cls_info = self.SPECIES_PARAMS[plant["class_name"]]
                cr, cg, cb = cls_info["color_rgb"]
                sr, sg, sb = cls_info["shadow_rgb"]

                # Apply cast shadow
                red_band[y0:y1, x0:x1][shadow_mask] = sr
                green_band[y0:y1, x0:x1][shadow_mask] = sg
                blue_band[y0:y1, x0:x1][shadow_mask] = sb

                # Apply plant crown with radial gradient (brighter center, leaf texture)
                grad = np.clip(1.2 - (dist / max(1, r_px)) * 0.35, 0.75, 1.25)
                sub_r = np.clip(cr * grad, 0, 255).astype(np.uint8)
                sub_g = np.clip(cg * grad, 0, 255).astype(np.uint8)
                sub_b = np.clip(cb * grad, 0, 255).astype(np.uint8)

                red_band[y0:y1, x0:x1][mask] = sub_r[mask]
                green_band[y0:y1, x0:x1][mask] = sub_g[mask]
                blue_band[y0:y1, x0:x1][mask] = sub_b[mask]

        rgb = np.stack([red_band, green_band, blue_band], axis=0)
        return rgb, transform

    def build_survey_blocks(
        self,
        random_seed: int = 42
    ) -> Tuple[List[str], str, Dict[str, Any]]:
        """
        Creates two distinct survey orthomosaic blocks:
        - Block 1: Ambasamudram riparian zone (dense banana plantations, paddy fields, bund coconuts)
        - Block 2: Cheranmahadevi agricultural zone (orchard trees, mixed agroforestry, paddy)
        """
        rng = np.random.default_rng(random_seed)
        gdf = self.load_parcels()

        # Find centers for Block 1 (around parcel 0) and Block 2 (around an 'Other' parcel)
        p0_pt = gdf.iloc[0].geometry.centroid
        dists1 = ((gdf.geometry.centroid.x - p0_pt.x)**2 + (gdf.geometry.centroid.y - p0_pt.y)**2)**0.5
        block1_parcels = gdf[dists1 < 1200].copy() # ~20-30 parcels

        p_other_pt = gdf[gdf["predicted_crop"] == "Other"].iloc[0].geometry.centroid
        dists2 = ((gdf.geometry.centroid.x - p_other_pt.x)**2 + (gdf.geometry.centroid.y - p_other_pt.y)**2)**0.5
        block2_parcels = gdf[dists2 < 1200].copy()

        logger.info(f"Survey Block 1 (Ambasamudram): {len(block1_parcels)} parcels")
        logger.info(f"Survey Block 2 (Cheranmahadevi): {len(block2_parcels)} parcels")

        all_plants = []
        plant_id = 1
        blocks_info = []

        # Process Block 1
        b1_plants = []
        for _, row in block1_parcels.iterrows():
            plants = self.generate_plants_for_parcel(row, rng)
            for p in plants:
                p["plant_id"] = f"PLANT_{plant_id:06d}"
                p["parcel_id"] = row["parcel_id"]
                p["dominant_crop"] = row["predicted_crop"]
                p["block"] = "block_1_ambasamudram"
                b1_plants.append(p)
                all_plants.append(p)
                plant_id += 1

        b1_bounds = block1_parcels.total_bounds
        b1_ext = (b1_bounds[0] - 30.0, b1_bounds[1] - 30.0, b1_bounds[2] + 30.0, b1_bounds[3] + 30.0)
        b1_rgb, b1_trans = self.render_block_raster(b1_ext, b1_plants, block1_parcels)
        b1_path = os.path.join(self.output_dir, "orthomosaic_block1_ambasamudram.tif")

        meta1 = {
            "driver": "GTiff",
            "dtype": "uint8",
            "nodata": None,
            "width": b1_rgb.shape[2],
            "height": b1_rgb.shape[1],
            "count": 3,
            "crs": CRS.from_string(self.target_crs),
            "transform": b1_trans,
            "compress": "lzw"
        }
        with rasterio.open(b1_path, "w", **meta1) as dst:
            dst.write(b1_rgb)
        logger.info(f"Saved Block 1 Orthomosaic: {b1_path} ({b1_rgb.shape[2]}x{b1_rgb.shape[1]} px, {len(b1_plants)} plants)")
        blocks_info.append({"name": "block_1", "path": b1_path, "bounds": list(b1_ext), "parcels": len(block1_parcels), "plants": len(b1_plants)})

        # Process Block 2
        b2_plants = []
        for _, row in block2_parcels.iterrows():
            plants = self.generate_plants_for_parcel(row, rng)
            for p in plants:
                p["plant_id"] = f"PLANT_{plant_id:06d}"
                p["parcel_id"] = row["parcel_id"]
                p["dominant_crop"] = row["predicted_crop"]
                p["block"] = "block_2_cheranmahadevi"
                b2_plants.append(p)
                all_plants.append(p)
                plant_id += 1

        b2_bounds = block2_parcels.total_bounds
        b2_ext = (b2_bounds[0] - 30.0, b2_bounds[1] - 30.0, b2_bounds[2] + 30.0, b2_bounds[3] + 30.0)
        b2_rgb, b2_trans = self.render_block_raster(b2_ext, b2_plants, block2_parcels)
        b2_path = os.path.join(self.output_dir, "orthomosaic_block2_cheranmahadevi.tif")

        meta2 = {
            "driver": "GTiff",
            "dtype": "uint8",
            "nodata": None,
            "width": b2_rgb.shape[2],
            "height": b2_rgb.shape[1],
            "count": 3,
            "crs": CRS.from_string(self.target_crs),
            "transform": b2_trans,
            "compress": "lzw"
        }
        with rasterio.open(b2_path, "w", **meta2) as dst:
            dst.write(b2_rgb)
        logger.info(f"Saved Block 2 Orthomosaic: {b2_path} ({b2_rgb.shape[2]}x{b2_rgb.shape[1]} px, {len(b2_plants)} plants)")
        blocks_info.append({"name": "block_2", "path": b2_path, "bounds": list(b2_ext), "parcels": len(block2_parcels), "plants": len(b2_plants)})

        # Export Ground Truth GeoJSON
        plant_geoms = [Point(p["utm_x"], p["utm_y"]) for p in all_plants]
        plant_gdf = gpd.GeoDataFrame(
            [
                {
                    "plant_id": p["plant_id"],
                    "class_name": p["class_name"],
                    "class_id": p["class_id"],
                    "parcel_id": p["parcel_id"],
                    "dominant_crop": p["dominant_crop"],
                    "block": p["block"],
                    "crown_radius_m": round(p["radius_m"], 2),
                    "utm_x": round(p["utm_x"], 2),
                    "utm_y": round(p["utm_y"], 2),
                }
                for p in all_plants
            ],
            geometry=plant_geoms,
            crs=self.target_crs
        )

        plant_geojson_utm = os.path.join(self.output_dir, "ground_truth_plants_utm.geojson")
        plant_gdf.to_file(plant_geojson_utm, driver="GeoJSON")

        plant_gdf_wgs84 = plant_gdf.to_crs("EPSG:4326")
        plant_geojson_wgs84 = os.path.join(self.output_dir, "ground_truth_plants.geojson")
        plant_gdf_wgs84.to_file(plant_geojson_wgs84, driver="GeoJSON")
        logger.info(f"Exported ground-truth plants GeoJSON: {plant_geojson_wgs84} ({len(plant_gdf)} total plants)")

        # Summary metadata
        class_breakdown = {}
        for p in all_plants:
            class_breakdown[p["class_name"]] = class_breakdown.get(p["class_name"], 0) + 1

        metadata = {
            "spatial_resolution_m": self.pixel_size,
            "crs": self.target_crs,
            "total_plants": len(all_plants),
            "class_breakdown": class_breakdown,
            "survey_blocks": blocks_info
        }

        meta_path = os.path.join(self.output_dir, "imagery_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return [b1_path, b2_path], plant_geojson_wgs84, metadata


if __name__ == "__main__":
    builder = HighResImageryBuilder()
    builder.build_survey_blocks()
