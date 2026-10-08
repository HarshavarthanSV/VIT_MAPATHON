"""
Advanced Spectral Indices and Spectral Relationship Features Module.
Phases 2, 3, 4 of the Crop Classification Upgrade Pipeline.
Computes vegetation, red-edge/chlorophyll, moisture, and cross-band ratio/difference features.
"""

from typing import Dict, Union, Optional
import numpy as np
import pandas as pd


def safe_divide(
    num: Union[np.ndarray, pd.Series, float],
    den: Union[np.ndarray, pd.Series, float],
    fill_val: float = 0.0,
    eps: float = 1e-7
) -> Union[np.ndarray, pd.Series]:
    """Safely divide avoiding division by zero or NaN propagation."""
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        den_clean = den.copy().replace(0.0, eps)
        res = num / den_clean
        return res.fillna(fill_val).replace([np.inf, -np.inf], fill_val)
    with np.errstate(divide="ignore", invalid="ignore"):
        res = np.where(np.abs(den) > eps, num / den, fill_val)
        res = np.nan_to_num(res, nan=fill_val, posinf=fill_val, neginf=fill_val)
    return res


def compute_spectral_indices(
    b02: Union[np.ndarray, pd.Series],
    b03: Union[np.ndarray, pd.Series],
    b04: Union[np.ndarray, pd.Series],
    b08: Union[np.ndarray, pd.Series],
    b05: Optional[Union[np.ndarray, pd.Series]] = None,
    b06: Optional[Union[np.ndarray, pd.Series]] = None,
    b07: Optional[Union[np.ndarray, pd.Series]] = None,
    b8a: Optional[Union[np.ndarray, pd.Series]] = None,
    b11: Optional[Union[np.ndarray, pd.Series]] = None,
    b12: Optional[Union[np.ndarray, pd.Series]] = None,
) -> Dict[str, Union[np.ndarray, pd.Series]]:
    """
    Computes all standard and advanced spectral indices for Sentinel-2 Level-2A surface reflectance.
    Expects reflectance values in continuous [0.0, 1.0] scale.
    """
    indices: Dict[str, Union[np.ndarray, pd.Series]] = {}

    # 1. VEGETATION INDICES
    # NDVI = (B08 - B04) / (B08 + B04)
    indices["NDVI"] = safe_divide(b08 - b04, b08 + b04)

    # EVI = 2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)
    evi_den = b08 + (6.0 * b04) - (7.5 * b02) + 1.0
    indices["EVI"] = 2.5 * safe_divide(b08 - b04, evi_den)

    # EVI2 = 2.5 * (B08 - B04) / (B08 + 2.4*B04 + 1)
    evi2_den = b08 + (2.4 * b04) + 1.0
    indices["EVI2"] = 2.5 * safe_divide(b08 - b04, evi2_den)

    # SAVI = 1.5 * (B08 - B04) / (B08 + B04 + 0.5)
    indices["SAVI"] = 1.5 * safe_divide(b08 - b04, b08 + b04 + 0.5)

    # MSAVI = (2*B08 + 1 - sqrt((2*B08 + 1)^2 - 8*(B08 - B04))) / 2
    term1 = 2.0 * b08 + 1.0
    term2 = term1 ** 2 - 8.0 * (b08 - b04)
    if isinstance(term2, pd.Series):
        term2_clipped = term2.clip(lower=0.0)
        indices["MSAVI"] = (term1 - np.sqrt(term2_clipped)) / 2.0
    else:
        indices["MSAVI"] = (term1 - np.sqrt(np.maximum(term2, 0.0))) / 2.0

    # OSAVI = (B08 - B04) / (B08 + B04 + 0.16)
    indices["OSAVI"] = safe_divide(b08 - b04, b08 + b04 + 0.16)

    # GNDVI = (B08 - B03) / (B08 + B03)
    indices["GNDVI"] = safe_divide(b08 - b03, b08 + b03)

    # 2. MOISTURE / WATER INDICES
    # NDWI (McFeeters) = (B03 - B08) / (B03 + B08)
    indices["NDWI"] = safe_divide(b03 - b08, b03 + b08)

    if b11 is not None:
        # NDMI (Gao) = (B08 - B11) / (B08 + B11)
        indices["NDMI"] = safe_divide(b08 - b11, b08 + b11)
        # MSI = B11 / B08
        indices["MSI"] = safe_divide(b11, b08)

    # 3. RED-EDGE & CHLOROPHYLL INDICES
    if b05 is not None:
        # NDRE_B05 = (B08 - B05) / (B08 + B05)
        indices["NDRE_B05"] = safe_divide(b08 - b05, b08 + b05)
    if b06 is not None:
        # NDRE_B06 = (B08 - B06) / (B08 + b06)
        indices["NDRE_B06"] = safe_divide(b08 - b06, b08 + b06)
    if b07 is not None:
        # NDRE_B07 = (B08 - B07) / (B08 + B07)
        indices["NDRE_B07"] = safe_divide(b08 - b07, b08 + b07)
    if b05 is not None and b06 is not None:
        # MTCI = (B06 - B05) / (B05 - B04)
        indices["MTCI"] = safe_divide(b06 - b05, b05 - b04)
    if b05 is not None and b07 is not None:
        # CI_red_edge = (B07 / B05) - 1.0
        indices["CI_red_edge"] = safe_divide(b07, b05) - 1.0

    return indices


def compute_spectral_relationships(
    b02: Union[np.ndarray, pd.Series],
    b03: Union[np.ndarray, pd.Series],
    b04: Union[np.ndarray, pd.Series],
    b08: Union[np.ndarray, pd.Series],
    b05: Optional[Union[np.ndarray, pd.Series]] = None,
    b06: Optional[Union[np.ndarray, pd.Series]] = None,
    b07: Optional[Union[np.ndarray, pd.Series]] = None,
    b11: Optional[Union[np.ndarray, pd.Series]] = None,
    b12: Optional[Union[np.ndarray, pd.Series]] = None,
) -> Dict[str, Union[np.ndarray, pd.Series]]:
    """
    Computes key spectral ratios and band differences (Phase 4).
    """
    rels: Dict[str, Union[np.ndarray, pd.Series]] = {}

    # Selected Ratios
    rels["Ratio_B08_B04"] = safe_divide(b08, b04)
    if b05 is not None:
        rels["Ratio_B08_B05"] = safe_divide(b08, b05)
    if b06 is not None:
        rels["Ratio_B08_B06"] = safe_divide(b08, b06)
    if b07 is not None:
        rels["Ratio_B08_B07"] = safe_divide(b08, b07)
    if b11 is not None:
        rels["Ratio_B08_B11"] = safe_divide(b08, b11)
    if b12 is not None:
        rels["Ratio_B08_B12"] = safe_divide(b08, b12)

    # Selected Differences
    rels["Diff_B08_B04"] = b08 - b04
    if b05 is not None:
        rels["Diff_B08_B05"] = b08 - b05
    if b06 is not None:
        rels["Diff_B08_B06"] = b08 - b06
    if b07 is not None:
        rels["Diff_B08_B07"] = b08 - b07
    if b11 is not None:
        rels["Diff_B08_B11"] = b08 - b11

    return rels
