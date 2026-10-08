"""
Member 2 — Copernicus Sentinel-2 L2A Automated Processor
Processes Sentinel-2 Level-2A .SAFE directories and .SAFE.zip archives.
Clips to Ambasamudram & Cheranmahadevi AOI in EPSG:32643, resamples 20m bands to 10m,
masks clouds via SCL, computes spectral indices (NDVI, EVI, SAVI, NDWI),
and outputs strictly aligned GeoTIFFs for Member 1 ML pipeline.
"""

import os
import sys
import glob
import re
import zipfile
import argparse
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.mask import mask
import geopandas as gpd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Member2_Sentinel2_Processor")


def find_scene_band_paths(scene_path: str) -> Dict[str, str]:
    """
    Locates band JP2 files inside either an unzipped .SAFE folder or a .SAFE.zip archive.
    
    Returns:
        Dict mapping canonical band names (B02, B03, B04, B08, B11, B12, SCL) to rasterio-readable URIs.
    """
    is_zip = scene_path.endswith(".zip")
    band_map = {}

    if is_zip:
        with zipfile.ZipFile(scene_path) as z:
            namelist = z.namelist()
            for name in namelist:
                if not name.endswith(".jp2"):
                    continue
                basename = os.path.basename(name)
                # Match bands
                for b in ["B02", "B03", "B04", "B08"]:
                    if f"_{b}_10m" in basename:
                        band_map[b] = f"zip://{os.path.abspath(scene_path)}!{name}"
                for b in ["B11", "B12", "SCL"]:
                    if f"_{b}_20m" in basename:
                        band_map[b] = f"zip://{os.path.abspath(scene_path)}!{name}"
    else:
        # Search unzipped folder
        jp2_files = glob.glob(os.path.join(scene_path, "**", "*.jp2"), recursive=True)
        for fpath in jp2_files:
            basename = os.path.basename(fpath)
            for b in ["B02", "B03", "B04", "B08"]:
                if f"_{b}_10m" in basename:
                    band_map[b] = fpath
            for b in ["B11", "B12", "SCL"]:
                if f"_{b}_20m" in basename:
                    band_map[b] = fpath

    return band_map


def extract_date_identifier(scene_path: str) -> str:
    """
    Extracts acquisition date string (e.g. '2026-03-20') from Sentinel-2 filename.
    Format: S2A_MSIL2A_YYYYMMDDTHHMMSS_...
    """
    basename = os.path.basename(scene_path)
    match = re.search(r"_(\d{8})T", basename)
    if match:
        d = match.group(1)
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return "date_01"


