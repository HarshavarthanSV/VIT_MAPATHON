"""
Geospatial Data Validation Module
Ensures strict spatial, geometric, and radiometric integrity of satellite features and vector labels.
"""

import os
import logging
from typing import Dict, List, Any, Tuple
import rasterio
from rasterio.crs import CRS
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon

logger = logging.getLogger(__name__)


class DataNotAvailableError(Exception):
    """Raised when upstream Member 2 data has not yet been generated or placed in expected paths."""
    pass


class GeospatialValidationError(ValueError):
    """Raised when raster or vector data fails spatial, geometric, or alignment checks."""
    pass


def validate_raster_metadata(raster_path: str, expected_crs: str = "EPSG:32643") -> Dict[str, Any]:
    """
    Validates a single GeoTIFF file's dimensions, CRS, affine transform, nodata, and numeric sanity.
    
    Args:
        raster_path: Path to the GeoTIFF raster.
        expected_crs: Required CRS string (default EPSG:32643 / UTM Zone 43N).
        
    Returns:
        Dictionary of validated raster metadata.
    """
    if not os.path.exists(raster_path):
        raise DataNotAvailableError(f"Raster file not found: {raster_path}")
        
    try:
        with rasterio.open(raster_path) as src:
            actual_crs = src.crs.to_string() if src.crs else None
            
            # CRS validation
            crs_match = False
            if actual_crs:
                target = CRS.from_string(expected_crs)
                current = CRS.from_string(actual_crs)
                crs_match = (current == target)
            
            if not crs_match:
                logger.warning(
                    f"CRS mismatch in {raster_path}: Expected {expected_crs}, but detected {actual_crs}. "
                    "Reprojection or CRS alignment may be required."
                )

            # Dimensions & Transform
            meta = {
                "path": raster_path,
                "width": src.width,
                "height": src.height,
                "count": src.count,
                "crs": actual_crs,
                "crs_valid": crs_match,
                "transform": src.transform,
                "bounds": src.bounds,
                "res": src.res,
                "nodata": src.nodata,
                "dtype": str(src.dtypes[0])
            }
            
            if src.width <= 0 or src.height <= 0:
                raise GeospatialValidationError(f"Invalid raster dimensions in {raster_path}: {src.width}x{src.height}")

            # Read sample/band to verify finite values
            sample_band = src.read(1, masked=True)
            valid_pixels = sample_band.compressed()
            if len(valid_pixels) == 0:
                raise GeospatialValidationError(f"Raster contains zero valid (non-masked) pixels: {raster_path}")
            
            nan_count = int(np.isnan(valid_pixels).sum())
            inf_count = int(np.isinf(valid_pixels).sum())
            if nan_count > 0 or inf_count > 0:
                logger.warning(f"Raster {raster_path} contains {nan_count} NaNs and {inf_count} Infs in valid mask.")
                
            meta["valid_pixel_count"] = len(valid_pixels)
            meta["min_val"] = float(np.min(valid_pixels))
            meta["max_val"] = float(np.max(valid_pixels))
            meta["mean_val"] = float(np.mean(valid_pixels))
            
            return meta
    except Exception as e:
        if isinstance(e, (DataNotAvailableError, GeospatialValidationError)):
            raise
        raise GeospatialValidationError(f"Failed to inspect raster {raster_path}: {str(e)}") from e


def validate_raster_alignment(raster_paths: List[str]) -> bool:
    """
    Validates that a collection of rasters share identical dimensions, CRS, affine transform, and grid bounds.
    
    Args:
        raster_paths: List of file paths to GeoTIFF rasters.
        
    Returns:
        True if all rasters are strictly aligned.
        
    Raises:
        GeospatialValidationError if any alignment discrepancy is detected.
    """
    if not raster_paths:
        raise DataNotAvailableError("No raster paths provided for alignment validation.")
        
    reference_meta = None
    ref_path = None
    
    for path in raster_paths:
        meta = validate_raster_metadata(path)
        if reference_meta is None:
            reference_meta = meta
            ref_path = path
            continue
            
        # Check dimensions
        if (meta["width"], meta["height"]) != (reference_meta["width"], reference_meta["height"]):
            raise GeospatialValidationError(
                f"Dimension mismatch between {ref_path} ({reference_meta['width']}x{reference_meta['height']}) "
                f"and {path} ({meta['width']}x{meta['height']})"
            )
            
        # Check CRS
        if meta["crs"] != reference_meta["crs"]:
            raise GeospatialValidationError(
                f"CRS mismatch between {ref_path} ({reference_meta['crs']}) and {path} ({meta['crs']})"
            )
            
        # Check Transform
        for i in range(6):
            if abs(meta["transform"][i] - reference_meta["transform"][i]) > 1e-4:
                raise GeospatialValidationError(
                    f"Affine transform mismatch between {ref_path} and {path}: "
                    f"{reference_meta['transform']} vs {meta['transform']}"
                )
                
    logger.info(f"Verified alignment across {len(raster_paths)} raster layers.")
    return True


