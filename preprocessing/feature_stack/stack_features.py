"""
Feature Stacking and Multi-Temporal Aggregation Module.
Creates unified multi-band feature stacks combining:
- Spectral bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR1), B12 (SWIR2)
- Spectral indices: NDVI, EVI, SAVI, NDWI, MNDWI
- Multi-temporal features across multiple Sentinel-2 acquisition dates.
Exports QGIS-compatible GeoTIFFs, JSON metadata, and CSV sample tables for ML handoff (Member 1).
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import json
import numpy as np
import pandas as pd
import rasterio


def stack_bands_and_indices(
    band_arrays: Dict[str, np.ndarray],
    output_geotiff_path: Union[str, Path],
    profile: dict,
    acquisition_date: Optional[str] = None,
    nodata_val: float = -9999.0,
) -> Tuple[Path, Path]:
    """
    Stack all provided 2D arrays into a single multi-band GeoTIFF.
    Generates a companion JSON metadata file describing band orders and channels.
    """
    out_tiff = Path(output_geotiff_path)
    out_json = out_tiff.with_suffix(".json")
    out_tiff.parent.mkdir(parents=True, exist_ok=True)

    band_names = list(band_arrays.keys())
    num_bands = len(band_names)

    first_array = next(iter(band_arrays.values()))
    height, width = first_array.shape

    out_profile = profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "count": num_bands,
        "dtype": "float32",
        "height": height,
        "width": width,
        "nodata": nodata_val,
        "compress": "lzw",
    })

    if width >= 256 and height >= 256:
        out_profile.update({
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        })
    else:
        out_profile.pop("tiled", None)
        out_profile.pop("blockxsize", None)
        out_profile.pop("blockysize", None)

    with rasterio.open(out_tiff, "w", **out_profile) as dst:
        for idx, (b_name, b_arr) in enumerate(band_arrays.items(), start=1):
            if b_arr.shape != (height, width):
                raise ValueError(f"Band {b_name} shape {b_arr.shape} does not match expected ({height}, {width}).")

            # Replace NaNs with nodata_val
            clean_arr = np.nan_to_num(b_arr, nan=nodata_val).astype(np.float32)
            dst.write(clean_arr, idx)
            dst.set_band_description(idx, b_name)

        # Update raster tags
        tags = {
            "BAND_NAMES": ",".join(band_names),
            "NUM_BANDS": str(num_bands),
            "CRS": str(profile.get("crs", "EPSG:32643")),
        }
        if acquisition_date:
            tags["ACQUISITION_DATE"] = acquisition_date
        dst.update_tags(**tags)

    # Save metadata JSON for Member 1 ML pipeline
    metadata = {
        "geotiff_file": out_tiff.name,
        "acquisition_date": acquisition_date,
        "crs": str(profile.get("crs", "EPSG:32643")),
        "transform": list(profile.get("transform", [])) if profile.get("transform") else None,
        "height": height,
        "width": width,
        "resolution_meters": [
            abs(profile["transform"][0]) if profile.get("transform") else 10.0,
            abs(profile["transform"][4]) if profile.get("transform") else 10.0,
        ],
        "nodata_value": nodata_val,
        "num_bands": num_bands,
        "band_order": {idx: name for idx, name in enumerate(band_names, start=1)},
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return out_tiff, out_json


def create_multitemporal_stack(
    temporal_stacks: Dict[str, Dict[str, np.ndarray]],
    output_geotiff_path: Union[str, Path],
    profile: dict,
    nodata_val: float = -9999.0,
) -> Tuple[Path, Path]:
    """
    Combine feature stacks from multiple acquisition dates into a multi-temporal stack.
    temporal_stacks format:
    {
        "2024-01-15": {"B02": arr, "B03": arr, "NDVI": arr, ...},
        "2024-02-15": {"B02": arr, "B03": arr, "NDVI": arr, ...},
        ...
    }
    """
    out_tiff = Path(output_geotiff_path)
    out_json = out_tiff.with_suffix(".json")
    out_tiff.parent.mkdir(parents=True, exist_ok=True)

    flattened_bands = {}
    for date_str, bands_dict in sorted(temporal_stacks.items()):
        for b_name, arr in bands_dict.items():
            flattened_name = f"{date_str}_{b_name}"
            flattened_bands[flattened_name] = arr

    num_bands = len(flattened_bands)
    first_arr = next(iter(flattened_bands.values()))
    height, width = first_arr.shape

    out_profile = profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "count": num_bands,
        "dtype": "float32",
        "height": height,
        "width": width,
        "nodata": nodata_val,
        "compress": "lzw",
    })

    if width >= 256 and height >= 256:
        out_profile.update({
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        })
    else:
        out_profile.pop("tiled", None)
        out_profile.pop("blockxsize", None)
        out_profile.pop("blockysize", None)

    with rasterio.open(out_tiff, "w", **out_profile) as dst:
        for idx, (b_name, b_arr) in enumerate(flattened_bands.items(), start=1):
            clean_arr = np.nan_to_num(b_arr, nan=nodata_val).astype(np.float32)
            dst.write(clean_arr, idx)
            dst.set_band_description(idx, b_name)

        dst.update_tags(
            DATES=",".join(sorted(temporal_stacks.keys())),
            NUM_BANDS=str(num_bands),
            CRS=str(profile.get("crs", "EPSG:32643")),
        )

    metadata = {
        "geotiff_file": out_tiff.name,
        "acquisition_dates": sorted(list(temporal_stacks.keys())),
        "crs": str(profile.get("crs", "EPSG:32643")),
        "height": height,
        "width": width,
        "nodata_value": nodata_val,
        "num_bands": num_bands,
        "band_order": {idx: name for idx, name in enumerate(flattened_bands.keys(), start=1)},
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return out_tiff, out_json


def extract_tabular_training_features(
    feature_stack_path: Union[str, Path],
    labels_raster_or_vector_path: Union[str, Path],
    output_csv_path: Union[str, Path],
    class_mapping: Optional[Dict[int, str]] = None,
    nodata_val: float = -9999.0,
) -> Path:
    """
    Extract pixel feature vectors from a feature stack corresponding to training labels.
    Prepares clean CSV dataset for Member 1 (ML/Random Forest).
    """
    import geopandas as gpd
    from rasterio.features import geometry_mask

    feat_path = Path(feature_stack_path)
    out_csv = Path(output_csv_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(feat_path) as src:
        band_count = src.count
        band_names = [src.descriptions[i - 1] or f"Band_{i}" for i in range(1, band_count + 1)]
        feat_data = src.read()  # (C, H, W)
        transform = src.transform
        crs = src.crs

    labels_path = Path(labels_raster_or_vector_path)
    if labels_path.suffix.lower() in [".geojson", ".shp", ".gpkg", ".json"]:
        gdf = gpd.read_file(labels_path)
        if gdf.crs != crs:
            gdf = gdf.to_crs(crs)

        records = []
        for _, row in gdf.iterrows():
            geom = row.geometry
            label = row.get("crop_type", row.get("label", row.get("class", "unknown")))
            class_id = row.get("class_id", 1)

            # Mask geometry
            mask = geometry_mask([geom], out_shape=feat_data.shape[1:], transform=transform, invert=True)
            valid_pixels = np.where(mask)

            for r, c in zip(valid_pixels[0], valid_pixels[1]):
                pixel_vals = feat_data[:, r, c]
                if not np.any(pixel_vals == nodata_val) and not np.any(np.isnan(pixel_vals)):
                    row_dict = {
                        "row": int(r),
                        "col": int(c),
                        "class_id": class_id,
                        "crop_name": label,
                    }
                    for b_idx, b_name in enumerate(band_names):
                        row_dict[b_name] = float(pixel_vals[b_idx])
                    records.append(row_dict)

        df = pd.DataFrame(records)
        df.to_csv(out_csv, index=False)

    return out_csv
