"""
Parcel Classifier Module
Performs parcel-level crop inference across study area vector geometries.
Generates classified_parcels.geojson and dynamically aggregates crop_statistics.json.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.crs import CRS
from sklearn.ensemble import RandomForestClassifier

try:
    from ..preprocessing.feature_loader import FeatureLoader
    from ..preprocessing.validation import (
        validate_study_area,
        DataNotAvailableError,
        GeospatialValidationError,
    )
except (ImportError, ValueError):
    from preprocessing.feature_loader import FeatureLoader
    from preprocessing.validation import (
        validate_study_area,
        DataNotAvailableError,
        GeospatialValidationError,
    )

logger = logging.getLogger(__name__)


class ParcelClassifier:
    """
    Executes crop classification over full agricultural parcel boundaries and computes summary statistics.
    """

    def __init__(
        self,
        model: RandomForestClassifier,
        feature_loader: FeatureLoader,
        feature_names: List[str],
        target_crs: str = "EPSG:32643",
    ):
        self.model = model
        self.feature_loader = feature_loader
        self.feature_names = feature_names
        self.target_crs = target_crs

    def classify_parcels(
        self,
        parcels_path: str,
        id_col: str = "parcel_id"
    ) -> gpd.GeoDataFrame:
        """
        Reads agricultural parcels, extracts raster features per parcel polygon,
        runs model inference, and attaches predictions and confidence scores.
        
        Args:
            parcels_path: Path to parcel boundaries vector file.
            id_col: Column name identifying unique parcel IDs.
            
        Returns:
            GeoDataFrame of classified parcels with predictions and metrics.
        """
        if not os.path.exists(parcels_path):
            raise DataNotAvailableError(
                f"Parcel boundaries file not found: {parcels_path}. "
                "Halting at data input boundary."
            )

        try:
            gdf = gpd.read_file(parcels_path)
        except Exception as e:
            raise GeospatialValidationError(f"Could not read parcels from {parcels_path}: {e}")

        if len(gdf) == 0:
            raise GeospatialValidationError(f"Parcels file {parcels_path} contains 0 geometries.")

        # Ensure ID column exists
        if id_col not in gdf.columns:
            alternatives = ["id", "ID", "fid", "FID", "poly_id", "parcel_no"]
            found = None
            for alt in alternatives:
                if alt in gdf.columns:
                    found = alt
                    break
            if found:
                gdf[id_col] = gdf[found]
            else:
                gdf[id_col] = [f"parcel_{i+1:05d}" for i in range(len(gdf))]

        # Ensure metric CRS for accurate spatial area calculations
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
            
        target_crs_obj = CRS.from_string(self.target_crs)
        if gdf.crs != target_crs_obj:
            gdf_projected = gdf.to_crs(self.target_crs)
        else:
            gdf_projected = gdf.copy()

        # Compute accurate metric area
        gdf_projected["area_sq_m"] = gdf_projected.geometry.area
        gdf_projected["area_ha"] = gdf_projected["area_sq_m"] / 10000.0
        gdf_projected["area_sq_km"] = gdf_projected["area_sq_m"] / 1000000.0

        # Validate study area coverage
        total_sq_km, meets_req = validate_study_area(gdf_projected, min_area_sq_km=20.0, target_crs=self.target_crs)
        logger.info(f"Classifying study area totaling {total_sq_km:.2f} sq. km across {len(gdf_projected)} parcels.")

        # Extract features per parcel
        logger.info("Extracting raster features for each parcel polygon...")
        feature_rows = []
        for idx, row in gdf_projected.iterrows():
            geom = row.geometry
            feat_dict = self.feature_loader.extract_polygon_features(geom, aggregation="mean")
            
            # Form feature vector strictly matching model expected features
            feat_vector = [feat_dict.get(fname, np.nan) for fname in self.feature_names]
            feature_rows.append(feat_vector)

        X_parcels = np.array(feature_rows)
        # Impute missing values with 0.0 or column means
        col_means = np.nanmean(X_parcels, axis=0)
        # If any column is entirely NaN, replace with 0
        col_means = np.nan_to_num(col_means, nan=0.0)
        inds = np.where(np.isnan(X_parcels))
        X_parcels[inds] = np.take(col_means, inds[1])

        # Convert to DataFrame with feature names matching model training
        df_parcels = pd.DataFrame(X_parcels, columns=self.feature_names)

        # Run model inference
        predictions = self.model.predict(df_parcels)
        probabilities = self.model.predict_proba(df_parcels)
        max_confidence = np.max(probabilities, axis=1)

        # Attach results to GeoDataFrame
        gdf_projected["predicted_crop"] = predictions
        gdf_projected["confidence"] = np.round(max_confidence, 4)

        # Attach probabilities for each target class
        for i, cls_name in enumerate(self.model.classes_):
            gdf_projected[f"prob_{cls_name.lower()}"] = np.round(probabilities[:, i], 4)

        return gdf_projected

    def export_classified_geojson(
        self,
        classified_gdf: gpd.GeoDataFrame,
        output_path: str
    ) -> str:
        """
        Exports classified parcels as standard WGS84 GeoJSON for PostGIS / Leaflet consumption.
        
        Args:
            classified_gdf: Projected GeoDataFrame with classification results.
            output_path: Destination file path.
            
        Returns:
            Path to exported GeoJSON file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Reproject to standard WGS84 (EPSG:4326) for Web GIS GeoJSON standard
        geojson_gdf = classified_gdf.to_crs("EPSG:4326")

        # Select clean properties for web API / PostGIS consumption
        property_cols = [
            "parcel_id", "predicted_crop", "confidence",
            "area_sq_km", "area_ha", "geometry"
        ]
        # Include probability columns if present
        for col in classified_gdf.columns:
            if col.startswith("prob_") and col not in property_cols:
                property_cols.append(col)

        export_gdf = geojson_gdf[[c for c in property_cols if c in geojson_gdf.columns]]
        export_gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Exported classified parcels GeoJSON to: {output_path}")
        return output_path

    def compute_crop_statistics(
        self,
        classified_gdf: gpd.GeoDataFrame,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically calculates crop area statistics, parcel counts, and percentages.
        Zero hardcoding: all metrics are computed from real classified polygons.
        
        Args:
            classified_gdf: Classified GeoDataFrame.
            output_path: Optional path to save crop_statistics.json.
            
        Returns:
            Summary statistics dictionary.
        """
        total_parcels = len(classified_gdf)
        total_area_sq_km = float(classified_gdf["area_sq_km"].sum())
        total_area_ha = float(classified_gdf["area_ha"].sum())
        mean_conf = float(classified_gdf["confidence"].mean())

        crops = ["Paddy", "Banana", "Other"]
        # Include any other classes present in model
        for c in classified_gdf["predicted_crop"].unique():
            if c not in crops:
                crops.append(c)

        crop_breakdown = {}
        for crop in crops:
            subset = classified_gdf[classified_gdf["predicted_crop"] == crop]
            p_count = int(len(subset))
            crop_sq_km = float(subset["area_sq_km"].sum()) if p_count > 0 else 0.0
            crop_ha = float(subset["area_ha"].sum()) if p_count > 0 else 0.0
            pct_area = float((crop_sq_km / total_area_sq_km * 100.0)) if total_area_sq_km > 0 else 0.0
            pct_count = float((p_count / total_parcels * 100.0)) if total_parcels > 0 else 0.0
            avg_conf = float(subset["confidence"].mean()) if p_count > 0 else 0.0

            crop_breakdown[crop] = {
                "parcel_count": p_count,
                "percentage_of_parcels": round(pct_count, 2),
                "area_sq_km": round(crop_sq_km, 4),
                "area_hectares": round(crop_ha, 2),
                "percentage_of_total_area": round(pct_area, 2),
                "mean_confidence": round(avg_conf, 4)
            }

        statistics = {
            "study_area_summary": {
                "total_parcels": total_parcels,
                "total_study_area_sq_km": round(total_area_sq_km, 4),
                "total_study_area_hectares": round(total_area_ha, 2),
                "overall_mean_confidence": round(mean_conf, 4),
                "meets_min_area_requirement": total_area_sq_km >= 20.0
            },
            "crop_distribution": crop_breakdown
        }

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(statistics, f, indent=2)
            logger.info(f"Saved crop statistics to: {output_path}")

        return statistics