def validate_labels_file(
    labels_path: str,
    label_col: str = "crop_type",
    id_col: str = "parcel_id",
    target_crs: str = "EPSG:32643"
) -> gpd.GeoDataFrame:
    """
    Validates vector polygons for crop ground truth labels.
    Checks geometry validity, CRS alignment, and required columns.
    
    Args:
        labels_path: Path to GeoJSON / GeoPackage vector file.
        label_col: Name of the class label column.
        id_col: Name of the parcel/polygon ID column.
        target_crs: Required metric CRS for analysis.
        
    Returns:
        Validated and aligned GeoDataFrame.
    """
    if not os.path.exists(labels_path):
        raise DataNotAvailableError(f"Labels file not found: {labels_path}")
        
    try:
        gdf = gpd.read_file(labels_path)
    except Exception as e:
        raise GeospatialValidationError(f"Could not read vector labels from {labels_path}: {e}") from e
        
    if len(gdf) == 0:
        raise GeospatialValidationError(f"Labels file {labels_path} contains 0 geometries.")
        
    # Check geometry types
    valid_geom_types = ("Polygon", "MultiPolygon")
    invalid_types = [t for t in gdf.geometry.geom_type.unique() if t not in valid_geom_types]
    if invalid_types:
        raise GeospatialValidationError(
            f"Unsupported geometry types found in {labels_path}: {invalid_types}. Must be Polygon or MultiPolygon."
        )
        
    # Fix or validate invalid geometries
    invalid_mask = ~gdf.geometry.is_valid
    if invalid_mask.any():
        logger.warning(f"Detected {invalid_mask.sum()} invalid geometries. Applying buffer(0) fix.")
        gdf["geometry"] = gdf.geometry.buffer(0)
        still_invalid = ~gdf.geometry.is_valid
        if still_invalid.any():
            raise GeospatialValidationError(f"Could not repair {still_invalid.sum()} invalid geometries in {labels_path}.")

    # Column checks
    # Support fallback names if column differs
    if label_col not in gdf.columns:
        alternatives = ["crop", "class", "label", "crop_name", "target", "CROP_TYPE"]
        found = None
        for alt in alternatives:
            if alt in gdf.columns:
                found = alt
                break
        if found:
            gdf[label_col] = gdf[found]
            logger.info(f"Mapped label column '{found}' to '{label_col}'.")
        else:
            raise GeospatialValidationError(
                f"Label column '{label_col}' not found in {labels_path}. Available columns: {list(gdf.columns)}"
            )

    if id_col not in gdf.columns:
        alternatives = ["id", "ID", "fid", "FID", "poly_id", "parcel_no"]
        found = None
        for alt in alternatives:
            if alt in gdf.columns:
                found = alt
                break
        if found:
            gdf[id_col] = gdf[found]
            logger.info(f"Mapped ID column '{found}' to '{id_col}'.")
        else:
            logger.warning(f"ID column '{id_col}' not found. Generating sequential parcel IDs.")
            gdf[id_col] = [f"parcel_{i+1:05d}" for i in range(len(gdf))]

    # CRS Reprojection if needed
    if gdf.crs is None:
        logger.warning(f"Labels file {labels_path} missing CRS. Assuming WGS 84 (EPSG:4326).")
        gdf = gdf.set_crs("EPSG:4326")
        
    target_crs_obj = CRS.from_string(target_crs)
    if gdf.crs != target_crs_obj:
        logger.info(f"Reprojecting labels from {gdf.crs.to_string()} to {target_crs}.")
        gdf = gdf.to_crs(target_crs)

    return gdf


def validate_study_area(
    gdf: gpd.GeoDataFrame,
    min_area_sq_km: float = 20.0,
    target_crs: str = "EPSG:32643"
) -> Tuple[float, bool]:
    """
    Dynamically computes the total area of the study area or parcels in square kilometers.
    Validates against the minimum study area requirement (>= 20 sq. km).
    
    Args:
        gdf: GeoDataFrame containing study area boundary or parcels.
        min_area_sq_km: Required minimum area in sq. km (default 20.0).
        target_crs: Metric CRS for accurate area computation.
        
    Returns:
        Tuple of (actual_area_sq_km, meets_requirement_boolean).
    """
    if len(gdf) == 0:
        return 0.0, False
        
    # Ensure metric projection
    target_crs_obj = CRS.from_string(target_crs)
    if gdf.crs != target_crs_obj:
        projected_gdf = gdf.to_crs(target_crs)
    else:
        projected_gdf = gdf

    # Calculate union area in square meters, convert to sq. km
    try:
        # Avoid double-counting overlapping bounds with unary union
        if hasattr(projected_gdf.geometry, "union_all"):
            unified_geom = projected_gdf.geometry.union_all()
        else:
            unified_geom = projected_gdf.geometry.unary_union
        total_sq_meters = unified_geom.area
    except Exception:
        total_sq_meters = projected_gdf.geometry.area.sum()

    actual_sq_km = total_sq_meters / 1_000_000.0
    meets_req = actual_sq_km >= min_area_sq_km
    
    if not meets_req:
        logger.warning(
            f"Study area is {actual_sq_km:.2f} sq. km, which is LESS than the required {min_area_sq_km} sq. km."
        )
    else:
        logger.info(f"Study area verified: {actual_sq_km:.2f} sq. km (>= {min_area_sq_km} sq. km required).")
        
    return actual_sq_km, meets_req
