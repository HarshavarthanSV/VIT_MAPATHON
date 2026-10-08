"""
Cloud and Shadow Masking Module for Sentinel-2 Level-2A Products.
Uses Scene Classification Layer (SCL) pixel values to mask clouds and shadows.
Generates data/validation/cloud_mask_report.csv.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
import rasterio

DEFAULT_SCL_MASK_CLASSES = [1, 3, 7, 8, 9, 10]
DEFAULT_SCL_KEEP_CLASSES = [4, 5, 6]


def create_cloud_mask(
    scl_array: np.ndarray,
    mask_classes: Optional[List[int]] = None,
) -> np.ndarray:
    """
    Generate boolean cloud mask from SCL array.
    True = Cloudy / Shadow / Defective (to mask out), False = Clear valid pixel.
    """
    if mask_classes is None:
        mask_classes = DEFAULT_SCL_MASK_CLASSES

    return np.isin(scl_array, mask_classes)


def apply_cloud_masking_to_scenes(
    aligned_scenes: Dict[str, Dict[str, Path]],
    output_base_dir: Path = Path("data/processed/cloud_masked"),
    report_path: Path = Path("data/validation/cloud_mask_report.csv"),
    mask_classes: Optional[List[int]] = None,
    nodata_val: float = -9999.0,
) -> Tuple[Dict[str, Dict[str, Path]], pd.DataFrame]:
    """
    Apply SCL cloud mask to all aligned bands and output clean rasters and validation report.
    """
    print("\n[CLOUD MASKING] Applying SCL cloud and shadow filtering...")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if mask_classes is None:
        mask_classes = DEFAULT_SCL_MASK_CLASSES

    cloud_masked_scenes = {}
    report_rows = []

    for date_str, bands in aligned_scenes.items():
        date_dir = output_base_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        masked_bands = {}

        # Load SCL
        scl_path = bands["SCL"]
        with rasterio.open(scl_path) as scl_src:
            scl_data = scl_src.read(1)
            ref_profile = scl_src.profile.copy()

        # Generate boolean mask
        is_cloud = create_cloud_mask(scl_data, mask_classes=mask_classes)

        total_pixels = int(is_cloud.size)
        masked_pixels = int(np.count_nonzero(is_cloud))
        valid_pixels = total_pixels - masked_pixels
        valid_pct = round((valid_pixels / total_pixels) * 100.0, 2)
        masked_pct = round((masked_pixels / total_pixels) * 100.0, 2)

        report_rows.append({
            "date": date_str,
            "total_pixels": total_pixels,
            "valid_pixels": valid_pixels,
            "masked_pixels": masked_pixels,
            "valid_percentage": valid_pct,
            "masked_percentage": masked_pct,
        })

        print(f"  * Date {date_str}: Valid: {valid_pct}% | Cloud/Shadow Masked: {masked_pct}%")

        ref_profile.update({
            "dtype": "float32",
            "nodata": nodata_val,
            "compress": "lzw",
        })

        if ref_profile["width"] >= 256 and ref_profile["height"] >= 256:
            ref_profile.update({"tiled": True, "blockxsize": 256, "blockysize": 256})
        else:
            ref_profile.pop("tiled", None)
            ref_profile.pop("blockxsize", None)
            ref_profile.pop("blockysize", None)

        for b_name in ["B02", "B03", "B04", "B08", "B11", "B12"]:
            b_path = bands[b_name]
            out_b_path = date_dir / f"{b_name}.tif"

            with rasterio.open(b_path) as src:
                arr = src.read(1).astype(np.float32)

            # Mask invalid pixels
            arr[is_cloud] = nodata_val

            with rasterio.open(out_b_path, "w", **ref_profile) as dst:
                dst.write(arr, 1)

            masked_bands[b_name] = out_b_path

        # Preserve SCL
        masked_bands["SCL"] = scl_path
        cloud_masked_scenes[date_str] = masked_bands

    df_report = pd.DataFrame(report_rows)
    df_report.to_csv(report_path, index=False)
    print(f"  [OK] Saved cloud mask report: {report_path.name}")

    return cloud_masked_scenes, df_report
