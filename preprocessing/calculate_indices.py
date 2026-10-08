"""
Spectral Indices Calculation and Statistical Validation Module.
Computes NDVI, EVI, SAVI, and NDWI for all Sentinel-2 acquisition dates.
Produces raster GeoTIFFs and data/validation/index_statistics.csv.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import numpy as np
import pandas as pd
import rasterio


def safe_divide(num: np.ndarray, den: np.ndarray, fill_val: float = np.nan) -> np.ndarray:
    """Safely divide numpy arrays avoiding zero division, infinity, and NaN propagation."""
    with np.errstate(divide="ignore", invalid="ignore"):
        res = np.where(np.abs(den) > 1e-7, num / den, fill_val)
    return res


def normalize_to_reflectance(band_data: np.ndarray, nodata_val: float = -9999.0) -> np.ndarray:
    """
    Ensure Sentinel-2 Level-2A BOA values are in continuous surface reflectance [0.0, 1.0].
    Standard Sentinel-2 BOA digital numbers are scaled by 10000.
    """
    data = band_data.astype(np.float32)
    valid_mask = (data != nodata_val) & (~np.isnan(data)) & (data > 0)
    if np.any(valid_mask) and np.nanmax(data[valid_mask]) > 2.0:
        data = np.where(valid_mask, data / 10000.0, nodata_val)
    return data


def compute_all_indices(
    b02: np.ndarray,
    b03: np.ndarray,
    b04: np.ndarray,
    b08: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None,
    nodata_val: float = -9999.0,
) -> Dict[str, np.ndarray]:
    """
    Compute NDVI, EVI, SAVI, NDWI given surface reflectance bands.
    """
    b02_r = normalize_to_reflectance(b02, nodata_val)
    b03_r = normalize_to_reflectance(b03, nodata_val)
    b04_r = normalize_to_reflectance(b04, nodata_val)
    b08_r = normalize_to_reflectance(b08, nodata_val)

    # Invalid mask where any band is nodata or cloud
    invalid = (
        (b02_r == nodata_val) | np.isnan(b02_r) |
        (b03_r == nodata_val) | np.isnan(b03_r) |
        (b04_r == nodata_val) | np.isnan(b04_r) |
        (b08_r == nodata_val) | np.isnan(b08_r)
    )
    if nodata_mask is not None:
        invalid = invalid | nodata_mask

    # 1. NDVI = (B08 - B04) / (B08 + B04)
    ndvi_num = b08_r - b04_r
    ndvi_den = b08_r + b04_r
    ndvi = safe_divide(ndvi_num, ndvi_den, fill_val=nodata_val)
    ndvi = np.where(~invalid, np.clip(ndvi, -1.0, 1.0), nodata_val)

    # 2. EVI = 2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)
    evi_num = b08_r - b04_r
    evi_den = b08_r + (6.0 * b04_r) - (7.5 * b02_r) + 1.0
    evi = 2.5 * safe_divide(evi_num, evi_den, fill_val=nodata_val)
    evi = np.where(~invalid, np.clip(evi, -1.5, 1.5), nodata_val)

    # 3. SAVI = 1.5 * (B08 - B04) / (B08 + B04 + 0.5)
    savi_num = b08_r - b04_r
    savi_den = b08_r + b04_r + 0.5
    savi = 1.5 * safe_divide(savi_num, savi_den, fill_val=nodata_val)
    savi = np.where(~invalid, np.clip(savi, -1.0, 1.0), nodata_val)

    # 4. NDWI = (B03 - B08) / (B03 + B08)
    ndwi_num = b03_r - b08_r
    ndwi_den = b03_r + b08_r
    ndwi = safe_divide(ndwi_num, ndwi_den, fill_val=nodata_val)
    ndwi = np.where(~invalid, np.clip(ndwi, -1.0, 1.0), nodata_val)

    return {
        "NDVI": ndvi.astype(np.float32),
        "EVI": evi.astype(np.float32),
        "SAVI": savi.astype(np.float32),
        "NDWI": ndwi.astype(np.float32),
    }


def process_and_save_indices(
    cloud_masked_scenes: Dict[str, Dict[str, Path]],
    output_base_dir: Path = Path("data/processed/indices"),
    stats_report_path: Path = Path("data/validation/index_statistics.csv"),
    nodata_val: float = -9999.0,
) -> Tuple[Dict[str, Dict[str, Path]], pd.DataFrame]:
    """
    Calculate and save all indices for all dates, and export summary statistics.
    """
    print("\n[INDICES] Calculating NDVI, EVI, SAVI, NDWI for all dates...")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    stats_report_path.parent.mkdir(parents=True, exist_ok=True)

    indices_scenes = {}
    stats_rows = []

    for date_str, bands in cloud_masked_scenes.items():
        date_dir = output_base_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        date_indices_paths = {}

        with rasterio.open(bands["B08"]) as src:
            ref_profile = src.profile.copy()
            b08 = src.read(1)

        with rasterio.open(bands["B02"]) as src:
            b02 = src.read(1)
        with rasterio.open(bands["B03"]) as src:
            b03 = src.read(1)
        with rasterio.open(bands["B04"]) as src:
            b04 = src.read(1)

        computed = compute_all_indices(b02, b03, b04, b08, nodata_val=nodata_val)

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

        for idx_name, idx_arr in computed.items():
            out_idx_file = date_dir / f"{idx_name}.tif"

            with rasterio.open(out_idx_file, "w", **ref_profile) as dst:
                dst.write(idx_arr, 1)

            date_indices_paths[idx_name] = out_idx_file

            # Compute statistics on valid pixels
            valid_vals = idx_arr[(idx_arr != nodata_val) & (~np.isnan(idx_arr))]
            val_count = int(len(valid_vals))
            if val_count > 0:
                min_v = float(np.min(valid_vals))
                max_v = float(np.max(valid_vals))
                mean_v = float(np.mean(valid_vals))
                median_v = float(np.median(valid_vals))
                std_v = float(np.std(valid_vals))
            else:
                min_v, max_v, mean_v, median_v, std_v = (np.nan, np.nan, np.nan, np.nan, np.nan)

            stats_rows.append({
                "date": date_str,
                "index_name": idx_name,
                "valid_pixel_count": val_count,
                "min": round(min_v, 4) if not np.isnan(min_v) else np.nan,
                "max": round(max_v, 4) if not np.isnan(max_v) else np.nan,
                "mean": round(mean_v, 4) if not np.isnan(mean_v) else np.nan,
                "median": round(median_v, 4) if not np.isnan(median_v) else np.nan,
                "std": round(std_v, 4) if not np.isnan(std_v) else np.nan,
            })

            print(f"  * Date {date_str} - {idx_name:<5}: Mean={mean_v:.4f}, Median={median_v:.4f}, Valid={val_count} px")

        indices_scenes[date_str] = date_indices_paths

    df_stats = pd.DataFrame(stats_rows)
    df_stats.to_csv(stats_report_path, index=False)
    print(f"  [OK] Saved index statistics to: {stats_report_path.name}")

    return indices_scenes, df_stats
