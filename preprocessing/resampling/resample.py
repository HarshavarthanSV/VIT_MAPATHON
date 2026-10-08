"""
Resampling and Spatial Alignment Module for Sentinel-2 Bands.
Aligns 20m bands (B11, B12, SCL) to 10m native grid (B02, B03, B04, B08)
ensuring exact matching CRS (EPSG:32643), transform, resolution, and pixel extent.
"""

from pathlib import Path
from typing import Union, Optional
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform


def resample_to_reference(
    src_raster_path: Union[str, Path],
    reference_raster_path: Union[str, Path],
    output_path: Union[str, Path],
    resampling_method: Resampling = Resampling.bilinear,
    nodata_val: float = -9999.0,
) -> Path:
    """
    Resample and reproject source raster to match the exact grid, extent,
    CRS, transform, and dimensions of a reference 10m raster.
    """
    src_path = Path(src_raster_path)
    ref_path = Path(reference_raster_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(ref_path) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_width = ref.width
        dst_height = ref.height
        ref_profile = ref.profile.copy()

    with rasterio.open(src_path) as src:
        src_profile = src.profile.copy()
        src_profile.update({
            "crs": dst_crs,
            "transform": dst_transform,
            "width": dst_width,
            "height": dst_height,
            "dtype": "float32",
            "nodata": nodata_val,
            "compress": "lzw",
        })

        if dst_width >= 256 and dst_height >= 256:
            src_profile.update({
                "tiled": True,
                "blockxsize": 256,
                "blockysize": 256,
            })
        else:
            src_profile.pop("tiled", None)
            src_profile.pop("blockxsize", None)
            src_profile.pop("blockysize", None)

        with rasterio.open(out_path, "w", **src_profile) as dst:
            for b_idx in range(1, src.count + 1):
                dst_data = np.full((dst_height, dst_width), nodata_val, dtype=np.float32)

                reproject(
                    source=rasterio.band(src, b_idx),
                    destination=dst_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=resampling_method,
                    src_nodata=src.nodata,
                    dst_nodata=nodata_val,
                )

                dst.write(dst_data, b_idx)

    return out_path


def resample_to_resolution(
    src_raster_path: Union[str, Path],
    output_path: Union[str, Path],
    target_resolution: float = 10.0,
    target_crs: str = "EPSG:32643",
    resampling_method: Resampling = Resampling.bilinear,
    nodata_val: float = -9999.0,
) -> Path:
    """
    Resample raster to a specific target spatial resolution (e.g. 10m) in EPSG:32643.
    """
    src_path = Path(src_raster_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs,
            target_crs,
            src.width,
            src.height,
            *src.bounds,
            resolution=target_resolution,
        )

        profile = src.profile.copy()
        profile.update({
            "crs": target_crs,
            "transform": transform,
            "width": width,
            "height": height,
            "dtype": "float32",
            "nodata": nodata_val,
            "compress": "lzw",
        })

        with rasterio.open(out_path, "w", **profile) as dst:
            for b_idx in range(1, src.count + 1):
                dst_data = np.full((height, width), nodata_val, dtype=np.float32)

                reproject(
                    source=rasterio.band(src, b_idx),
                    destination=dst_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=resampling_method,
                    src_nodata=src.nodata,
                    dst_nodata=nodata_val,
                )

                dst.write(dst_data, b_idx)

    return out_path
