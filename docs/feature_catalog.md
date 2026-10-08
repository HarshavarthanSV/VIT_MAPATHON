# Sentinel-2 Advanced Feature Catalog
**Project**: VIT MAPATHON — Parcel-Level Agricultural Crop Classification  
**Study Area**: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu (EPSG:32643)  
**File**: `docs/feature_catalog.md`  
**Date**: October 2026  

---

## 1. Overview & Spectral Strategy

Copernicus Sentinel-2 MultiSpectral Instrument (MSI) Level-2A surface reflectance (BOA) data provides 13 spectral bands. For parcel-level crop discrimination in tropical canal-irrigated and riparian agro-ecosystems (Paddy, Banana, and Other), we exploit the full useful optical spectrum spanning 443 nm to 2190 nm, with a special emphasis on the **Red-Edge** inflection zone (705–783 nm) and shortwave infrared moisture sensitivity.

All bands and derived features are aligned to a **common 10-meter analysis grid** (EPSG:32643 / WGS 84 UTM Zone 43N). Native 20m bands are resampled using **Bilinear Interpolation** for continuous reflectance metrics and **Nearest-Neighbor** for discrete categorical masks (SCL).

---

## 2. Spectral Bands (Raw Surface Reflectance)

| Feature Name | Band ID | Central Wavelength (nm) | Bandwidth (nm) | Native Resolution | Resampling Method | Interpretation in Agricultural Mapping | Used in Final Model |
|---|---|---|---|---|---|---|---|
| **B02** | Blue | 490 | 65 | 10 m | None (Native) | Sensitive to atmospheric scattering, soil background, and chlorophyll absorption. | Yes |
| **B03** | Green | 560 | 35 | 10 m | None (Native) | Reflectance peak for green vegetation; essential for NDWI and GNDVI. | Yes |
| **B04** | Red | 665 | 30 | 10 m | None (Native) | Primary chlorophyll-a/b absorption pit; critical for NDVI, EVI, and biomass contrasts. | Yes |
| **B05** | Red Edge 1 | 705 | 15 | 20 m | Bilinear to 10m | Onset of the red-edge inflection; sensitive to low-to-medium chlorophyll concentrations without saturation. | Yes |
| **B06** | Red Edge 2 | 740 | 15 | 20 m | Bilinear to 10m | Steepest portion of the red-edge slope; strongly correlated with canopy nitrogen content and leaf area index (LAI). | Yes |
| **B07** | Red Edge 3 | 783 | 20 | 20 m | Bilinear to 10m | Transition to NIR reflectance plateau; sensitive to high biomass, canopy architecture, and multi-layer scattering. | Yes |
| **B08** | Broad NIR | 842 | 115 | 10 m | None (Native) | High scattering by spongy mesophyll leaf tissue; dominant indicator of vegetation canopy density. | Yes |
| **B8A** | Narrow NIR | 865 | 20 | 20 m | Bilinear to 10m | Narrow NIR band avoiding water vapor absorption at 820 nm; cleaner spectral signature for biomass estimation. | Yes |
| **B11** | SWIR 1 | 1610 | 90 | 20 m | Bilinear to 10m | Sensitive to leaf cellular water content and soil moisture; discriminates flooded paddy fields. | Yes |
| **B12** | SWIR 2 | 2190 | 180 | 20 m | Bilinear to 10m | Sensitive to lignin, cellulose, dry biomass, and bare soil background. | Yes |

---

## 3. Vegetation & Canopy Indices

### 3.1 NDVI (Normalized Difference Vegetation Index)
- **Formula**:  
  $$\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$$
- **Input Bands**: B08 (NIR), B04 (Red)
- **Interpretation**: Standard measure of green vegetation vitality and photosynthetic capacity. Ranges from -1.0 to +1.0.
- **Native Resolution Considerations**: Both B08 and B04 are native 10m.
- **Used in Final Model**: Yes (Core baseline & phenology tracker).

### 3.2 EVI (Enhanced Vegetation Index)
- **Formula**:  
  $$\text{EVI} = 2.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + 6.0 \cdot \text{B04} - 7.5 \cdot \text{B02} + 1.0}$$
- **Input Bands**: B08 (NIR), B04 (Red), B02 (Blue)
- **Interpretation**: Decouples canopy greenness from background soil and atmospheric aerosols; does not saturate as easily as NDVI over dense banana plantations.
- **Native Resolution Considerations**: B08, B04, B02 are all native 10m.
- **Used in Final Model**: Yes.

### 3.3 EVI2 (Two-Band Enhanced Vegetation Index)
- **Formula**:  
  $$\text{EVI2} = 2.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + 2.4 \cdot \text{B04} + 1.0}$$
