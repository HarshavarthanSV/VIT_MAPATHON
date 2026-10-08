"""
Crop Phenology and Multi-Temporal Feature Extraction Module.
Phases 5, 6, 7 of the Crop Classification Upgrade Pipeline.
Derives growth fingerprints, phenological milestones, temporal statistics,
and consecutive temporal derivatives for each parcel time-series.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


def compute_temporal_summary_statistics(
    series_values: np.ndarray,
    prefix: str
) -> Dict[str, float]:
    """
    Computes 10 robust multi-temporal statistics across available observations:
    mean, median, min, max, std, range, P10, P25, P75, P90.
    """
    valid = series_values[~np.isnan(series_values)]
    if len(valid) == 0:
        return {
            f"{prefix}_temporal_mean": 0.0,
            f"{prefix}_temporal_median": 0.0,
            f"{prefix}_temporal_min": 0.0,
            f"{prefix}_temporal_max": 0.0,
            f"{prefix}_temporal_std": 0.0,
            f"{prefix}_temporal_range": 0.0,
            f"{prefix}_temporal_p10": 0.0,
            f"{prefix}_temporal_p25": 0.0,
            f"{prefix}_temporal_p75": 0.0,
            f"{prefix}_temporal_p90": 0.0,
        }

    val_min = float(np.min(valid))
    val_max = float(np.max(valid))
    return {
        f"{prefix}_temporal_mean": round(float(np.mean(valid)), 5),
        f"{prefix}_temporal_median": round(float(np.median(valid)), 5),
        f"{prefix}_temporal_min": round(val_min, 5),
        f"{prefix}_temporal_max": round(val_max, 5),
        f"{prefix}_temporal_std": round(float(np.std(valid)), 5),
        f"{prefix}_temporal_range": round(float(val_max - val_min), 5),
        f"{prefix}_temporal_p10": round(float(np.percentile(valid, 10)), 5),
        f"{prefix}_temporal_p25": round(float(np.percentile(valid, 25)), 5),
        f"{prefix}_temporal_p75": round(float(np.percentile(valid, 75)), 5),
        f"{prefix}_temporal_p90": round(float(np.percentile(valid, 90)), 5),
    }


def compute_phenology_metrics(
    dates: List[str],
    ndvi_ts: np.ndarray,
    ndre_ts: np.ndarray,
    ndmi_ts: np.ndarray,
    evi_ts: np.ndarray,
) -> Dict[str, float]:
    """
    Derives crop growth fingerprint per parcel (Phase 6):
    - Peak values and peak observation dates for NDVI, NDRE, NDMI, EVI
    - Maximum growth rate (green-up velocity)
    - Maximum decline rate (senescence/harvest velocity)
    - Seasonal amplitude
    - Vegetation duration (observations >= threshold)
    - Area under the curve (AUC via trapezoidal rule)
    """
    # Days offset from start date
    dt_objects = pd.to_datetime(dates)
    day_offsets = (dt_objects - dt_objects[0]).days.values.astype(float)
    if day_offsets[-1] == 0:
        day_offsets = np.arange(len(dates), dtype=float)

    n_obs = len(dates)
    metrics: Dict[str, float] = {}

    # Helper for peaks
    def get_peak_and_idx(arr: np.ndarray, name: str):
        valid = ~np.isnan(arr)
        if not np.any(valid):
            return 0.0, -1
        idx = int(np.argmax(arr))
        return round(float(arr[idx]), 5), idx

    ndvi_peak, ndvi_peak_idx = get_peak_and_idx(ndvi_ts, "NDVI")
    ndre_peak, ndre_peak_idx = get_peak_and_idx(ndre_ts, "NDRE")
    ndmi_peak, ndmi_peak_idx = get_peak_and_idx(ndmi_ts, "NDMI")
    evi_peak, evi_peak_idx = get_peak_and_idx(evi_ts, "EVI")

    metrics["pheno_ndvi_peak_val"] = ndvi_peak
    metrics["pheno_ndvi_peak_date_idx"] = float(ndvi_peak_idx)
    metrics["pheno_ndre_peak_val"] = ndre_peak
    metrics["pheno_ndre_peak_date_idx"] = float(ndre_peak_idx)
    metrics["pheno_ndmi_peak_val"] = ndmi_peak
    metrics["pheno_ndmi_peak_date_idx"] = float(ndmi_peak_idx)
    metrics["pheno_evi_peak_val"] = evi_peak
    metrics["pheno_evi_peak_date_idx"] = float(evi_peak_idx)

    # Seasonal Amplitudes
    metrics["pheno_ndvi_amplitude"] = round(float(np.ptp(ndvi_ts[~np.isnan(ndvi_ts)])), 5)
    metrics["pheno_ndre_amplitude"] = round(float(np.ptp(ndre_ts[~np.isnan(ndre_ts)])), 5)
    metrics["pheno_ndmi_amplitude"] = round(float(np.ptp(ndmi_ts[~np.isnan(ndmi_ts)])), 5)

    # Growth and Decline Rates (delta value / delta days)
    rates_ndvi = []
    rates_ndre = []
    for i in range(len(dates) - 1):
        dt = max(day_offsets[i+1] - day_offsets[i], 1.0)
        d_ndvi = (ndvi_ts[i+1] - ndvi_ts[i]) / dt
        d_ndre = (ndre_ts[i+1] - ndre_ts[i]) / dt
        rates_ndvi.append(d_ndvi)
        rates_ndre.append(d_ndre)

    if rates_ndvi:
        metrics["pheno_max_ndvi_growth_rate"] = round(float(np.max(rates_ndvi)), 6)
        metrics["pheno_max_ndvi_decline_rate"] = round(float(np.min(rates_ndvi)), 6)
        metrics["pheno_mean_ndvi_rate"] = round(float(np.mean(rates_ndvi)), 6)
    else:
        metrics["pheno_max_ndvi_growth_rate"] = 0.0
        metrics["pheno_max_ndvi_decline_rate"] = 0.0
        metrics["pheno_mean_ndvi_rate"] = 0.0

    if rates_ndre:
        metrics["pheno_max_ndre_growth_rate"] = round(float(np.max(rates_ndre)), 6)
        metrics["pheno_max_ndre_decline_rate"] = round(float(np.min(rates_ndre)), 6)
    else:
        metrics["pheno_max_ndre_growth_rate"] = 0.0
        metrics["pheno_max_ndre_decline_rate"] = 0.0

    # Vegetation Duration (observations above thresholds)
    metrics["pheno_ndvi_obs_above_030"] = float(np.sum(ndvi_ts >= 0.30))
    metrics["pheno_ndvi_obs_above_035"] = float(np.sum(ndvi_ts >= 0.35))
    metrics["pheno_ndvi_obs_above_045"] = float(np.sum(ndvi_ts >= 0.45))
    metrics["pheno_vegetation_duration_ratio"] = round(float(metrics["pheno_ndvi_obs_above_035"] / n_obs), 4)

    # Area Under the Curve (Trapezoidal integration over day offsets)
    try:
        auc_ndvi = np.trapezoid(ndvi_ts, day_offsets) if hasattr(np, "trapezoid") else np.trapz(ndvi_ts, day_offsets)
        auc_ndre = np.trapezoid(ndre_ts, day_offsets) if hasattr(np, "trapezoid") else np.trapz(ndre_ts, day_offsets)
        # Normalize by total duration
        total_days = max(day_offsets[-1] - day_offsets[0], 1.0)
        metrics["pheno_auc_ndvi_normalized"] = round(float(auc_ndvi / total_days), 5)
        metrics["pheno_auc_ndre_normalized"] = round(float(auc_ndre / total_days), 5)
    except Exception:
        metrics["pheno_auc_ndvi_normalized"] = round(float(np.mean(ndvi_ts)), 5)
        metrics["pheno_auc_ndre_normalized"] = round(float(np.mean(ndre_ts)), 5)

    return metrics


def compute_temporal_derivatives(
    dates: List[str],
    ndvi_ts: np.ndarray,
    ndre_ts: np.ndarray,
    ndmi_ts: np.ndarray,
    evi_ts: np.ndarray,
) -> Dict[str, float]:
    """
    Computes step changes between consecutive valid satellite observations (Phase 7):
    delta = current_value - previous_value
    plus maximum positive change, maximum negative change, mean change, temporal standard deviation.
    """
    derivs: Dict[str, float] = {}

    def extract_consecutive_deltas(arr: np.ndarray, name: str):
        deltas = []
        for i in range(len(arr) - 1):
            d_val = round(float(arr[i+1] - arr[i]), 5)
            derivs[f"delta_{name}_step_{i+1}_to_{i+2}"] = d_val
            deltas.append(d_val)
        if deltas:
            derivs[f"delta_{name}_max_pos"] = round(float(np.max(deltas)), 5)
            derivs[f"delta_{name}_max_neg"] = round(float(np.min(deltas)), 5)
            derivs[f"delta_{name}_mean_change"] = round(float(np.mean(deltas)), 5)
            derivs[f"delta_{name}_std_change"] = round(float(np.std(deltas)), 5)

    extract_consecutive_deltas(ndvi_ts, "NDVI")
    extract_consecutive_deltas(ndre_ts, "NDRE")
    extract_consecutive_deltas(ndmi_ts, "NDMI")
    extract_consecutive_deltas(evi_ts, "EVI")

    return derivs
