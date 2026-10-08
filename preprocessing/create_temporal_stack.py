"""
Temporal Feature Stacking and Temporal Statistics Module.
Builds the 60-layer multi-temporal feature stack GeoTIFF and metadata JSON for Member 1 ML Handoff.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
import json
import numpy as np
import rasterio

FEATURE_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]
FEATURE_INDICES = ["NDVI", "EVI", "SAVI", "NDWI"]


def compute_temporal_index_statistics(
    index_arrays_by_date: Dict[str, np.ndarray],
    nodata_val: float = -9999.0,
) -> Dict[str, np.ndarray]:
    """
    Compute mean, min, max, std, and range across all acquisition dates for an index.
    Masks nodata pixels during calculation.
    """
    date_arrays = list(index_arrays_by_date.values())
    stacked = np.stack(date_arrays, axis=0)  # (N_dates, H, W)

    # Valid mask where values are not nodata and not NaN
    valid_mask = (stacked != nodata_val) & (~np.isnan(stacked))

    # Replace invalid entries with NaN for nan-aware numpy computations
    masked_stack = np.where(valid_mask, stacked, np.nan)

    with np.errstate(divide="ignore", invalid="ignore"):
        t_mean = np.nanmean(masked_stack, axis=0)
        t_min = np.nanmin(masked_stack, axis=0)
        t_max = np.nanmax(masked_stack, axis=0)
        t_std = np.nanstd(masked_stack, axis=0)
        t_range = t_max - t_min

    # Re-apply nodata to pixels where all dates were invalid
    all_invalid = np.all(~valid_mask, axis=0)

    t_mean[all_invalid] = nodata_val
    t_min[all_invalid] = nodata_val
    t_max[all_invalid] = nodata_val
    t_std[all_invalid] = nodata_val
    t_range[all_invalid] = nodata_val

    # Replace any leftover NaNs
    t_mean = np.nan_to_num(t_mean, nan=nodata_val).astype(np.float32)
    t_min = np.nan_to_num(t_min, nan=nodata_val).astype(np.float32)
    t_max = np.nan_to_num(t_max, nan=nodata_val).astype(np.float32)
    t_std = np.nan_to_num(t_std, nan=nodata_val).astype(np.float32)
    t_range = np.nan_to_num(t_range, nan=nodata_val).astype(np.float32)

    return {
        "mean": t_mean,
        "min": t_min,
        "max": t_max,
        "std": t_std,
        "range": t_range,
    }


def build_temporal_feature_stack(
    cloud_masked_scenes: Dict[str, Dict[str, Path]],
    indices_scenes: Dict[str, Dict[str, Path]],
    output_stack_tiff: Path = Path("data/features/raster_stack/temporal_feature_stack.tif"),
    output_metadata_json: Path = Path("data/features/temporal/feature_metadata.json"),
    nodata_val: float = -9999.0,
) -> Tuple[Path, Path, List[str]]:
    """
    Construct the unified 60-channel temporal feature stack combining:
    - 40 per-date spectral & index bands (10 features x 4 dates)
    - 20 multi-temporal summary index features (5 stats x 4 indices)
    """
    print("\n[FEATURE STACK] Building 60-layer multi-temporal feature stack...")
    output_stack_tiff.parent.mkdir(parents=True, exist_ok=True)
    output_metadata_json.parent.mkdir(parents=True, exist_ok=True)

    sorted_dates = sorted(list(cloud_masked_scenes.keys()))
    first_date = sorted_dates[0]
    ref_b08_path = cloud_masked_scenes[first_date]["B08"]

    with rasterio.open(ref_b08_path) as ref_src:
        ref_profile = ref_src.profile.copy()
        height, width = ref_src.height, ref_src.width

    all_features: Dict[str, np.ndarray] = {}
    index_arrays_for_stats: Dict[str, Dict[str, np.ndarray]] = {idx: {} for idx in FEATURE_INDICES}

    # 1. Per-date features (40 layers)
    for date_str in sorted_dates:
        # Load 6 spectral bands
        for b_name in FEATURE_BANDS:
            b_path = cloud_masked_scenes[date_str][b_name]
            with rasterio.open(b_path) as src:
                arr = src.read(1).astype(np.float32)
                # Scale BOA to reflectance if not already scaled
                valid_m = (arr != nodata_val) & (~np.isnan(arr)) & (arr > 0)
                if np.any(valid_m) and np.nanmax(arr[valid_m]) > 2.0:
                    arr = np.where(valid_m, arr / 10000.0, nodata_val)
                feat_name = f"{date_str}_{b_name}"
                all_features[feat_name] = arr

        # Load 4 spectral indices
        for idx_name in FEATURE_INDICES:
            idx_path = indices_scenes[date_str][idx_name]
            with rasterio.open(idx_path) as src:
                arr = src.read(1).astype(np.float32)
                feat_name = f"{date_str}_{idx_name}"
                all_features[feat_name] = arr
                index_arrays_for_stats[idx_name][date_str] = arr

    # 2. Multi-temporal summary index features (20 layers)
    print("  * Calculating multi-temporal summary features (mean, min, max, std, range)...")
    for idx_name in FEATURE_INDICES:
        stats_dict = compute_temporal_index_statistics(index_arrays_for_stats[idx_name], nodata_val=nodata_val)
        for stat_name, stat_arr in stats_dict.items():
            feat_name = f"{idx_name}_temporal_{stat_name}"
            all_features[feat_name] = stat_arr

    num_bands = len(all_features)
    feature_names = list(all_features.keys())
    print(f"  * Total Feature Stack Layers: {num_bands} channels")

    # Update raster profile
    ref_profile.update({
        "driver": "GTiff",
        "count": num_bands,
        "dtype": "float32",
        "nodata": nodata_val,
        "compress": "lzw",
    })

    if width >= 256 and height >= 256:
        ref_profile.update({"tiled": True, "blockxsize": 256, "blockysize": 256})
    else:
        ref_profile.pop("tiled", None)
        ref_profile.pop("blockxsize", None)
        ref_profile.pop("blockysize", None)

    with rasterio.open(output_stack_tiff, "w", **ref_profile) as dst:
        for idx, (f_name, f_arr) in enumerate(all_features.items(), start=1):
            clean_arr = np.nan_to_num(f_arr, nan=nodata_val).astype(np.float32)
            dst.write(clean_arr, idx)
            dst.set_band_description(idx, f_name)

        dst.update_tags(
            DATES=",".join(sorted_dates),
            NUM_BANDS=str(num_bands),
            CRS=str(ref_profile.get("crs", "EPSG:32643")),
        )

    # Save feature metadata JSON
    metadata = {
        "geotiff_file": output_stack_tiff.name,
        "dates": sorted_dates,
        "total_features": num_bands,
        "crs": str(ref_profile.get("crs", "EPSG:32643")),
        "dimensions": {"width": width, "height": height},
        "resolution_meters": [10.0, 10.0],
        "nodata_value": nodata_val,
        "feature_list": feature_names,
        "feature_index_mapping": {idx: name for idx, name in enumerate(feature_names, start=1)},
        "index_formulas": {
            "NDVI": "(B08 - B04) / (B08 + B04)",
            "EVI": "2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)",
            "SAVI": "1.5 * (B08 - B04) / (B08 + B04 + 0.5)",
            "NDWI": "(B03 - B08) / (B03 + B08)",
        },
        "temporal_statistics_calculated": ["mean", "min", "max", "std", "range"],
    }

    with open(output_metadata_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"  [OK] Saved GeoTIFF stack: {output_stack_tiff.resolve()}")
    print(f"  [OK] Saved metadata JSON: {output_metadata_json.resolve()}")

    return output_stack_tiff, output_metadata_json, feature_names