- **Input Bands**: B08 (NIR), B04 (Red)
- **Interpretation**: Retains EVI's dynamic range without introducing noise from the blue band (B02) which is susceptible to sub-pixel haze.
- **Native Resolution Considerations**: Both bands native 10m.
- **Used in Final Model**: Yes.

### 3.4 SAVI (Soil Adjusted Vegetation Index)
- **Formula**:  
  $$\text{SAVI} = 1.5 \times \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 0.5}$$
- **Input Bands**: B08 (NIR), B04 (Red)
- **Interpretation**: Incorporates soil brightness adjustment factor ($L = 0.5$) for emerging paddy seedlings where soil/water reflectance dominates.
- **Native Resolution Considerations**: Native 10m.
- **Used in Final Model**: Yes.

### 3.5 MSAVI (Modified Soil Adjusted Vegetation Index)
- **Formula**:  
  $$\text{MSAVI} = \frac{2 \cdot \text{B08} + 1 - \sqrt{(2 \cdot \text{B08} + 1)^2 - 8 \cdot (\text{B08} - \text{B04})}}{2}$$
- **Input Bands**: B08 (NIR), B04 (Red)
- **Interpretation**: Self-adjusting soil factor; ideal for low canopy cover early in the paddy crop cycle.
- **Native Resolution Considerations**: Native 10m.
- **Used in Final Model**: Yes.

### 3.6 OSAVI (Optimized Soil Adjusted Vegetation Index)
- **Formula**:  
  $$\text{OSAVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04} + 0.16}$$
- **Input Bands**: B08 (NIR), B04 (Red)
- **Interpretation**: Optimized for agricultural canopies with varying soil brightness (Rondeaux et al., 1996).
- **Native Resolution Considerations**: Native 10m.
- **Used in Final Model**: Yes.

### 3.7 GNDVI (Green Normalized Difference Vegetation Index)
- **Formula**:  
  $$\text{GNDVI} = \frac{\text{B08} - \text{B03}}{\text{B08} + \text{B03}}$$
- **Input Bands**: B08 (NIR), B03 (Green)
- **Interpretation**: More sensitive to canopy chlorophyll variation than NDVI during mid-to-late growth stages.
- **Native Resolution Considerations**: Native 10m.
- **Used in Final Model**: Yes.

---

## 4. Red-Edge & Chlorophyll Indices

### 4.1 NDRE_B05 (Normalized Difference Red Edge 1)
- **Formula**:  
  $$\text{NDRE}_{\text{B05}} = \frac{\text{B08} - \text{B05}}{\text{B08} + \text{B05}}$$
- **Input Bands**: B08 (NIR 10m), B05 (Red Edge 705 nm, 20m resampled)
- **Interpretation**: Highly sensitive to leaf chlorophyll content at the 705 nm red-edge inflection boundary; avoids saturation over dense perennial banana plantations.
- **Native Resolution Considerations**: B05 resampled from 20m to 10m grid using bilinear interpolation.
- **Used in Final Model**: Yes (Top discriminative feature).

### 4.2 NDRE_B06 (Normalized Difference Red Edge 2)
- **Formula**:  
  $$\text{NDRE}_{\text{B06}} = \frac{\text{B08} - \text{B06}}{\text{B08} + \text{B06}}$$
- **Input Bands**: B08 (NIR 10m), B06 (Red Edge 740 nm, 20m resampled)
- **Interpretation**: Captures chlorophyll and structural scattering midway through the red edge.
- **Native Resolution Considerations**: B06 resampled to 10m.
- **Used in Final Model**: Yes.

### 4.3 NDRE_B07 (Normalized Difference Red Edge 3)
- **Formula**:  
  $$\text{NDRE}_{\text{B07}} = \frac{\text{B08} - \text{B07}}{\text{B08} + \text{B07}}$$
- **Input Bands**: B08 (NIR 10m), B07 (Red Edge 783 nm, 20m resampled)
- **Interpretation**: Measures the near-plateau red-edge contrast; highly correlated with canopy depth.
- **Native Resolution Considerations**: B07 resampled to 10m.
- **Used in Final Model**: Yes.

### 4.4 MTCI (MERIS Terrestrial Chlorophyll Index)
- **Formula**:  
  $$\text{MTCI} = \frac{\text{B06} - \text{B05}}{\text{B05} - \text{B04} + \epsilon}$$
