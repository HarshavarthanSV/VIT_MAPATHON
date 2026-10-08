"""
End-to-End GIS Preprocessing Pipeline Runner.
Member 2 - Agricultural Land Parcel and Crop Identification (Tirunelveli District).

Workflow:
1. Inspect input raster metadata (CRS, resolution, dimensions, bands).
2. Cloud Masking (using SCL).
3. AOI Clipping (using study_area.geojson).
4. Resampling 20m bands (B11, B12) to match 10m grid (EPSG:32643).
5. Spectral Indices Calculation (NDVI, EVI, SAVI, NDWI, MNDWI).
6. Multi-band Feature Stacking (bands + indices + metadata JSON).
7. Training Dataset Extraction (tabular CSV & polygon masks for Member 1 ML).
8. Validation & QGIS compatibility report.
"""

from pathlib import Path
from typing import Optional, Dict, List
import sys
import argparse
import rasterio
import numpy as np
import geopandas as gpd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.clipping.clip_raster import clip_raster_to_aoi, load_aoi_geometry
from preprocessing.resampling.resample import resample_to_reference
from preprocessing.indices.spectral_indices import (
    compute_ndvi,
    compute_evi,
    compute_savi,
    compute_ndwi,
    compute_mndwi,
    save_index_geotiff,
)
from preprocessing.cloud_mask.cloud_mask import create_cloud_mask_from_scl, apply_cloud_mask_to_band
from preprocessing.feature_stack.stack_features import stack_bands_and_indices, extract_tabular_training_features
from postprocessing.vectorize_and_validate import vectorize_classified_raster


