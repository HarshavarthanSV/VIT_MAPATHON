"""
Cloud and Shadow Masking Module for Sentinel-2 Level-2A Imagery.
Supports Scene Classification Layer (SCL) filtering and QA60 band masking.
"""

from pathlib import Path
from typing import Optional, Union, Tuple, List
import numpy as np
import rasterio

# SCL classification classes
SCL_NO_DATA = 0
SCL_SATURATED = 1
SCL_DARK_AREA = 2
SCL_CLOUD_SHADOW = 3
SCL_VEGETATION = 4
SCL_NOT_VEGETATED = 5
SCL_WATER = 6
SCL_UNCLASSIFIED = 7
SCL_CLOUD_MED_PROB = 8
SCL_CLOUD_HIGH_PROB = 9
SCL_THIN_CIRRUS = 10
SCL_SNOW_ICE = 11

# Default invalid classes to mask out for agriculture & crop monitoring
DEFAULT_MASK_CLASSES = [
    SCL_NO_DATA,
    SCL_SATURATED,
    SCL_CLOUD_SHADOW,
    SCL_CLOUD_MED_PROB,
    SCL_CLOUD_HIGH_PROB,
    SCL_THIN_CIRRUS,
]


def create_cloud_mask_from_scl(
    scl_array: np.ndarray,
    mask_classes: Optional[List[int]] = None,
) -> np.ndarray:
    """
    Create a boolean cloud/shadow mask from Sentinel-2 SCL (Scene Classification Layer).
    Returns True for invalid/cloud/shadow pixels (to be masked), False for valid clear pixels.
    """
    if mask_classes is None:
        mask_classes = DEFAULT_MASK_CLASSES

    # isin check returns boolean array
    invalid_mask = np.isin(scl_array, mask_classes)
    return invalid_mask


def create_cloud_mask_from_qa60(qa60_array: np.ndarray) -> np.ndarray:
    """
    Create a boolean cloud mask from Sentinel-2 QA60 band.
    Bit 10: Opaque clouds
    Bit 11: Cirrus clouds
    Returns True for cloudy/cirrus pixels.
    """
    opaque_cloud_bit = 1 << 10
    cirrus_cloud_bit = 1 << 11

    is_opaque = (qa60_array & opaque_cloud_bit) != 0
    is_cirrus = (qa60_array & cirrus_cloud_bit) != 0

    return is_opaque | is_cirrus


def apply_cloud_mask_to_band(
    band_array: np.ndarray,
    cloud_mask: np.ndarray,
    nodata_value: float = np.nan,
) -> np.ndarray:
    """
    Apply a boolean cloud mask to a band array, setting cloudy pixels to nodata_value (default NaN).
    """
    band_masked = band_array.astype(np.float32).copy()
    band_masked[cloud_mask] = nodata_value
    return band_masked


def mask_raster_file(
    input_raster_path: Union[str, Path],
    scl_raster_path: Union[str, Path],
    output_raster_path: Union[str, Path],
    mask_classes: Optional[List[int]] = None,
    nodata_val: float = -9999.0,
) -> Path:
    """
    Read an input raster and SCL band, apply cloud mask, and write out clean GeoTIFF.
    """
    input_path = Path(input_raster_path)
    scl_path = Path(scl_raster_path)
    out_path = Path(output_raster_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(scl_path) as scl_src:
        scl_data = scl_src.read(1)

    cloud_mask = create_cloud_mask_from_scl(scl_data, mask_classes=mask_classes)

    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        num_bands = src.count

        profile.update({
            "dtype": "float32",
            "nodata": nodata_val,
            "compress": "lzw",
        })

        with rasterio.open(out_path, "w", **profile) as dst:
            for b_idx in range(1, num_bands + 1):
                band_data = src.read(b_idx).astype(np.float32)
                band_masked = apply_cloud_mask_to_band(band_data, cloud_mask, nodata_value=nodata_val)
                dst.write(band_masked, b_idx)

    return out_path
