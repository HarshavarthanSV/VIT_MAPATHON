"""
Feature Loader Module
Discovers, validates, and reads single-scene and multi-temporal Sentinel-2 GeoTIFFs.
Calculates dynamic multi-temporal features and manages raster band stacks.
"""

import os
import glob
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping, Polygon, MultiPolygon

from .validation import (
    validate_raster_metadata,
    validate_raster_alignment,
    DataNotAvailableError,
    GeospatialValidationError,
)

logger = logging.getLogger(__name__)


class FeatureLoader:
    """
    Manages loading of Sentinel-2 spectral bands and calculated indices from Member 2 outputs.
    Supports single-date baseline and multi-temporal stacks.
    """

    def __init__(
        self,
        features_dir: str,
        temporal_dir: Optional[str] = None,
        expected_crs: str = "EPSG:32643",
        core_bands: Optional[List[str]] = None,
        spectral_indices: Optional[List[str]] = None,
    ):
        self.features_dir = features_dir
        self.temporal_dir = temporal_dir
        self.expected_crs = expected_crs
        self.core_bands = core_bands or ["B02", "B03", "B04", "B08", "B11", "B12"]
        self.spectral_indices = spectral_indices or ["NDVI", "EVI", "SAVI", "NDWI"]
        
        self.available_features: Dict[str, str] = {}
        self.temporal_dates: Dict[str, Dict[str, str]] = {}
        self.reference_raster_path: Optional[str] = None
        self.raster_profile: Optional[Dict[str, Any]] = None

    def discover_features(self) -> Dict[str, str]:
        """
        Scans features_dir and discovers all available GeoTIFF files.
        Maps canonical feature names (e.g., 'NDVI', 'B04') to their file paths.
        
        Returns:
            Dict mapping feature name to file path.
            
        Raises:
            DataNotAvailableError: If features_dir does not exist or has no valid GeoTIFFs.
        """
        if not os.path.exists(self.features_dir):
            raise DataNotAvailableError(
                f"Member 2 features directory does not exist: {self.features_dir}. "
                "Halting at data input boundary."
            )

        tif_files = glob.glob(os.path.join(self.features_dir, "*.tif")) + \
                    glob.glob(os.path.join(self.features_dir, "*.tiff"))

        if not tif_files:
            raise DataNotAvailableError(
                f"No GeoTIFF files found in {self.features_dir}. Member 2 raster features are not yet generated."
            )

        discovered = {}
        for fpath in tif_files:
            fname = os.path.splitext(os.path.basename(fpath))[0]
            # Normalize name: check for matching core band or index
            canonical_name = fname
            for band in self.core_bands + self.spectral_indices:
                if band.lower() in fname.lower():
                    canonical_name = band
                    break
            discovered[canonical_name] = fpath

        self.available_features = discovered
        logger.info(f"Discovered {len(discovered)} feature rasters: {list(discovered.keys())}")
        
        # Validate raster alignment across all discovered rasters
        validate_raster_alignment(list(discovered.values()))
        
        # Save reference profile
        self.reference_raster_path = list(discovered.values())[0]
        with rasterio.open(self.reference_raster_path) as ref_src:
            self.raster_profile = ref_src.profile.copy()
            
        return self.available_features

    def discover_temporal_stacks(self) -> Dict[str, Dict[str, str]]:
        """
        Scans temporal_dir for multi-date acquisitions.
        Discovers subdirectories (e.g. date_01, date_02, or ISO dates) and their contained GeoTIFFs.
        
        Returns:
            Dict mapping date identifier -> dict of feature name -> file path.
        """
        if not self.temporal_dir or not os.path.exists(self.temporal_dir):
            logger.info("No temporal directory configured or directory does not exist. Using baseline single-date features.")
            return {}

        subdirs = [
            d for d in os.listdir(self.temporal_dir)
            if os.path.isdir(os.path.join(self.temporal_dir, d))
        ]

        if not subdirs:
            logger.info(f"No temporal date subdirectories found in {self.temporal_dir}.")
            return {}

        subdirs.sort()
        temporal_stacks = {}
        for sdir in subdirs:
            date_path = os.path.join(self.temporal_dir, sdir)
            tif_files = glob.glob(os.path.join(date_path, "*.tif")) + \
                        glob.glob(os.path.join(date_path, "*.tiff"))
            
            if not tif_files:
                continue

            date_features = {}
            for fpath in tif_files:
                fname = os.path.splitext(os.path.basename(fpath))[0]
                canonical_name = fname
                for band in self.core_bands + self.spectral_indices:
                    if band.lower() in fname.lower():
                        canonical_name = band
                        break
                date_features[canonical_name] = fpath
                
            if date_features:
                temporal_stacks[sdir] = date_features

        self.temporal_dates = temporal_stacks
        logger.info(f"Discovered {len(temporal_stacks)} multi-temporal dates: {list(temporal_stacks.keys())}")
        return self.temporal_dates

    def extract_polygon_features(
        self,
        geometry: Any,
        features_to_read: Optional[List[str]] = None,
        aggregation: str = "mean"
    ) -> Dict[str, float]:
        """
        Extracts zonal feature summary (mean, median, std) for a given vector polygon across all raster bands.
        
        Args:
            geometry: Shapely geometry (Polygon or MultiPolygon) or GeoJSON mapping.
            features_to_read: Subset of feature names to extract (defaults to all available).
            aggregation: Aggregation statistic ("mean", "median", "std").
            
        Returns:
            Dictionary of {feature_name: value}.
        """
        if not self.available_features:
            self.discover_features()

        if hasattr(geometry, "__geo_interface__"):
            geom_json = [mapping(geometry)]
        elif isinstance(geometry, dict):
            geom_json = [geometry]
        else:
            geom_json = [mapping(geometry)]

        selected_features = features_to_read or list(self.available_features.keys())
        results = {}

        # 1. Baseline feature extraction
        for feat_name in selected_features:
            fpath = self.available_features.get(feat_name)
            if not fpath or not os.path.exists(fpath):
                continue
                
            with rasterio.open(fpath) as src:
                try:
                    masked_arr, _ = mask(src, geom_json, crop=True, filled=False)
                    valid_data = masked_arr[0].compressed()
                    
                    if len(valid_data) == 0:
                        results[feat_name] = np.nan
                    elif aggregation == "median":
                        results[feat_name] = float(np.ma.median(valid_data))
                    elif aggregation == "std":
                        results[feat_name] = float(np.ma.std(valid_data))
                    else:  # default mean
                        results[feat_name] = float(np.ma.mean(valid_data))
                except Exception as e:
                    logger.debug(f"Masking failed for feature {feat_name}: {e}")
                    results[feat_name] = np.nan

        # 2. Multi-temporal feature extraction (if temporal dates are present)
        if self.temporal_dates:
            temporal_series = {feat: [] for feat in ["NDVI", "EVI", "SAVI", "NDWI"]}
            for date_key, date_dict in self.temporal_dates.items():
                for feat in temporal_series.keys():
                    if feat in date_dict:
                        with rasterio.open(date_dict[feat]) as src:
                            try:
                                masked_arr, _ = mask(src, geom_json, crop=True, filled=False)
                                valid_data = masked_arr[0].compressed()
                                if len(valid_data) > 0:
                                    val = float(np.ma.mean(valid_data))
                                    temporal_series[feat].append(val)
                                    # Also record date-specific feature
                                    results[f"{feat}_{date_key}"] = val
                            except Exception:
                                pass

            # Compute temporal statistics across dates (mean, std, min, max, range)
            for feat, vals in temporal_series.items():
                if len(vals) > 1:
                    arr = np.array(vals)
                    results[f"{feat}_temporal_mean"] = float(np.mean(arr))
                    results[f"{feat}_temporal_std"] = float(np.std(arr))
                    results[f"{feat}_temporal_min"] = float(np.min(arr))
                    results[f"{feat}_temporal_max"] = float(np.max(arr))
                    results[f"{feat}_temporal_range"] = float(np.max(arr) - np.min(arr))

        return results