def run_pipeline(
    data_dir: Path = PROJECT_ROOT / "data" / "sample",
    output_base_dir: Path = PROJECT_ROOT / "data" / "processed",
    aoi_file: Optional[Path] = None,
    training_parcels_file: Optional[Path] = None,
    acquisition_date: str = "2024-01-15",
):
    print("\n" + "=" * 70)
    print("STARTING MEMBER 2 GIS PREPROCESSING PIPELINE")
    print("Study Area: Tirunelveli (Ambasamudram & Cheranmahadevi Taluks)")
    print(f"Acquisition Date: {acquisition_date}")
    print(f"Target CRS: EPSG:32643 (UTM Zone 43N)")
    print("=" * 70)

    # 1. Locate Bands
    band_files = {}
    for b in ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]:
        # Match either sample_B02.tif or B02.tif or B02_10m.tif
        matches = list(data_dir.glob(f"*{b}*.tif")) + list(data_dir.glob(f"*{b}*.jp2"))
        if matches:
            band_files[b] = matches[0]

    print(f"\n[STEP 1] Inspecting Input Bands in: {data_dir}")
    for b, p in band_files.items():
        with rasterio.open(p) as src:
            res_x, res_y = abs(src.transform[0]), abs(src.transform[4])
            print(f"  - Band {b:<4}: {p.name:<24} | Dim: {src.width}x{src.height} | Res: {res_x}x{res_y}m | CRS: {src.crs}")

    if not all(k in band_files for k in ["B02", "B03", "B04", "B08"]):
        print("\n[ERROR] Missing core 10m bands (B02, B03, B04, B08). Cannot proceed.")
        return False

    # 2. AOI Setup
    if aoi_file is None:
        aoi_file = data_dir / "study_area.geojson"

    if not aoi_file.exists():
        print(f"\n[WARN] AOI file not found at {aoi_file}. Skipping clipping step.")
        use_clipping = False
    else:
        print(f"\n[STEP 2] AOI boundary found: {aoi_file.name}")
        use_clipping = True

    # Directories for intermediate outputs
    dir_clipped = output_base_dir / "01_clipped"
    dir_aligned = output_base_dir / "02_resampled_10m"
    dir_indices = output_base_dir / "03_indices"
    dir_stack = output_base_dir / "04_feature_stack"
    dir_training = output_base_dir / "05_training_ready"

    for d in [dir_clipped, dir_aligned, dir_indices, dir_stack, dir_training]:
        d.mkdir(parents=True, exist_ok=True)

    # 3. Clip or prepare 10m bands
    working_bands_10m = {}
    reference_10m_path = None

    for b in ["B02", "B03", "B04", "B08"]:
        src_path = band_files[b]
        if use_clipping:
            out_clip = dir_clipped / f"{acquisition_date}_{b}_clipped.tif"
            clip_raster_to_aoi(src_path, aoi_file, out_clip)
            working_bands_10m[b] = out_clip
        else:
            working_bands_10m[b] = src_path

    reference_10m_path = working_bands_10m["B08"]

    # 4. Resample 20m bands (B11, B12, SCL) to 10m grid
    print("\n[STEP 3] Resampling 20m Bands to Match 10m Grid...")
    working_bands_20m = {}
    for b in ["B11", "B12", "SCL"]:
        if b in band_files:
            src_path = band_files[b]
            if use_clipping:
                clipped_20m = dir_clipped / f"{acquisition_date}_{b}_clipped.tif"
                clip_raster_to_aoi(src_path, aoi_file, clipped_20m)
                target_src = clipped_20m
            else:
                target_src = src_path

            out_resampled = dir_aligned / f"{acquisition_date}_{b}_10m.tif"
            resample_to_reference(target_src, reference_10m_path, out_resampled)
            working_bands_20m[b] = out_resampled
            print(f"  - Aligned {b} -> 10m grid: {out_resampled.name}")

    # 5. Read all aligned bands into memory
    print("\n[STEP 4] Reading Arrays and Applying Cloud Mask...")
    arrays = {}
    with rasterio.open(reference_10m_path) as ref:
        ref_profile = ref.profile.copy()

    for b, p in {**working_bands_10m, **working_bands_20m}.items():
        with rasterio.open(p) as src:
            arrays[b] = src.read(1).astype(np.float32)

    # Cloud Masking via SCL if available
    cloud_mask = None
    if "SCL" in arrays:
        cloud_mask = create_cloud_mask_from_scl(arrays["SCL"])
        cloud_pct = (np.count_nonzero(cloud_mask) / cloud_mask.size) * 100.0
        print(f"  - SCL Cloud/Shadow detected: {cloud_pct:.2f}% invalid pixels masked.")
    else:
        print("  - SCL band not present; processing without cloud mask.")

    # 6. Calculate Spectral Indices
    print("\n[STEP 5] Calculating Spectral Indices (NDVI, EVI, SAVI, NDWI, MNDWI)...")
    indices = {}
    indices["NDVI"] = compute_ndvi(arrays["B08"], arrays["B04"], nodata_mask=cloud_mask)
    indices["SAVI"] = compute_savi(arrays["B08"], arrays["B04"], nodata_mask=cloud_mask)
    indices["EVI"] = compute_evi(arrays["B08"], arrays["B04"], arrays["B02"], nodata_mask=cloud_mask)

    if "B11" in arrays:
        indices["NDWI"] = compute_ndwi(arrays["B08"], arrays["B11"], nodata_mask=cloud_mask)
        indices["MNDWI"] = compute_mndwi(arrays["B03"], arrays["B11"], nodata_mask=cloud_mask)

    # Save individual index GeoTIFFs
    for idx_name, idx_arr in indices.items():
        out_idx_path = dir_indices / f"{acquisition_date}_{idx_name}.tif"
        save_index_geotiff(idx_arr, out_idx_path, ref_profile, nodata_val=-9999.0)
        valid_vals = idx_arr[~np.isnan(idx_arr) & (idx_arr != -9999.0)]
        mean_val = float(np.mean(valid_vals)) if len(valid_vals) > 0 else 0.0
        print(f"  - Saved {idx_name:<5} GeoTIFF: {out_idx_path.name:<28} | Mean: {mean_val:.4f}")

    # 7. Multi-Band Feature Stacking for Member 1 ML Handoff
    print("\n[STEP 6] Building Multi-Band Feature Stack for Member 1 ML Handoff...")
    stack_dict = {
        "B02": arrays["B02"],
        "B03": arrays["B03"],
        "B04": arrays["B04"],
        "B08": arrays["B08"],
    }
    if "B11" in arrays:
        stack_dict["B11"] = arrays["B11"]
    if "B12" in arrays:
        stack_dict["B12"] = arrays["B12"]

    # Append all indices
    stack_dict.update(indices)

    out_stack_tiff = dir_stack / f"{acquisition_date}_feature_stack_10m.tif"
    stack_tiff, stack_json = stack_bands_and_indices(
        stack_dict,
        out_stack_tiff,
        ref_profile,
        acquisition_date=acquisition_date,
        nodata_val=-9999.0,
    )
    print(f"  - Created Feature Stack: {stack_tiff.name} ({len(stack_dict)} bands)")
    print(f"  - Created Metadata JSON : {stack_json.name}")

    # 8. Training Feature Extraction (if parcels available)
    if training_parcels_file is None:
        training_parcels_file = data_dir / "sample_training_parcels.geojson"

    if training_parcels_file.exists():
        print(f"\n[STEP 7] Extracting Training Pixel Feature Table from: {training_parcels_file.name}...")
        out_csv = dir_training / f"{acquisition_date}_training_features.csv"
        extract_tabular_training_features(stack_tiff, training_parcels_file, out_csv)
        print(f"  - Extracted ML Training CSV: {out_csv.name}")

    print("\n" + "=" * 70)
    print("GIS PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Outputs saved in: {output_base_dir.resolve()}")
    print("=" * 70)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GIS Preprocessing Pipeline")
    parser.add_argument("--data-dir", type=str, default="data/sample", help="Input raw/sample data directory")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--aoi", type=str, default=None, help="Path to AOI GeoJSON boundary")
    parser.add_argument("--parcels", type=str, default=None, help="Path to training parcel polygons")
    parser.add_argument("--date", type=str, default="2024-01-15", help="Acquisition date (YYYY-MM-DD)")

    args = parser.parse_args()
    run_pipeline(
        data_dir=Path(args.data_dir),
        output_base_dir=Path(args.output_dir),
        aoi_file=Path(args.aoi) if args.aoi else None,
        training_parcels_file=Path(args.parcels) if args.parcels else None,
        acquisition_date=args.date,
    )
