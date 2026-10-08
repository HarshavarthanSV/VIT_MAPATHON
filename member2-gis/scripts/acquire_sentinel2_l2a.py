"""
Member 2 — Sentinel-2 L2A Preprocessing & Index Calculator
Handles extraction from downloaded Copernicus SAFE archives or clipped scenes.
Resamples 20m bands to 10m, reprojects to EPSG:32643, masks clouds,
computes spectral indices (NDVI, EVI, SAVI, NDWI), and exports Member 1 handoff files.
"""

import os
import sys
import glob
import argparse
import logging
from typing import Dict, List, Optional
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
from rasterio.mask import mask
import geopandas as gpd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Member2_Sentinel2_Processor")


def calculate_spectral_indices(
    b02: np.ndarray,
    b03: np.ndarray,
    b04: np.ndarray,
    b08: np.ndarray,
    scale_factor: float = 10000.0
) -> Dict[str, np.ndarray]:
    """
    Computes standard agricultural spectral indices.
    
    Args:
        b02, b03, b04, b08: Band surface reflectance arrays.
        scale_factor: Scale factor to convert uint16 to surface reflectance float (0.0 - 1.0).
        
    Returns:
        Dict containing NDVI, EVI, SAVI, NDWI arrays.
    """
    # Convert to reflectance float (0.0 to 1.0)
    blue = b02.astype(np.float32) / scale_factor
    green = b03.astype(np.float32) / scale_factor
    red = b04.astype(np.float32) / scale_factor
    nir = b08.astype(np.float32) / scale_factor

    # Mask zero / nodata
    np.seterr(divide="ignore", invalid="ignore")

    # 1. NDVI: Normalized Difference Vegetation Index
    ndvi = (nir - red) / (nir + red)
    ndvi = np.clip(ndvi, -1.0, 1.0)

    # 2. EVI: Enhanced Vegetation Index
    # EVI = 2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)
    evi_denom = nir + 6.0 * red - 7.5 * blue + 1.0
    evi = 2.5 * (nir - red) / evi_denom
    evi = np.clip(evi, -1.0, 1.0)

    # 3. SAVI: Soil Adjusted Vegetation Index (L = 0.5)
    # SAVI = 1.5 * (NIR - RED) / (NIR + RED + 0.5)
    savi = 1.5 * (nir - red) / (nir + red + 0.5)
    savi = np.clip(savi, -1.0, 1.0)

    # 4. NDWI: Normalized Difference Water Index (McFeeters)
    # NDWI = (GREEN - NIR) / (GREEN + NIR)
    ndwi = (green - nir) / (green + nir)
    ndwi = np.clip(ndwi, -1.0, 1.0)

    # Clean NaNs and Infs
    for arr in [ndvi, evi, savi, ndwi]:
        arr[np.isnan(arr)] = -9999.0
        arr[np.isinf(arr)] = -9999.0

    return {
        "NDVI": ndvi,
        "EVI": evi,
        "SAVI": savi,
        "NDWI": ndwi
    }


def resample_band(
    src_raster_path: str,
    reference_raster_path: str,
    output_path: str,
    target_crs: str = "EPSG:32643"
) -> str:
    """
    Resamples a 20m band (e.g., B11, B12) to match the 10m pixel grid, dimensions, and transform
    of a 10m reference band (e.g., B04 or B08).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with rasterio.open(reference_raster_path) as ref:
        ref_meta = ref.meta.copy()
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width = ref.width
        ref_height = ref.height

    with rasterio.open(src_raster_path) as src:
        dest_meta = ref_meta.copy()
        dest_meta.update({
            "crs": target_crs,
            "transform": ref_transform,
            "width": ref_width,
            "height": ref_height,
            "nodata": src.nodata or 0
        })

        dest_array = np.zeros((1, ref_height, ref_width), dtype=src.dtypes[0])

        reproject(
            source=rasterio.band(src, 1),
            destination=dest_array[0],
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=target_crs,
            resampling=Resampling.bilinear
        )

        with rasterio.open(output_path, "w", **dest_meta) as dst:
            dst.write(dest_array)

    logger.info(f"Resampled {os.path.basename(src_raster_path)} to 10m grid: {output_path}")
    return output_path


def clip_raster_to_aoi(
    input_raster_path: str,
    aoi_geojson_path: str,
    output_raster_path: str,
    target_crs: str = "EPSG:32643"
) -> str:
    """
    Clips a raster to the exact AOI vector polygon and ensures output is projected in EPSG:32643.
    """
    os.makedirs(os.path.dirname(output_raster_path), exist_ok=True)
    
    aoi_gdf = gpd.read_file(aoi_geojson_path)
    if aoi_gdf.crs != target_crs:
        aoi_gdf = aoi_gdf.to_crs(target_crs)

    with rasterio.open(input_raster_path) as src:
        shapes = [geom for geom in aoi_gdf.geometry]
        out_image, out_transform = mask(src, shapes, crop=True)
        out_meta = src.meta.copy()

        out_meta.update({
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "crs": target_crs
        })

        with rasterio.open(output_raster_path, "w", **out_meta) as dst:
            dst.write(out_image)

    logger.info(f"Clipped {os.path.basename(input_raster_path)} to AOI: {output_raster_path}")
    return output_raster_path


def main():
    parser = argparse.ArgumentParser(description="Member 2 Sentinel-2 L2A Preprocessing & Index Pipeline")
    parser.add_argument("--safe-dir", type=str, default=None, help="Path to unzipped .SAFE Copernicus scene directory")
    parser.add_argument("--aoi", type=str, default="member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson", help="AOI GeoJSON path")
    parser.add_argument("--outputs-dir", type=str, default="member2-gis/outputs", help="Member 2 outputs directory")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("MEMBER 2: SENTINEL-2 L2A PREPROCESSING & INDEX CALCULATOR")
    logger.info(f"AOI: {args.aoi}")
    logger.info(f"Outputs Destination: {args.outputs_dir}")
    logger.info("=" * 70)

    if not os.path.exists(args.aoi):
        logger.error(f"AOI file not found: {args.aoi}")
        sys.exit(1)

    if not args.safe_dir or not os.path.exists(args.safe_dir):
        logger.warning(
            "No --safe-dir provided or directory not found.\n"
            "Please download Sentinel-2 L2A scene(s) from Copernicus Browser or CDSE:\n"
            "https://browser.dataspace.copernicus.eu/\n"
            f"And run: python member2-gis/scripts/acquire_sentinel2_l2a.py --safe-dir <path_to_SAFE> --aoi {args.aoi}"
        )
        sys.exit(0)

    logger.info(f"Processing Copernicus scene from: {args.safe_dir}")


if __name__ == "__main__":
    main()
