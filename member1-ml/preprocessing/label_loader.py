"""
Label Loader Module
Loads, cleans, validates, and normalizes ground-truth crop training polygons.
Handles class mapping to canonical targets: Paddy, Banana, Other.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import geopandas as gpd
from rasterio.crs import CRS

from .validation import (
    validate_labels_file,
    DataNotAvailableError,
    GeospatialValidationError,
)

logger = logging.getLogger(__name__)


class LabelLoader:
    """
    Manages ingestion and normalization of agricultural training polygons.
    """

    DEFAULT_NORMALIZATION = {
        "paddy": "Paddy",
        "rice": "Paddy",
        "PADDY": "Paddy",
        "RICE": "Paddy",
        "banana": "Banana",
        "plantain": "Banana",
        "BANANA": "Banana",
        "PLANTAIN": "Banana",
        "other": "Other",
        "OTHER": "Other",
        "fallow": "Other",
        "scrub": "Other",
        "builtup": "Other",
        "water": "Other",
        "barren": "Other",
    }

    def __init__(
        self,
        labels_path: str,
        target_classes: Optional[List[str]] = None,
        label_col: str = "crop_type",
        id_col: str = "parcel_id",
        target_crs: str = "EPSG:32643",
        normalization_map: Optional[Dict[str, str]] = None,
    ):
        self.labels_path = labels_path
        self.target_classes = target_classes or ["Paddy", "Banana", "Other"]
        self.label_col = label_col
        self.id_col = id_col
        self.target_crs = target_crs
        self.normalization_map = normalization_map or self.DEFAULT_NORMALIZATION
        self.gdf: Optional[gpd.GeoDataFrame] = None

    def load_and_normalize(self) -> gpd.GeoDataFrame:
        """
        Loads the training labels file, applies geometry checks, reprojects to target_crs,
        normalizes crop class strings, and verifies target class representation.
        
        Returns:
            Cleaned and normalized GeoDataFrame.
            
        Raises:
            DataNotAvailableError: If labels_path does not exist.
            GeospatialValidationError: If geometries or classes are invalid.
        """
        if not os.path.exists(self.labels_path):
            raise DataNotAvailableError(
                f"Training labels file not found: {self.labels_path}. "
                "Halting at data input boundary."
            )

        # Base validation & reprojection
        raw_gdf = validate_labels_file(
            labels_path=self.labels_path,
            label_col=self.label_col,
            id_col=self.id_col,
            target_crs=self.target_crs
        )

        gdf = raw_gdf.copy()

        # Class normalization
        def normalize_class(val: Any) -> str:
            if not isinstance(val, str):
                val = str(val)
            cleaned = val.strip()
            
            # Check direct match in target classes
            for target in self.target_classes:
                if cleaned.lower() == target.lower():
                    return target
                    
            # Check map
            if cleaned in self.normalization_map:
                return self.normalization_map[cleaned]
            if cleaned.lower() in self.normalization_map:
                return self.normalization_map[cleaned.lower()]
                
            # Fallback to Other
            logger.info(f"Unrecognized class '{cleaned}' mapped to 'Other'.")
            return "Other"

        gdf[self.label_col] = gdf[self.label_col].apply(normalize_class)

        # Compute area in metric CRS (square meters -> hectares & sq km)
        gdf["area_sq_m"] = gdf.geometry.area
        gdf["area_ha"] = gdf["area_sq_m"] / 10000.0
        gdf["area_sq_km"] = gdf["area_sq_m"] / 1000000.0

        # Class counts
        class_counts = gdf[self.label_col].value_counts().to_dict()
        logger.info(f"Loaded {len(gdf)} training parcels. Class distribution: {class_counts}")

        # Check for required classes
        missing_classes = [c for c in self.target_classes if c not in class_counts or class_counts[c] == 0]
        if missing_classes:
            logger.warning(
                f"Warning: The following target classes have 0 training samples: {missing_classes}. "
                "Random Forest model will only be trained on available classes."
            )

        self.gdf = gdf
        return self.gdf
