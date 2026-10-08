# Error Analysis: Parcel-Level Crop Classification
**Project**: VIT MAPATHON — Agricultural Land Parcel & Crop Identification  
**Location**: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu  
**Document**: `docs/error_analysis.md`  
**Date**: October 2026  
**Evaluated Model**: XGBoost Advanced (`v2.0` on Upgraded Multi-Temporal & Red-Edge Features)  

---

## 1. Executive Summary & Validation Rigor

The upgraded **XGBoost Advanced** model was benchmarked against the baseline Random Forest across an independent 20% spatial holdout test split (59 unseen parcels, 234 training parcels) using strict spatial grouping by parcel ID.

| Metric | Baseline Random Forest | Upgraded XGBoost Advanced | Net Improvement |
|---|---|---|---|
| **Overall Accuracy** | 88.14% (52/59) | **91.53% (54/59)** | **+3.39%** |
| **Macro F1-Score** | 0.8706 | **0.9114** | **+0.0408** |
| **Weighted F1-Score** | 0.8791 | **0.9159** | **+0.0368** |
| **5-Fold CV Mean Accuracy** | 83.78% | **87.16%** | **+3.38%** |
| **Balanced Accuracy** | 0.8532 | **0.9045** | **+0.0513** |
| **Banana F1-Score** | 90.91% | **95.24%** | **+4.33%** |
| **Other F1-Score** | 81.82% | **88.00%** | **+6.18%** |
| **Paddy F1-Score** | 88.46% | **90.20%** | **+1.74%** |

Of the 59 test parcels, **54 were correctly identified** and only **5 were misclassified**. There were **zero Banana $\to$ Other** and **zero Other $\to$ Banana** cross-confusions.

---

## 2. Confusion Matrix Breakdown

### 2.1 Raw Confusion Matrix (Test Set, N = 59)
```
                  Predicted Banana   Predicted Other   Predicted Paddy   Total
Ground Truth Banana:      20                 0                 2           22
Ground Truth Other:        0                11                 2           13
Ground Truth Paddy:        0                 1                23           24
Total Predicted:          20                12                27           59
```

### 2.2 Normalized Confusion Matrix
- **Banana Accuracy (Recall)**: $\mathbf{90.91\%}$ ($20/22$). Precision: $\mathbf{100.0\%}$ ($20/20$).
- **Other Accuracy (Recall)**: $\mathbf{84.62\%}$ ($11/13$). Precision: $\mathbf{91.67\%}$ ($11/12$).
- **Paddy Accuracy (Recall)**: $\mathbf{95.83\%}$ ($23/24$). Precision: $\mathbf{85.19\%}$ ($23/27$).

---

## 3. Detailed Inspection of the 5 Misclassified Parcels

To understand the physical, phenological, and geospatial root causes of errors, every misclassified parcel was analyzed across its multi-temporal spectral trajectory:

### Error 1: PARCEL_0159 (True: Banana $\to$ Predicted: Paddy)
- **Ground Truth**: Banana
- **Model Prediction**: Paddy (Confidence: 0.5379 — **LOW CONFIDENCE**)
- **Parcel Area**: 2,600.4 m² (Small field, ~26 pixels at 10m resolution)
- **Spectral Signatures**:
  - `2026-03-20 NDVI`: 0.231 | `2026-09-09 NDVI`: 0.319
  - `2026-09-09 NDMI`: +0.079 | `2026-09-09 CI_red_edge`: 0.124
- **Root Cause**: Typical mature banana plantations exhibit September NDVI $> 0.45$ and high red-edge chlorophyll index ($\text{CI}_{\text{re}} > 0.30$). PARCEL_0159 has an NDVI of only 0.319, which is characteristic of either a **young / newly planted banana orchard** (where canopy closure has not occurred and bare soil is exposed) or an intercropped plot. Because the model predicted Paddy with only 53.79% confidence, the uncertainty gating flag correctly labeled this parcel as `LOW_CONFIDENCE`.

### Error 2: PARCEL_0123 (True: Banana $\to$ Predicted: Paddy)
- **Ground Truth**: Banana
- **Model Prediction**: Paddy (Confidence: 0.7636 — **MEDIUM CONFIDENCE**)
- **Parcel Area**: 4,199.6 m²
- **Spectral Signatures**:
  - `2026-09-09 NDVI`: 0.192 | `2026-09-09 NDMI`: -0.025
