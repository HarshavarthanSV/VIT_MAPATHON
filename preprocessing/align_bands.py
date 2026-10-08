"""
Spatial Alignment and Resampling Module for Sentinel-2 Bands.
Aligns 20m bands (B11, B12, SCL) to the 10m grid (B02, B03, B04, B08)
using Bilinear resampling for continuous reflectance and Nearest Neighbor for SCL classes.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


def resample_band_to_reference(
    src_band_path: Path,
    reference_band_path: Path,
    output_band_path: Path,
    resampling_method: Resampling = Resampling.bilinear,
    nodata_val: Optional[float] = None,
) -> Path:
    """
    Resample and warp source band to match the exact resolution, dimensions,
    transform, and grid of a reference 10m band.
    """
    output_band_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(reference_band_path) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_width = ref.width
        dst_height = ref.height

    with rasterio.open(src_band_path) as src:
        src_profile = src.profile.copy()
        effective_nodata = nodata_val if nodata_val is not None else src.nodata

        src_profile.update({
            "crs": dst_crs,
            "transform": dst_transform,
            "width": dst_width,
            "height": dst_height,
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

        with rasterio.open(output_band_path, "w", **src_profile) as dst:
            for b_idx in range(1, src.count + 1):
                dst_data = np.zeros((dst_height, dst_width), dtype=src.dtypes[0])

                reproject(
                    source=rasterio.band(src, b_idx),
                    destination=dst_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=resampling_method,
                    src_nodata=src.nodata,
                    dst_nodata=effective_nodata,
                )

                dst.write(dst_data, b_idx)

    return output_band_path


def align_all_scenes(
    clipped_scenes: Dict[str, Dict[str, Path]],
    output_base_dir: Path = Path("data/processed/aligned"),
) -> Dict[str, Dict[str, Path]]:
    """
    Align all 7 bands for each date to a uniform 10m grid.
    """
    print("\n[ALIGNMENT] Resampling and spatially aligning all bands to 10m...")
    aligned_scenes = {}

    for date_str, bands in clipped_scenes.items():
        date_dir = output_base_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        aligned_bands = {}

        ref_10m = bands["B08"]

        print(f"  * Date {date_str} (Reference: {ref_10m.name})")

        for b_name in ["B02", "B03", "B04", "B08"]:
            src_p = bands[b_name]
            out_p = date_dir / f"{b_name}.tif"
            if src_p.resolve() != out_p.resolve():
                resample_band_to_reference(src_p, ref_10m, out_p, resampling_method=Resampling.nearest)
            aligned_bands[b_name] = out_p

        for b_name in ["B11", "B12"]:
            src_p = bands[b_name]
            out_p = date_dir / f"{b_name}.tif"
            resample_band_to_reference(src_p, ref_10m, out_p, resampling_method=Resampling.bilinear)
            aligned_bands[b_name] = out_p

        if "SCL" in bands:
            src_p = bands["SCL"]
            out_p = date_dir / "SCL.tif"
            # Nearest neighbor for categorical classes
            resample_band_to_reference(src_p, ref_10m, out_p, resampling_method=Resampling.nearest)
            aligned_bands["SCL"] = out_p

        aligned_scenes[date_str] = aligned_bands

    print("  [OK] Spatial alignment completed for all scenes.")
    return aligned_scenes
