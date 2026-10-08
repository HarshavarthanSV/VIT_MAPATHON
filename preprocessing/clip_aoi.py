"""
AOI Clipping Module for Sentinel-2 Bands.
Clips all required bands (B02, B03, B04, B08, B11, B12, SCL) to the study area boundary.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping


def load_aoi_shapes(aoi_path: Path, target_crs: Optional[str] = "EPSG:32643") -> List[dict]:
    """Load and reproject AOI boundary geometries."""
    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI file not found at: {aoi_path}")

    gdf = gpd.read_file(aoi_path)
    if gdf.empty:
        raise ValueError(f"AOI file {aoi_path} is empty.")

    if gdf.crs is None:
        gdf.set_crs(epsg=32643, inplace=True)
    elif target_crs and gdf.crs.to_string().upper() != target_crs.upper():
        gdf = gdf.to_crs(target_crs)

    shapes = [mapping(geom) for geom in gdf.geometry if geom is not None and not geom.is_empty]
    return shapes


def clip_single_band(
    input_raster: Path,
    shapes: List[dict],
    output_raster: Path,
    target_crs_str: str = "EPSG:32643",
) -> Path:
    """Clip a single raster file using vector geometries."""
    output_raster.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(input_raster) as src:
        dtype_str = src.dtypes[0]
        if src.nodata is not None:
            nodata_val = src.nodata
        elif "uint" in dtype_str:
            nodata_val = 0
        elif "int" in dtype_str:
            nodata_val = -9999
        else:
            nodata_val = np.nan

        out_image, out_transform = mask(
            src,
            shapes,
            crop=True,
            nodata=nodata_val,
            filled=True,
        )

        out_profile = src.profile.copy()
        out_profile.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": nodata_val,
            "compress": "lzw",
        })

        # Ensure block sizes are valid if tiled
        if out_image.shape[1] >= 256 and out_image.shape[2] >= 256:
            out_profile.update({
                "tiled": True,
                "blockxsize": 256,
                "blockysize": 256,
            })
        else:
            out_profile.pop("tiled", None)
            out_profile.pop("blockxsize", None)
            out_profile.pop("blockysize", None)

        with rasterio.open(output_raster, "w", **out_profile) as dst:
            dst.write(out_image)

    return output_raster


def clip_all_scenes_to_aoi(
    scenes_info: Dict[str, Dict[str, Any]],
    aoi_path: Path,
    output_base_dir: Path = Path("data/processed/clipped"),
    target_crs: str = "EPSG:32643",
) -> Dict[str, Dict[str, Path]]:
    """Clip all 4 Sentinel-2 date granules to the AOI."""
    print(f"\n[CLIPPING] Clipping all Sentinel-2 scenes to AOI: {aoi_path.name}")
    shapes = load_aoi_shapes(aoi_path, target_crs=target_crs)
    clipped_scenes = {}

    for date_str, sdata in scenes_info.items():
        date_dir = output_base_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        clipped_bands = {}

        print(f"  * Processing Date: {date_str}")
        for b_name, b_path in sdata["bands"].items():
            if b_path is None:
                continue
            out_band_file = date_dir / f"{b_name}.tif"
            clip_single_band(b_path, shapes, out_band_file, target_crs_str=target_crs)
            clipped_bands[b_name] = out_band_file

        clipped_scenes[date_str] = clipped_bands

    print("  [OK] Clipping completed for all dates.")
    return clipped_scenes
