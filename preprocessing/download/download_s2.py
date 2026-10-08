"""
Sentinel-2 L2A Data Acquisition and Organization Helper.
Manages input data structure for Tirunelveli Study Area (Ambasamudram and Cheranmahadevi Taluks).
Coordinates and catalogs raw SAFE / GeoTIFF granules from Copernicus / Planetary Computer / Google Drive.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import re
import shutil


# Sentinel-2 Tile Covering Tirunelveli / Ambasamudram / Cheranmahadevi
TARGET_MGRS_TILES = ["43KGS", "43KFS"]
DEFAULT_TARGET_CRS = "EPSG:32643"

# Key Spectral Bands for Agricultural Identification
ESSENTIAL_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]


def organize_sentinel2_bands(
    raw_folder_path: Union[str, Path],
    output_organized_dir: Union[str, Path],
    date_str: Optional[str] = None,
) -> Dict[str, Path]:
    """
    Scan a directory for Sentinel-2 JP2/GeoTIFF files and organize them
    into a structured date folder with standard band keys: B02, B03, B04, B08, B11, B12, SCL.
    """
    raw_path = Path(raw_folder_path)
    out_dir = Path(output_organized_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    found_bands = {}

    if not raw_path.exists():
        return found_bands

    # Regex patterns for standard band files (e.g. T43KGS_20240115T051031_B02_10m.jp2 or B02.tif)
    for band_key in ESSENTIAL_BANDS:
        pattern = re.compile(rf"(?:.*[_\-\./])?({band_key})(?:_[12]0m)?\.(tif|tiff|jp2)$", re.IGNORECASE)
        for f in raw_path.rglob("*"):
            if f.is_file() and pattern.search(f.name):
                found_bands[band_key] = f
                break

    return found_bands
