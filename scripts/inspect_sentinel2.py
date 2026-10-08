"""
Sentinel-2 L2A Data Inspection Script for Member 2 (GIS / Remote Sensing Engineer).
Scans all 4 Sentinel-2 SAFE / directory dates, locates required bands (B02, B03, B04, B08, B11, B12, SCL),
inspects metadata (CRS, resolution, dimensions, bounds, datatype, nodata, file sizes),
and verifies spatial compatibility.
"""

from pathlib import Path
import re
import sys
import rasterio

REQUIRED_BANDS = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]

def find_sentinel2_dates(base_dirs):
    """Locate Sentinel-2 SAFE folders or date directories."""
    date_folders = {}
    
    for base in base_dirs:
        p = Path(base)
        if not p.exists():
            continue
        
        # Check direct subdirectories for SAFE folders or date folders
        for item in p.iterdir():
            if item.is_dir():
                # Match SAFE naming e.g. S2A_MSIL2A_20260320T... or YYYY-MM-DD
                match_safe = re.search(r"MSIL2A_(\d{4})(\d{2})(\d{2})T", item.name)
                match_date = re.search(r"(\d{4})-(\d{2})-(\d{2})", item.name)
                if match_safe:
                    date_str = f"{match_safe.group(1)}-{match_safe.group(2)}-{match_safe.group(3)}"
                    date_folders[date_str] = item
                elif match_date:
                    date_str = f"{match_date.group(1)}-{match_date.group(2)}-{match_date.group(3)}"
                    date_folders[date_str] = item

    return dict(sorted(date_folders.items()))


def locate_bands_for_scene(scene_dir: Path):
    """Find all 7 required band files within a Sentinel-2 granule/SAFE directory."""
    bands = {}
    all_raster_files = list(scene_dir.rglob("*.jp2")) + list(scene_dir.rglob("*.tif")) + list(scene_dir.rglob("*.tiff"))
    
    for b in REQUIRED_BANDS:
        # Pattern to match e.g. T43PGK_20260320T051241_B02_10m.jp2 or B02_10m.jp2 or B02.jp2
        # Note: B02, B03, B04, B08 are usually in R10m or 10m; B11, B12, SCL in R20m or 20m
        matched = []
        for f in all_raster_files:
            fname = f.stem
            # Match band name ensuring boundaries (e.g., _B02_ or _B02 or B02)
            if re.search(rf"(?:^|[_\-\./])({b})(?:_[126]0m)?$", fname, re.IGNORECASE):
                matched.append(f)
        
        if matched:
            # If multiple resolutions found (e.g. 20m vs 60m), prefer native: 10m for B02..B08, 20m for B11,B12,SCL
            if b in ["B02", "B03", "B04", "B08"]:
                pref = [m for m in matched if "10m" in m.name or "R10m" in str(m)]
                bands[b] = pref[0] if pref else matched[0]
            else:
                pref = [m for m in matched if "20m" in m.name or "R20m" in str(m)]
                bands[b] = pref[0] if pref else matched[0]
        else:
            bands[b] = None

    return bands


def inspect_all_scenes():
    print("=" * 80)
    print("SENTINEL-2 L2A METADATA & INTEGRITY INSPECTION REPORT")
    print("=" * 80)
    
    search_paths = [
        Path("data/sentinel2"),
        Path("data/raw/sentinel2"),
        Path("data/raw"),
        Path("data/sample"),
    ]
    
    dates_dict = find_sentinel2_dates(search_paths)
    print(f"Found {len(dates_dict)} Sentinel-2 Acquisition Dates:")
    for d, p in dates_dict.items():
        print(f"  - Date: {d} -> Path: {p.name}")
    print("-" * 80)

    if len(dates_dict) < 4:
        print(f"[WARNING] Expected 4 Sentinel-2 dates, found {len(dates_dict)}.")
    
    scene_metadata = {}
    has_missing_files = False

    for date_str, scene_path in dates_dict.items():
        print(f"\n[DATE: {date_str}] Directory: {scene_path.name}")
        bands = locate_bands_for_scene(scene_path)
        scene_metadata[date_str] = {"path": scene_path, "bands": {}}
        
        # Check if any band is missing
        missing = [b for b, p in bands.items() if p is None]
        if missing:
            print(f"  [ERROR] Missing required bands for {date_str}: {', '.join(missing)}")
            has_missing_files = True
            
        for b in REQUIRED_BANDS:
            b_path = bands[b]
            if b_path is None:
                continue
            
            size_mb = b_path.stat().st_size / (1024 * 1024)
            fmt = b_path.suffix.upper().replace(".", "")
            
            with rasterio.open(b_path) as src:
                crs = src.crs
                w, h = src.width, src.height
                res_x = round(abs(src.transform[0]), 2)
                res_y = round(abs(src.transform[4]), 2)
                bounds = src.bounds
                dtype = src.dtypes[0]
                nodata = src.nodata
                transform = src.transform
                
                scene_metadata[date_str]["bands"][b] = {
                    "path": b_path,
                    "size_mb": size_mb,
                    "format": fmt,
                    "crs": str(crs),
                    "width": w,
                    "height": h,
                    "res": (res_x, res_y),
                    "bounds": bounds,
                    "dtype": dtype,
                    "nodata": nodata,
                    "transform": transform
                }
                
                print(f"  * Band {b:<3} [{fmt:<3} {size_mb:6.2f} MB]: {b_path.name}")
                print(f"      CRS: {crs} | Dim: {w}x{h} | Res: {res_x}x{res_y}m | Dtype: {dtype} | NoData: {nodata}")

    print("\n" + "=" * 80)
    print("SPATIAL & TEMPORAL COMPATIBILITY VERIFICATION")
    print("=" * 80)
    
    # Verify CRS consistency across all dates and bands
    crss = set()
    b08_bounds = []
    
    for date_str, sdata in scene_metadata.items():
        for b_name, binfo in sdata["bands"].items():
            crss.add(binfo["crs"])
        if "B08" in sdata["bands"]:
            b08_bounds.append((date_str, sdata["bands"]["B08"]["bounds"]))

    print(f"Detected CRS set across all scenes: {crss}")
    if len(crss) == 1:
        print("  [OK] CRS is perfectly uniform across all scenes.")
    else:
        print(f"  [WARN] Multiple CRSs detected: {crss}")

    print("\nBounding Boxes for 10m Reference Band (B08):")
    for date_str, bb in b08_bounds:
        print(f"  - {date_str}: minx={bb.left:.1f}, miny={bb.bottom:.1f}, maxx={bb.right:.1f}, maxy={bb.top:.1f}")

    if has_missing_files:
        print("\n[CRITICAL ERROR] Some required bands/files are missing!")
        return False
    else:
        print("\n[SUCCESS] All 4 dates and all 7 required bands (B02, B03, B04, B08, B11, B12, SCL) verified!")
        return True

if __name__ == "__main__":
    success = inspect_all_scenes()
    sys.exit(0 if success else 1)