- **Input Bands**: B06 (740 nm), B05 (705 nm), B04 (665 nm)
- **Interpretation**: Calculates red-edge position shift; directly correlates with total chlorophyll accumulation in agricultural crops (Dash & Curran, 2004).
- **Native Resolution Considerations**: B05, B06 resampled to 10m; B04 native 10m. $\epsilon = 10^{-6}$ protects against zero division.
- **Used in Final Model**: Yes.

### 4.5 CI_red_edge (Chlorophyll Index Red-Edge)
- **Formula**:  
  $$\text{CI}_{\text{re}} = \frac{\text{B07}}{\text{B05} + \epsilon} - 1.0$$
- **Input Bands**: B07 (783 nm), B05 (705 nm)
- **Interpretation**: Linear relationship with canopy chlorophyll over a broad dynamic range (Gitelson et al., 2005).
- **Native Resolution Considerations**: Both bands 20m resampled to 10m.
- **Used in Final Model**: Yes.

---

## 5. Moisture & Water Indices

### 5.1 NDWI (Normalized Difference Water Index - McFeeters)
- **Formula**:  
  $$\text{NDWI} = \frac{\text{B03} - \text{B08}}{\text{B03} + \text{B08}}$$
- **Input Bands**: B03 (Green), B08 (NIR)
- **Interpretation**: Water features appear positive (> 0); land and vegetation are negative. Delineates paddy field flooding and irrigation canals.
- **Native Resolution Considerations**: Native 10m.
- **Used in Final Model**: Yes.

### 5.2 NDMI (Normalized Difference Moisture Index / Gao NDWI)
- **Formula**:  
  $$\text{NDMI} = \frac{\text{B08} - \text{B11}}{\text{B08} + \text{B11}}$$
- **Input Bands**: B08 (NIR), B11 (SWIR 1)
- **Interpretation**: Directly measures canopy water thickness and leaf turgor. Distinguishes well-watered banana plantations from rainfed or fallow plots.
- **Native Resolution Considerations**: B11 resampled to 10m.
- **Used in Final Model**: Yes.

### 5.3 MSI (Moisture Stress Index)
- **Formula**:  
  $$\text{MSI} = \frac{\text{B11}}{\text{B08} + \epsilon}$$
- **Input Bands**: B11 (SWIR 1), B08 (NIR)
- **Interpretation**: Higher values indicate severe moisture stress or dry fallow soil; low values indicate lush, well-irrigated vegetation.
- **Native Resolution Considerations**: B11 resampled to 10m.
- **Used in Final Model**: Yes.

---

## 6. Spectral Relationship Features (Ratios & Differences)

| Feature Name | Formula | Inputs | Scientific Rationale | Used in Final Model |
|---|---|---|---|---|
| **Ratio_B08_B04** | $\text{B08} / (\text{B04} + \epsilon)$ | NIR, Red | Simple Ratio (Jordan, 1969); sensitive to high LAI where NDVI saturates. | Yes |
| **Ratio_B08_B05** | $\text{B08} / (\text{B05} + \epsilon)$ | NIR, RE1 | Red-edge simple ratio; discriminates banana leaf thickness. | Yes |
| **Ratio_B08_B06** | $\text{B08} / (\text{B06} + \epsilon)$ | NIR, RE2 | Red-edge slope steepness ratio. | Yes |
| **Ratio_B08_B07** | $\text{B08} / (\text{B07} + \epsilon)$ | NIR, RE3 | NIR-to-plateau ratio. | Yes |
| **Ratio_B08_B11** | $\text{B08} / (\text{B11} + \epsilon)$ | NIR, SWIR1 | Vegetative water content contrast. Flooded paddy produces distinct ratio. | Yes |
| **Ratio_B08_B12** | $\text{B08} / (\text{B12} + \epsilon)$ | NIR, SWIR2 | Woody/lignin vs green canopy contrast. | Yes |
| **Diff_B08_B04** | $\text{B08} - \text{B04}$ | NIR, Red | Absolute photosynthetic amplitude. | Yes |
| **Diff_B08_B05** | $\text{B08} - \text{B05}$ | NIR, RE1 | Absolute red-edge step height. | Yes |
| **Diff_B08_B06** | $\text{B08} - \text{B06}$ | NIR, RE2 | Transition step height. | Yes |
| **Diff_B08_B07** | $\text{B08} - \text{B07}$ | NIR, RE3 | High-frequency canopy depth. | Yes |
| **Diff_B08_B11** | $\text{B08} - \text{B11}$ | NIR, SWIR1 | Absolute moisture contrast. | Yes |

---

## 7. Multi-Temporal Statistics & Phenology Features