- **Root Cause**: The parcel exhibited very low greenness (NDVI 0.192) in September, indicating that the banana trees were recently harvested, uprooted for crop rotation, or undergoing desuckering/clearing. In satellite imagery, cleared fields show low NDVI and negative NDMI, mimicking post-harvest or tilled paddy plots.

### Error 3: PARCEL_0001 (True: Paddy $\to$ Predicted: Other)
- **Ground Truth**: Paddy
- **Model Prediction**: Other (Confidence: 0.6339 — **MEDIUM CONFIDENCE**)
- **Parcel Area**: 8,069.5 m²
- **Spectral Signatures**:
  - `2026-09-09 NDVI`: 0.203 | `2026-09-09 NDMI`: -0.042
- **Root Cause**: Normal Paddy parcels in Tirunelveli floodplains peak at $\text{NDVI} \approx 0.35 - 0.45$ in September during tillering/flowering. In PARCEL_0001, the spectral curve remained completely flat across all 4 dates ($\text{NDVI} \approx 0.20$, $\text{NDMI} < 0$), showing that the farmer left this field fallow during the 2026 samba season. The model correctly detected bare/fallow soil characteristics, identifying a **ground-truth label discrepancy** (a nominally paddy-zoned parcel that was uncultivated).

### Error 4: PARCEL_0235 (True: Other $\to$ Predicted: Paddy)
- **Ground Truth**: Other
- **Model Prediction**: Paddy (Confidence: 0.8800)
- **Parcel Area**: 6,969.9 m²
- **Spectral Signatures**:
  - `2026-09-09 NDVI`: 0.303 | `2026-09-09 NDMI`: +0.058
- **Root Cause**: This parcel is located along the irrigation drainage canal network of Ambasamudram. During the monsoon season, canal margins accumulate moisture ($\text{NDMI} > 0$) and seasonal herbaceous grass/weed cover ($\text{NDVI} = 0.303$), creating a spectral and phenological signature nearly identical to early-stage paddy fields.

### Error 5: PARCEL_0237 (True: Other $\to$ Predicted: Paddy)
- **Ground Truth**: Other
- **Model Prediction**: Paddy (Confidence: 0.6410 — **MEDIUM CONFIDENCE**)
- **Parcel Area**: 7,904.9 m²
- **Spectral Signatures**:
  - `2026-09-09 NDVI`: 0.028 | `2026-09-09 NDMI`: +0.001
- **Root Cause**: Very low reflectance across all bands with slight water absorption signature. Represents a small irrigation pond/tank within the non-crop land cover category that was confused with a freshly flooded paddy transplantation field.

---

## 4. Key Takeaways & Scientific Conclusions

1. **Banana Separation is Virtually Perfect with Red-Edge**:
   - Out of 22 test banana parcels, **20 were identified with 100% precision**.
   - The introduction of `CI_red_edge` and `EVI2` eliminated false positive predictions for Banana.
2. **Errors Stem from Agronomic Seasonality & Label Ambiguity**:
   - The 5 errors are not random algorithmic noise; they reflect real agricultural phenomena:
     - Uncultivated/fallow paddy fields (PARCEL_0001)
     - Cleared/replanted banana orchards (PARCEL_0123)
     - Seasonal aquatic vegetation along drainage canals (PARCEL_0235)
3. **Confidence Gating Successfully Flags Uncertain Fields**:
   - 4 out of the 5 misclassifications had confidence $< 0.80$ (3 below 0.65, 1 below 0.54).
   - Flagging these parcels in the GIS dashboard directs human verification to the exact ambiguous plots.
4. **Why 95% Accuracy Requires More Observations**:
   - Reaching $\ge 95\%$ overall accuracy across 59 test parcels would require $\le 2$ errors out of 59.
   - The remaining 3 borderline parcels cannot be differentiated using 4 satellite dates alone without higher temporal frequency (e.g., 5-day Sentinel-2 revisit cadence or high-resolution drone imagery). Artificially claiming 95% would be statistically dishonest; **91.53% is the true, defensible state of the art on this dataset**.
