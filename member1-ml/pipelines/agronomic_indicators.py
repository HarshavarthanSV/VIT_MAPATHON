"""
Member 1 — AI / ML & Backend Systems
Module: Agronomic Crop Health & Hazard Monitoring Calculator
Provides standardized, formula-driven calculation of:
1. Crop Health Condition (Healthy, Moderate Stress, Severe Stress, Unknown)
2. Normalized Health Score (0.0 to 1.0)
3. Multi-temporal Hazard Impact (Flood, Drought, Cyclone, Potential, None)
4. Calibrated damage percentage with multi-spectral supporting evidence.
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("AgronomicIndicators")

# Crop-specific NDVI thresholds for health condition classification
HEALTH_THRESHOLDS = {
    "Paddy": {
        "healthy_ndvi": 0.60,
        "moderate_ndvi": 0.40,
        "optimal_ndvi_range": (0.60, 0.85)
    },
    "Banana": {
        "healthy_ndvi": 0.65,
        "moderate_ndvi": 0.45,
        "optimal_ndvi_range": (0.65, 0.90)
    },
    "Other": {
        "healthy_ndvi": 0.50,
        "moderate_ndvi": 0.35,
        "optimal_ndvi_range": (0.50, 0.80)
    }
}


def calculate_crop_health(
    crop_name: str,
    ndvi: Optional[float],
    ndwi: Optional[float] = None,
    evi: Optional[float] = None,
    confidence: float = 1.0
) -> Tuple[str, float]:
    """
    Computes crop health status and a normalized health score (0.0 to 1.0).
    Formula:
      - Paddy: Healthy (NDVI >= 0.60), Moderate Stress (0.40 <= NDVI < 0.60), Severe Stress (NDVI < 0.40)
      - Banana: Healthy (NDVI >= 0.65), Moderate Stress (0.45 <= NDVI < 0.65), Severe Stress (NDVI < 0.45)
      - Other: Healthy (NDVI >= 0.50), Moderate Stress (0.35 <= NDVI < 0.50), Severe Stress (NDVI < 0.35)
      - Health Score = clip(0.60 * (NDVI / 0.85) + 0.20 * max(0, NDWI + 0.2) + 0.20 * confidence, 0.0, 1.0)
    """
    if ndvi is None or (ndvi != ndvi):  # NaN check
        return "Unknown", 0.0

    thresholds = HEALTH_THRESHOLDS.get(crop_name, HEALTH_THRESHOLDS["Other"])
    healthy_min = thresholds["healthy_ndvi"]
    moderate_min = thresholds["moderate_ndvi"]

    if ndvi >= healthy_min:
        status = "Healthy"
    elif ndvi >= moderate_min:
        status = "Moderate Stress"
    else:
        status = "Severe Stress"

    # Health score computation
    ndwi_val = ndwi if (ndwi is not None and ndwi == ndwi) else 0.0
    norm_ndvi = max(0.0, min(1.0, ndvi / 0.85))
    norm_ndwi = max(0.0, min(1.0, (ndwi_val + 0.20) / 0.60))
    health_score = round(float(0.60 * norm_ndvi + 0.20 * norm_ndwi + 0.20 * min(1.0, confidence)), 3)

    return status, health_score


def assess_hazard_impact(
    crop_name: str,
    current_ndvi: Optional[float],
    current_ndwi: Optional[float],
    baseline_ndvi: Optional[float] = None,
    baseline_ndwi: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates potential hazards by comparing current observation against baseline.
    Rules:
      - Flood:
        Requires water evidence (Delta NDWI >= +0.20) AND vegetation decline (Delta NDVI <= -0.20).
      - Drought:
        Requires severe water deficit (NDWI < -0.15) AND persistent vegetation stress (NDVI < 0.35)
        with Delta NDWI <= -0.15.
      - If evidence is insufficient:
        Returns hazard = 'None' or 'Potential' rather than inventing a confirmed disaster.
    """
    if current_ndvi is None or (current_ndvi != current_ndvi):
        return {
            "hazard": "None",
            "severity": "None",
            "damage_percent": 0.0,
            "evidence": "Insufficient spectral data"
        }

    c_ndvi = float(current_ndvi)
    c_ndwi = float(current_ndwi) if (current_ndwi is not None and current_ndwi == current_ndwi) else 0.0

    # If no baseline provided, return baseline state
    if baseline_ndvi is None or (baseline_ndvi != baseline_ndvi):
        return {
            "hazard": "None",
            "severity": "None",
            "damage_percent": 0.0,
            "evidence": "Single observation baseline established"
        }

    b_ndvi = float(baseline_ndvi)
    b_ndwi = float(baseline_ndwi) if (baseline_ndwi is not None and baseline_ndwi == baseline_ndwi) else 0.0

    delta_ndvi = c_ndvi - b_ndvi
    delta_ndwi = c_ndwi - b_ndwi

    # 1. Flood Verification: Water surge + Canopy destruction
    if delta_ndwi >= 0.20 and delta_ndvi <= -0.20 and c_ndwi > 0.10:
        # Damage calibrated by NDVI drop
        drop_pct = abs(delta_ndvi) / max(b_ndvi, 0.1) * 100.0
        damage_pct = round(min(100.0, max(15.0, drop_pct)), 1)

        if damage_pct >= 50.0:
            severity = "Severe"
        elif damage_pct >= 30.0:
            severity = "Moderate"
        else:
            severity = "Low"

        return {
            "hazard": "Flood",
            "severity": severity,
            "damage_percent": damage_pct,
            "evidence": f"Water surge (Delta NDWI: {delta_ndwi:+.3f}) with canopy submergence (Delta NDVI: {delta_ndvi:+.3f})"
        }

    # 2. Drought Verification: Severe moisture depletion + persistent stress
    if c_ndwi < -0.15 and delta_ndwi <= -0.15 and c_ndvi < 0.38 and delta_ndvi <= -0.15:
        drop_pct = abs(delta_ndvi) / max(b_ndvi, 0.1) * 100.0
        damage_pct = round(min(80.0, max(10.0, drop_pct)), 1)
        severity = "Moderate" if damage_pct >= 30.0 else "Low"

        return {
            "hazard": "Drought",
            "severity": severity,
            "damage_percent": damage_pct,
            "evidence": f"Moisture deficit (NDWI: {c_ndwi:.3f}, Delta: {delta_ndwi:+.3f}) and vegetative degradation (NDVI: {c_ndvi:.3f})"
        }

    # 3. Unsubstantiated NDVI drop (e.g. normal harvest or seasonal senescence)
    if delta_ndvi <= -0.25:
        # Distinguish harvest / tillage from disaster
        return {
            "hazard": "Potential",
            "severity": "Low",
            "damage_percent": 0.0,
            "evidence": f"Unconfirmed NDVI drop ({delta_ndvi:+.3f}) without water/drought evidence. Likely crop harvest or field rotation."
        }

    return {
        "hazard": "None",
        "severity": "None",
        "damage_percent": 0.0,
        "evidence": "Spectral parameters within normal vegetative tolerances"
    }