### 7.1 Multi-Temporal Summary Statistics (Per Feature across Dates)
For each key spectral band and index time series per parcel:
1. `mean`: Central tendency across season.
2. `median`: Robust seasonal central value resistant to residual cloud artifacts.
3. `min`: Basal ground/transplanting signature.
4. `max`: Peak vegetative canopy expression.
5. `std`: Magnitude of seasonal fluctuation.
6. `range`: Amplitude ($\text{max} - \text{min}$).
7. `P10`: 10th percentile (robust lower baseline).
8. `P25`: 25th percentile (early growth floor).
9. `P75`: 75th percentile (late canopy ceiling).
10. `P90`: 90th percentile (robust peak indicator).

### 7.2 Crop Phenological Dynamics & Derivatives

| Feature Name | Computation Formula / Logic | Phenological Meaning |
|---|---|---|
| **NDVI_peak_value** | $\max_t (\text{NDVI}_t)$ | Maximum photosynthetic biomass achieved during the growing season. |
| **NDVI_peak_date** | $\operatorname{argmax}_t (\text{NDVI}_t)$ | Date/observation index of maximum vegetative canopy closure. |
| **NDRE_peak_value** | $\max_t (\text{NDRE}_{\text{B05}, t})$ | Maximum chlorophyll density reached. |
| **NDRE_peak_date** | $\operatorname{argmax}_t (\text{NDRE}_{\text{B05}, t})$ | Timing of peak nitrogen/chlorophyll content. |
| **NDMI_peak_value** | $\max_t (\text{NDMI}_t)$ | Peak canopy water content. |
| **NDMI_peak_date** | $\operatorname{argmax}_t (\text{NDMI}_t)$ | Timing of peak parcel irrigation/flooding. |
| **EVI_peak_value** | $\max_t (\text{EVI}_t)$ | Peak non-saturating structural biomass. |
| **EVI_peak_date** | $\operatorname{argmax}_t (\text{EVI}_t)$ | Timing of peak structural canopy. |
| **max_growth_rate** | $\max_t \left( \frac{\text{NDVI}_{t+1} - \text{NDVI}_t}{\Delta \text{days}} \right)$ | Maximum rate of vegetative green-up (fast in Paddy, stable in Banana). |
| **max_decline_rate** | $\min_t \left( \frac{\text{NDVI}_{t+1} - \text{NDVI}_t}{\Delta \text{days}} \right)$ | Maximum senescence/harvest rate (steep in harvested Paddy). |
| **seasonal_amplitude** | $\max_t (\text{NDVI}_t) - \min_t (\text{NDVI}_t)$ | Net phenological swing. High in seasonal Paddy; low in perennial Banana. |
| **vegetation_duration** | $\sum_t \mathbb{I}(\text{NDVI}_t \ge 0.35)$ | Number of observations maintaining active photosynthetic cover. |
| **auc_NDVI** | $\sum_t \frac{\text{NDVI}_t + \text{NDVI}_{t+1}}{2} \cdot \Delta t$ | Cumulative seasonal vegetative productivity (trapezoidal integral). |
| **auc_NDRE** | $\sum_t \frac{\text{NDRE}_t + \text{NDRE}_{t+1}}{2} \cdot \Delta t$ | Cumulative seasonal chlorophyll accumulation. |
| **delta_NDVI_consec** | $\text{NDVI}_{t+1} - \text{NDVI}_t$ | Temporal step derivatives tracking intra-seasonal trajectory. |
| **delta_NDRE_consec** | $\text{NDRE}_{t+1} - \text{NDRE}_t$ | Red-edge step changes tracking chlorophyll dynamics. |
| **delta_NDMI_consec** | $\text{NDMI}_{t+1} - \text{NDMI}_t$ | Moisture step changes tracking flooding and drainage cycles. |

---

## 8. Parcel-Level Zonal Statistics & Quality Control

For each parcel polygon, valid pixels (excluding SCL clouds, shadows, and NoData) are summarized using:
- **Zonal Statistics**: `mean`, `median`, `min`, `max`, `std`, `P10`, `P25`, `P75`, `P90`.
- **Data Quality Control**:
  - `valid_pixel_count`: Number of clear unmasked 10m pixels inside parcel.
  - `valid_pixel_ratio`: Ratio of valid pixels to total parcel area ($\text{pixels} \cdot 100 \text{ m}^2 / \text{area\_m2}$).
  - `number_of_valid_dates`: Count of multi-temporal scenes with $\ge 50\%$ valid pixels.
  - `data_quality_flag`:
    - `GOOD`: $\ge 80\%$ valid pixels across all 4 dates.
    - `LIMITED`: $50\% - 79\%$ valid pixels or 3 valid dates.
    - `INSUFFICIENT`: $< 50\%$ valid pixels or $< 3$ valid dates (flagged for GIS inspection).