def process_sentinel2_scene(
    scene_path: str,
    aoi_geojson_path: str,
    output_dir: str,
    target_crs: str = "EPSG:32643"
) -> Dict[str, str]:
    """
    Full processing pipeline for a single Sentinel-2 L2A scene:
    1. Read and crop 10m bands (B02, B03, B04, B08) to AOI in EPSG:32643.
    2. Read, crop, and resample 20m bands (B11, B12) to match 10m grid.
    3. Apply SCL cloud mask (mask cloud shadows, medium/high clouds, cirrus).
    4. Calculate NDVI, EVI, SAVI, NDWI.
    5. Save aligned GeoTIFFs to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    band_paths = find_scene_band_paths(scene_path)

    required = ["B02", "B03", "B04", "B08", "B11", "B12"]
    missing = [b for b in required if b not in band_paths]
    if missing:
        raise ValueError(f"Missing required bands in {scene_path}: {missing}")

    logger.info(f"Found all required bands in scene: {list(band_paths.keys())}")

    # Load AOI polygon in target CRS
    aoi_gdf = gpd.read_file(aoi_geojson_path)
    if aoi_gdf.crs != target_crs:
        aoi_gdf = aoi_gdf.to_crs(target_crs)
    shapes = [geom for geom in aoi_gdf.geometry]

    # Step 1: Read and crop 10m reference band (B04) to establish grid
    ref_b04_uri = band_paths["B04"]
    with rasterio.open(ref_b04_uri) as src:
        out_image_ref, out_transform_ref = mask(src, shapes, crop=True)
        height_10m = out_image_ref.shape[1]
        width_10m = out_image_ref.shape[2]
        meta_10m = src.meta.copy()
        meta_10m.update({
            "driver": "GTiff",
            "height": height_10m,
            "width": width_10m,
            "transform": out_transform_ref,
            "crs": target_crs,
            "count": 1,
            "nodata": 0,
            "dtype": "uint16"
        })

    cropped_10m_bands = {}

    # Step 2: Crop all 10m bands (B02, B03, B04, B08)
    for b in ["B02", "B03", "B04", "B08"]:
        with rasterio.open(band_paths[b]) as src:
            data, _ = mask(src, shapes, crop=True)
            cropped_10m_bands[b] = data[0]
            # Save band GeoTIFF
            out_file = os.path.join(output_dir, f"{b}.tif")
            with rasterio.open(out_file, "w", **meta_10m) as dst:
                dst.write(data[0], 1)
        logger.info(f"Exported 10m band: {out_file} ({width_10m}x{height_10m})")

    # Step 3: Crop and resample 20m bands (B11, B12) to match 10m grid
    for b in ["B11", "B12"]:
        with rasterio.open(band_paths[b]) as src_20m:
            data_20m, transform_20m = mask(src_20m, shapes, crop=True)
            # Resample to 10m dimensions
            resampled_data = np.zeros((height_10m, width_10m), dtype=np.uint16)
            reproject(
                source=data_20m[0],
                destination=resampled_data,
                src_transform=transform_20m,
                src_crs=src_20m.crs,
                dst_transform=out_transform_ref,
                dst_crs=target_crs,
                resampling=Resampling.bilinear
            )
            cropped_10m_bands[b] = resampled_data
            out_file = os.path.join(output_dir, f"{b}.tif")
            with rasterio.open(out_file, "w", **meta_10m) as dst:
                dst.write(resampled_data, 1)
        logger.info(f"Resampled & exported 20m->10m band: {out_file}")

    # Step 4: SCL Cloud Masking (if SCL exists)
    cloud_mask = np.zeros((height_10m, width_10m), dtype=bool)
    if "SCL" in band_paths:
        with rasterio.open(band_paths["SCL"]) as src_scl:
            data_scl, transform_scl = mask(src_scl, shapes, crop=True)
            resampled_scl = np.zeros((height_10m, width_10m), dtype=np.uint8)
            reproject(
                source=data_scl[0],
                destination=resampled_scl,
                src_transform=transform_scl,
                src_crs=src_scl.crs,
                dst_transform=out_transform_ref,
                dst_crs=target_crs,
                resampling=Resampling.nearest
            )
            # SCL invalid classes: 3=cloud shadow, 8=cloud medium prob, 9=cloud high prob, 10=thin cirrus
            cloud_mask = np.isin(resampled_scl, [3, 8, 9, 10])
            cloud_pct = float(cloud_mask.sum() / cloud_mask.size * 100.0)
            logger.info(f"SCL cloud/shadow mask applied: {cloud_pct:.2f}% masked pixels.")

    # Step 5: Compute Spectral Indices (NDVI, EVI, SAVI, NDWI)
    b02 = cropped_10m_bands["B02"].astype(np.float32) / 10000.0
    b03 = cropped_10m_bands["B03"].astype(np.float32) / 10000.0
    b04 = cropped_10m_bands["B04"].astype(np.float32) / 10000.0
    b08 = cropped_10m_bands["B08"].astype(np.float32) / 10000.0

    np.seterr(divide="ignore", invalid="ignore")

    # NDVI = (B08 - B04) / (B08 + B04)
    ndvi = (b08 - b04) / (b08 + b04)
    ndvi = np.clip(ndvi, -1.0, 1.0)

    # EVI = 2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)
    evi_denom = b08 + 6.0 * b04 - 7.5 * b02 + 1.0
    evi = 2.5 * (b08 - b04) / evi_denom
    evi = np.clip(evi, -1.0, 1.0)

    # SAVI = 1.5 * (B08 - B04) / (B08 + B04 + 0.5)
    savi = 1.5 * (b08 - b04) / (b08 + b04 + 0.5)
    savi = np.clip(savi, -1.0, 1.0)

    # NDWI = (B03 - B08) / (B03 + B08)
    ndwi = (b03 - b08) / (b03 + b08)
    ndwi = np.clip(ndwi, -1.0, 1.0)

    # Apply nodata & cloud mask
    nodata_val = -9999.0
    meta_indices = meta_10m.copy()
    meta_indices.update({
        "dtype": "float32",
        "nodata": nodata_val
    })

    indices_dict = {"NDVI": ndvi, "EVI": evi, "SAVI": savi, "NDWI": ndwi}
    for name, arr in indices_dict.items():
        arr[cloud_mask] = nodata_val
        arr[np.isnan(arr)] = nodata_val
        arr[np.isinf(arr)] = nodata_val
        # Where reflectance was 0 (unobserved), set nodata
        arr[cropped_10m_bands["B04"] == 0] = nodata_val

        out_file = os.path.join(output_dir, f"{name}.tif")
        with rasterio.open(out_file, "w", **meta_indices) as dst:
            dst.write(arr.astype(np.float32), 1)
        logger.info(f"Exported spectral index: {out_file}")

    logger.info(f"Successfully processed scene to: {output_dir}")
    return {"output_dir": output_dir, "date": extract_date_identifier(scene_path)}


def main():
    parser = argparse.ArgumentParser(description="Member 2 Sentinel-2 L2A Preprocessor")
    parser.add_argument("--scene", type=str, default=None, help="Path to .SAFE folder or .SAFE.zip archive")
    parser.add_argument("--aoi", type=str, default="member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson")
    parser.add_argument("--output-dir", type=str, default="member2-gis/outputs/features")
    parser.add_argument("--is-temporal", action="store_true", help="Save into member2-gis/outputs/temporal/<date>/")
    args = parser.parse_args()

    if not args.scene:
        # Search for available .SAFE or .SAFE.zip in project root or member2-gis/inputs/
        candidates = glob.glob("*.SAFE.zip") + glob.glob("*.SAFE") + \
                     glob.glob("member2-gis/inputs/*.SAFE.zip") + glob.glob("member2-gis/inputs/*.SAFE")
        if candidates:
            args.scene = candidates[0]
            logger.info(f"Auto-detected Sentinel-2 scene: {args.scene}")
        else:
            logger.error("No Sentinel-2 scene specified and no .SAFE or .SAFE.zip found.")
            sys.exit(1)

    dest_dir = args.output_dir
    if args.is_temporal:
        date_id = extract_date_identifier(args.scene)
        dest_dir = os.path.join("member2-gis/outputs/temporal", date_id)

    process_sentinel2_scene(args.scene, args.aoi, dest_dir)


if __name__ == "__main__":
    main()
