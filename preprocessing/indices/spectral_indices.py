"""
Spectral Indices Calculation Module for Sentinel-2 Level-2A Imagery.
Supports: NDVI, EVI, SAVI, NDWI (Moisture & Water).
Handles NoData, division by zero, and invalid pixel values safely.
"""

from pathlib import Path
from typing import Optional, Union, Dict
import numpy as np
import rasterio


def safe_divide(numerator: np.ndarray, denominator: np.ndarray, fill_value: float = np.nan) -> np.ndarray:
    """Safely divide two numpy arrays handling zeros, NaNs, and infinite values."""
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(np.abs(denominator) > 1e-7, numerator / denominator, fill_value)
    return result


def normalize_reflectance(band: np.ndarray) -> np.ndarray:
    """
    Ensure band reflectance values are in standard floating point range [0.0, 1.0].
    Sentinel-2 L2A BOA digital numbers are typically scaled by 10000 (0 - 10000).
    """
    band_float = band.astype(np.float32)
    # If max value exceeds 2.0, it's unscaled DN (0 - 10000)
    valid_mask = ~np.isnan(band_float)
    if np.any(valid_mask) and np.nanmax(band_float) > 2.0:
        band_float = band_float / 10000.0
    return band_float


def compute_ndvi(nir: np.ndarray, red: np.ndarray, nodata_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Normalized Difference Vegetation Index (NDVI)
    NDVI = (NIR - Red) / (NIR + Red)
    Sentinel-2: (B08 - B04) / (B08 + B04)
    Range: [-1.0, 1.0]
    """
    nir_f = normalize_reflectance(nir)
    red_f = normalize_reflectance(red)

    num = nir_f - red_f
    den = nir_f + red_f

    ndvi = safe_divide(num, den, fill_value=np.nan)
    ndvi = np.clip(ndvi, -1.0, 1.0)

    if nodata_mask is not None:
        ndvi[nodata_mask] = np.nan

    return ndvi.astype(np.float32)


def compute_evi(
    nir: np.ndarray,
    red: np.ndarray,
    blue: np.ndarray,
    g: float = 2.5,
    c1: float = 6.0,
    c2: float = 7.5,
    l: float = 1.0,
    nodata_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Enhanced Vegetation Index (EVI)
    EVI = G * ((NIR - Red) / (NIR + C1 * Red - C2 * Blue + L))
    Sentinel-2: 2.5 * ((B08 - B04) / (B08 + 6.0 * B04 - 7.5 * B02 + 1.0))
    Optimized for high biomass areas like paddy and banana plantations.
    Range: [-1.0, 1.5]
    """
    nir_f = normalize_reflectance(nir)
    red_f = normalize_reflectance(red)
    blue_f = normalize_reflectance(blue)

    num = nir_f - red_f
    den = nir_f + (c1 * red_f) - (c2 * blue_f) + l

    evi = g * safe_divide(num, den, fill_value=np.nan)
    evi = np.clip(evi, -1.5, 1.5)

    if nodata_mask is not None:
        evi[nodata_mask] = np.nan

    return evi.astype(np.float32)


def compute_savi(
    nir: np.ndarray,
    red: np.ndarray,
    l: float = 0.5,
    nodata_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Soil Adjusted Vegetation Index (SAVI)
    SAVI = ((NIR - Red) / (NIR + Red + L)) * (1.0 + L)
    Sentinel-2: ((B08 - B04) / (B08 + B04 + 0.5)) * 1.5
    Crucial for early stage paddy/transplanting where soil background is prominent.
    Range: [-1.0, 1.0]
    """
    nir_f = normalize_reflectance(nir)
    red_f = normalize_reflectance(red)

    num = nir_f - red_f
    den = nir_f + red_f + l

    savi = safe_divide(num, den, fill_value=np.nan) * (1.0 + l)
    savi = np.clip(savi, -1.0, 1.0)

    if nodata_mask is not None:
        savi[nodata_mask] = np.nan

    return savi.astype(np.float32)


def compute_ndwi(
    nir: np.ndarray,
    swir: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Normalized Difference Water Index (NDWI - Gao / Moisture)
    NDWI = (NIR - SWIR1) / (NIR + SWIR1)
    Sentinel-2: (B08 - B11) / (B08 + B11)
    Reflects canopy water content; essential for differentiating flooded paddy fields vs banana plantations.
    Range: [-1.0, 1.0]
    """
    nir_f = normalize_reflectance(nir)
    swir_f = normalize_reflectance(swir)

    num = nir_f - swir_f
    den = nir_f + swir_f

    ndwi = safe_divide(num, den, fill_value=np.nan)
    ndwi = np.clip(ndwi, -1.0, 1.0)

    if nodata_mask is not None:
        ndwi[nodata_mask] = np.nan

    return ndwi.astype(np.float32)


def compute_mndwi(
    green: np.ndarray,
    swir: np.ndarray,
    nodata_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Modified Normalized Difference Water Index (MNDWI - Xu)
    MNDWI = (Green - SWIR1) / (Green + SWIR1)
    Sentinel-2: (B03 - B11) / (B03 + B11)
    Open surface water extraction for irrigation canals, ponds, and river network (Tamirabarani River basin).
    Range: [-1.0, 1.0]
    """
    green_f = normalize_reflectance(green)
    swir_f = normalize_reflectance(swir)

    num = green_f - swir_f
    den = green_f + swir_f

    mndwi = safe_divide(num, den, fill_value=np.nan)
    mndwi = np.clip(mndwi, -1.0, 1.0)

    if nodata_mask is not None:
        mndwi[nodata_mask] = np.nan

    return mndwi.astype(np.float32)


def calculate_all_indices(bands: Dict[str, np.ndarray], nodata_mask: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
    """
    Calculate all available spectral indices given a dictionary of band arrays.
    Required bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), and optionally B11 (SWIR1).
    """
    indices = {}

    has_nir = "B08" in bands
    has_red = "B04" in bands
    has_blue = "B02" in bands
    has_green = "B03" in bands
    has_swir = "B11" in bands

    if has_nir and has_red:
        indices["NDVI"] = compute_ndvi(bands["B08"], bands["B04"], nodata_mask=nodata_mask)
        indices["SAVI"] = compute_savi(bands["B08"], bands["B04"], nodata_mask=nodata_mask)

    if has_nir and has_red and has_blue:
        indices["EVI"] = compute_evi(bands["B08"], bands["B04"], bands["B02"], nodata_mask=nodata_mask)

    if has_nir and has_swir:
        indices["NDWI"] = compute_ndwi(bands["B08"], bands["B11"], nodata_mask=nodata_mask)

    if has_green and has_swir:
        indices["MNDWI"] = compute_mndwi(bands["B03"], bands["B11"], nodata_mask=nodata_mask)

    return indices


def save_index_geotiff(
    index_array: np.ndarray,
    output_path: Union[str, Path],
    profile: dict,
    nodata_val: float = -9999.0,
    extra_tags: Optional[dict] = None,
) -> Path:
    """
    Save a single spectral index array as a QGIS-compatible GeoTIFF with full georeference metadata.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    out_height = index_array.shape[0]
    out_width = index_array.shape[1]

    out_profile = profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "height": out_height,
        "width": out_width,
        "nodata": nodata_val,
        "compress": "lzw",
    })

    if out_width >= 256 and out_height >= 256:
        out_profile.update({
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        })
    else:
        out_profile.pop("tiled", None)
        out_profile.pop("blockxsize", None)
        out_profile.pop("blockysize", None)

    # Replace NaNs with nodata_val
    data_to_write = np.nan_to_num(index_array, nan=nodata_val).astype(np.float32)

    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(data_to_write, 1)
        if extra_tags:
            dst.update_tags(**extra_tags)

    return output_path
