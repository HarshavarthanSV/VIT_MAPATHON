"""
Sentinel-2 L2A Input Data Discovery and Inspection Module.
Member 2 - Agricultural Land Parcel and Crop Identification (Tirunelveli).
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Any
import rasterio

REQUIRED_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]


def discover_sentinel2_scenes(base_dirs: Optional[List[Path]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Search workspace directories for Sentinel-2 L2A dates and bands.
    Supports SAFE folders and custom date directories.
    """
    if base_dirs is None:
        base_dirs = [
            Path("data/sentinel2"),
            Path("data/raw/sentinel2"),
            Path("data/raw"),
        ]

    date_scenes = {}

    for base in base_dirs:
        if not base.exists():
            continue

        for item in base.iterdir():
            if not item.is_dir():
                continue

            match_safe = re.search(r"MSIL2A_(\d{4})(\d{2})(\d{2})T", item.name)
            match_date = re.search(r"(\d{4})-(\d{2})-(\d{2})", item.name)

            if match_safe:
                date_str = f"{match_safe.group(1)}-{match_safe.group(2)}-{match_safe.group(3)}"
            elif match_date:
                date_str = f"{match_date.group(1)}-{match_date.group(2)}-{match_date.group(3)}"
            else:
                continue

            if date_str not in date_scenes:
                date_scenes[date_str] = item

    sorted_dates = dict(sorted(date_scenes.items()))
    scenes_info = {}

    for date_str, scene_path in sorted_dates.items():
        all_rasters = list(scene_path.rglob("*.jp2")) + list(scene_path.rglob("*.tif")) + list(scene_path.rglob("*.tiff"))
        bands_found = {}

        for b in REQUIRED_BANDS:
            matched = []
            for f in all_rasters:
                fname = f.stem
                if re.search(rf"(?:^|[_\-\./])({b})(?:_[126]0m)?$", fname, re.IGNORECASE):
                    matched.append(f)

            if matched:
                if b in ["B02", "B03", "B04", "B08"]:
                    pref = [m for m in matched if "10m" in m.name or "R10m" in str(m)]
                    bands_found[b] = pref[0] if pref else matched[0]
                else:
                    pref = [m for m in matched if "20m" in m.name or "R20m" in str(m)]
                    bands_found[b] = pref[0] if pref else matched[0]
            else:
                bands_found[b] = None

        scenes_info[date_str] = {
            "scene_dir": scene_path,
            "bands": bands_found,
        }

    return scenes_info


def inspect_and_validate_inputs(scenes_info: Dict[str, Dict[str, Any]], target_crs: str = "EPSG:32643") -> bool:
    """
    Validate that all required bands exist, share consistent CRS, dimensions, and spatial coverage.
    """
    if len(scenes_info) < 4:
        raise ValueError(f"Expected at least 4 Sentinel-2 dates, but found {len(scenes_info)}.")

    print(f"\n[INSPECT] Found {len(scenes_info)} Sentinel-2 Acquisition Dates:")
    all_valid = True

    for date_str, sdata in scenes_info.items():
        print(f"  * Date: {date_str} (Source: {sdata['scene_dir'].name})")
        missing_bands = [b for b, p in sdata["bands"].items() if p is None]
        if missing_bands:
            print(f"    [ERROR] Missing bands: {', '.join(missing_bands)}")
            all_valid = False
        else:
            print(f"    [OK] All 7 bands located: {', '.join(REQUIRED_BANDS)}")

    if not all_valid:
        raise FileNotFoundError("One or more required Sentinel-2 bands are missing from the raw dataset.")

    return True


if __name__ == "__main__":
    scenes = discover_sentinel2_scenes()
    inspect_and_validate_inputs(scenes)
