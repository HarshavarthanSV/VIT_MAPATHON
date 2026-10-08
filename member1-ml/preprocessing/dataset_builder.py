"""
Dataset Builder Module
Constructs ML datasets from real Sentinel-2 raster layers and ground-truth polygons.
Enforces spatial-aware splitting using GroupShuffleSplit to prevent spatial autocorrelation leakage.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.model_selection import GroupShuffleSplit, StratifiedShuffleSplit
from sklearn.impute import SimpleImputer

from .feature_loader import FeatureLoader
from .label_loader import LabelLoader

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """
    Builds structured training, validation, and testing feature matrices from geospatial data.
    """

    def __init__(
        self,
        feature_loader: FeatureLoader,
        label_loader: LabelLoader,
        sampling_strategy: str = "parcel_mean",
        handle_nan: str = "median_impute",
        test_size: float = 0.20,
        val_size: float = 0.10,
        random_state: int = 42,
    ):
        self.feature_loader = feature_loader
        self.label_loader = label_loader
        self.sampling_strategy = sampling_strategy
        self.handle_nan = handle_nan
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state

        self.df: Optional[pd.DataFrame] = None
        self.feature_names: List[str] = []
        self.imputer: Optional[SimpleImputer] = None

    def build_dataset(self) -> pd.DataFrame:
        """
        Iterates over validated training polygons, extracts spectral and temporal features,
        and constructs a master tabular DataFrame.
        
        Returns:
            pd.DataFrame containing parcel_id, crop_type, and extracted feature columns.
        """
        # Discover raster features
        self.feature_loader.discover_features()
        self.feature_loader.discover_temporal_stacks()

        # Load labels
        labels_gdf = self.label_loader.load_and_normalize()

        records = []
        id_col = self.label_loader.id_col
        label_col = self.label_loader.label_col

        logger.info(f"Extracting features for {len(labels_gdf)} polygons using strategy '{self.sampling_strategy}'...")

        for idx, row in labels_gdf.iterrows():
            geom = row.geometry
            parcel_id = row[id_col]
            crop_label = row[label_col]

            # Extract features across all available bands & indices
            feat_dict = self.feature_loader.extract_polygon_features(
                geometry=geom,
                aggregation="mean" if self.sampling_strategy == "parcel_mean" else "median"
            )

            # Record
            record = {
                "parcel_id": str(parcel_id),
                "crop_type": str(crop_label),
                "area_sq_km": float(row.get("area_sq_km", 0.0)),
            }
            record.update(feat_dict)
            records.append(record)

        df = pd.DataFrame(records)

        # Identify feature columns (all columns except metadata and target)
        exclude_cols = {"parcel_id", "crop_type", "area_sq_km"}
        self.feature_names = [c for c in df.columns if c not in exclude_cols]

        logger.info(f"Constructed raw dataset with {len(df)} samples and {len(self.feature_names)} features: {self.feature_names}")

        # Drop rows where all feature values are NaN
        all_nan_mask = df[self.feature_names].isna().all(axis=1)
        if all_nan_mask.any():
            dropped_count = all_nan_mask.sum()
            logger.warning(f"Dropping {dropped_count} parcels with zero valid raster pixels.")
            df = df[~all_nan_mask].reset_index(drop=True)

        self.df = df
        return self.df

    def create_spatial_splits(
        self,
        df: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """
        Splits dataset into train, validation, and test subsets.
        Uses GroupShuffleSplit grouped by parcel_id to eliminate spatial leakage.
        
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test).
        """
        if df is None:
            if self.df is None:
                df = self.build_dataset()
            else:
                df = self.df

        if len(df) == 0:
            raise ValueError("Dataset is empty. Cannot perform train/val/test splitting.")

        X = df[self.feature_names].copy()
        y = df["crop_type"].copy()
        groups = df["parcel_id"].values

        n_unique_groups = len(np.unique(groups))
        logger.info(f"Splitting dataset of {len(df)} samples across {n_unique_groups} unique parcel groups.")

        # If each row is a unique parcel or if multiple samples belong to parcel groups
        if n_unique_groups >= 5:
            # First split: Train+Val vs Test
            gss_test = GroupShuffleSplit(
                n_splits=1,
                test_size=self.test_size,
                random_state=self.random_state
            )
            train_val_idx, test_idx = next(gss_test.split(X, y, groups=groups))

            X_train_val = X.iloc[train_val_idx].copy()
            y_train_val = y.iloc[train_val_idx].copy()
            groups_train_val = groups[train_val_idx]

            X_test = X.iloc[test_idx].copy()
            y_test = y.iloc[test_idx].copy()

            # Second split: Train vs Val (from train_val)
            val_relative_size = self.val_size / (1.0 - self.test_size)
            if len(np.unique(groups_train_val)) >= 4 and val_relative_size > 0:
                gss_val = GroupShuffleSplit(
                    n_splits=1,
                    test_size=val_relative_size,
                    random_state=self.random_state
                )
                train_idx, val_idx = next(gss_val.split(X_train_val, y_train_val, groups=groups_train_val))
                X_train = X_train_val.iloc[train_idx].copy()
                y_train = y_train_val.iloc[train_idx].copy()
                X_val = X_train_val.iloc[val_idx].copy()
                y_val = y_train_val.iloc[val_idx].copy()
            else:
                # If train_val groups too small for further split, validation is empty or subset
                X_train = X_train_val
                y_train = y_train_val
                X_val = pd.DataFrame(columns=self.feature_names)
                y_val = pd.Series(dtype=object)
        else:
            # Fallback: Stratified split if very few groups
            logger.warning("Fewer than 5 distinct parcel groups detected. Falling back to StratifiedShuffleSplit.")
            sss = StratifiedShuffleSplit(n_splits=1, test_size=self.test_size, random_state=self.random_state)
            train_val_idx, test_idx = next(sss.split(X, y))
            X_train = X.iloc[train_val_idx].copy()
            y_train = y.iloc[train_val_idx].copy()
            X_val = pd.DataFrame(columns=self.feature_names)
            y_val = pd.Series(dtype=object)
            X_test = X.iloc[test_idx].copy()
            y_test = y.iloc[test_idx].copy()

        # Handle NaNs via Imputation (fit on train, transform on val & test)
        if self.handle_nan == "median_impute" and len(X_train) > 0:
            self.imputer = SimpleImputer(strategy="median")
            X_train_imputed = self.imputer.fit_transform(X_train)
            X_train = pd.DataFrame(X_train_imputed, columns=self.feature_names, index=X_train.index)

            if len(X_val) > 0:
                X_val_imputed = self.imputer.transform(X_val)
                X_val = pd.DataFrame(X_val_imputed, columns=self.feature_names, index=X_val.index)

            if len(X_test) > 0:
                X_test_imputed = self.imputer.transform(X_test)
                X_test = pd.DataFrame(X_test_imputed, columns=self.feature_names, index=X_test.index)

        logger.info(
            f"Dataset split complete: Train={len(X_train)} samples, "
            f"Val={len(X_val)} samples, Test={len(X_test)} samples."
        )

        return X_train, X_val, X_test, y_train, y_val, y_test
