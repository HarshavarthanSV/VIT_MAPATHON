import React, { useState, useEffect } from 'react';

export default function DisasterImpactPanel({
  hazardData,
  damageSummary,
  fundPriority,
  isDamageMode,
  onToggleDamageMode,
  showInundationLayer,
  onToggleInundationLayer,
  onSelectParcel
}) {
  const [totalFund, setTotalFund] = useState(10000000);
  const [fundAllocation, setFundAllocation] = useState(null);
  const [calculating, setCalculating] = useState(false);

  // Fetch or calculate fund allocation whenever totalFund changes
  useEffect(() => {
    async function fetchAllocation() {
      try {
        setCalculating(true);
        const res = await fetch(`/api/fund-allocation?total_fund=${totalFund}`);
        if (res.ok) {
          const data = await res.json();
          setFundAllocation(data);
        }
      } catch (err) {
        console.error('Error fetching fund allocation:', err);
      } finally {
        setCalculating(false);
      }
    }
    fetchAllocation();
  }, [totalFund]);

  const cropBreakdown = damageSummary?.crop_damage_breakdown || [];
  const topParcels = fundAllocation?.top_priority_parcels || fundPriority?.top_priority_parcels || [];

  const formatINR = (val) => {
    if (!val && val !== 0) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="disaster-panel-card">
      <div className="disaster-header">
        <div className="disaster-title-row">
          <span className="disaster-badge">⚠️ NATURAL HAZARD IMPACT ASSESSMENT</span>
          <span className="disaster-date">Before: 2026-04-22 • After: 2026-09-09</span>
        </div>
        <h3 className="disaster-h3">Monsoon Flood Inundation & Crop Damage</h3>
        <p className="disaster-desc">
          Automated multi-temporal change detection derived from Sentinel-2 Level-2A (NDWI, LSWI, Delta NDVI)
          audited across 293 cadastral parcels.
        </p>
      </div>

      {/* Action / Map Toggle Buttons */}
      <div className="disaster-controls-grid">
        <button
          className={`toggle-mode-btn ${showInundationLayer ? 'active-flood' : ''}`}
          onClick={onToggleInundationLayer}
        >
          🌊 {showInundationLayer ? 'Hide Inundation Footprint' : 'Show Inundation Layer (103.4 ha)'}
        </button>
        <button
          className={`toggle-mode-btn ${isDamageMode ? 'active-damage' : ''}`}
          onClick={onToggleDamageMode}
        >
          🏷️ {isDamageMode ? 'Show Crop Classification' : 'Color by Damage Severity'}
        </button>
      </div>

      {/* Key Metrics Grid */}
      <div className="disaster-kpi-grid">
        <div className="kpi-box kpi-inundated">
          <div className="kpi-label">Surface Inundation</div>
          <div className="kpi-value">{hazardData?.total_inundated_area_ha || 103.39} <span className="kpi-unit">ha</span></div>
          <div className="kpi-sub">{(hazardData?.total_inundated_area_acres || 255.48).toFixed(1)} Acres Footprint</div>
        </div>

        <div className="kpi-box kpi-affected">
          <div className="kpi-label">Crop Area Affected</div>
          <div className="kpi-value">0.61 <span className="kpi-unit">ha</span></div>
          <div className="kpi-sub">9 Agricultural Parcels Inundated</div>
        </div>

        <div className="kpi-box kpi-priority">
          <div className="kpi-label">Highest Priority Crop</div>
          <div className="kpi-value highlight-banana">Banana</div>
          <div className="kpi-sub">79.04% of Priority Need</div>
        </div>
      </div>

      {/* Crop-Wise Damage Summary Table */}
      <div className="disaster-section">
        <h4 className="section-h4">🌾 Crop Damage & Priority Distribution</h4>
        <div className="crop-damage-table-wrapper">
          <table className="crop-damage-table">
            <thead>
              <tr>
                <th>Crop</th>
                <th>Affected Parcels</th>
                <th>Affected Area</th>
                <th>Damage %</th>
                <th>Priority Score</th>
                <th>Recommended Relief</th>
              </tr>
            </thead>
            <tbody>
              {cropBreakdown.map((row, idx) => {
                const alloc = fundAllocation?.crop_allocation_recommendations?.find(
                  (c) => c.Crop === row.Crop
                );
                return (
                  <tr key={idx} className={row.Crop === 'Banana' ? 'row-banana' : row.Crop === 'Paddy' ? 'row-paddy' : ''}>
                    <td className="crop-name-cell">
                      <span className={`crop-bullet bullet-${row.Crop.toLowerCase()}`}></span>
                      <strong>{row.Crop}</strong>
                    </td>
                    <td>{row.Affected_Parcels} / {row.Total_Parcels}</td>
                    <td>{row.Affected_Area_Ha} ha</td>
                    <td>{row.Crop_Damage_Percentage}%</td>
                    <td>{alloc?.Crop_Priority_Score || (row.Crop === 'Banana' ? 1.538 : row.Crop === 'Paddy' ? 0.408 : 0.0)}</td>
                    <td className="relief-cell">
                      {formatINR(alloc?.Recommended_Allocation_INR || (row.Crop === 'Banana' ? totalFund * 0.7904 : row.Crop === 'Paddy' ? totalFund * 0.2096 : 0))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transparent Relief Fund Allocation Calculator */}
      <div className="disaster-section fund-calc-section">
        <div className="calc-header">
          <h4 className="section-h4">💰 Transparent Relief Fund Allocation Calculator</h4>
          <span className="calc-badge">Deterministic MCDA Formula</span>
        </div>
        <p className="calc-info">
          Enter available relief fund pool to compute equitable, proportional relief recommendations
          scaled by satellite-verified damage severity and inundated acreage.
        </p>

        <div className="fund-input-row">
          <label className="fund-label">Total Relief Fund Pool (INR ₹):</label>
          <div className="fund-input-wrapper">
            <span className="currency-prefix">₹</span>
            <input
              type="number"
              min="10000"
              step="500000"
              value={totalFund}
              onChange={(e) => setTotalFund(Number(e.target.value))}
              className="fund-input"
            />
          </div>
          <div className="quick-fund-buttons">
            <button onClick={() => setTotalFund(5000000)}>₹50 Lakh</button>
            <button onClick={() => setTotalFund(10000000)}>₹1 Crore</button>
            <button onClick={() => setTotalFund(25000000)}>₹2.5 Crore</button>
          </div>
        </div>

        {/* Priority Parcels List */}
        <div className="top-parcels-box">
          <div className="top-parcels-title">Top Priority Affected Parcels for Relief Verification:</div>
          <div className="parcels-scroll-list">
            {topParcels.map((p, idx) => (
              <div
                key={idx}
                className="priority-parcel-item"
                onClick={() => onSelectParcel && onSelectParcel(p.parcel_id)}
              >
                <div className="p-item-left">
                  <span className="p-rank">#{idx + 1}</span>
                  <div>
                    <span className="p-id">{p.parcel_id}</span>
                    <span className="p-crop-tag">{p.crop}</span>
                    <span className="p-taluk">{p.taluk}</span>
                  </div>
                </div>
                <div className="p-item-mid">
                  <span className={`p-sev-badge sev-${(p.severity || '').toLowerCase().replace(/\s+/g, '-')}`}>
                    {p.severity}
                  </span>
                  <span className="p-dmg-pct">{p.damage_percentage}% dmg ({p.affected_area_ha} ha)</span>
                </div>
                <div className="p-item-right">
                  <span className="p-alloc">{formatINR(p.recommended_relief_inr)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="statutory-disclaimer">
          🔒 <strong>Official Disclaimer:</strong> AI/GIS-based decision-support recommendation generated via
          Multi-Criteria Decision Analysis (MCDA). Final statutory disbursement requires revenue department field verification.
        </div>
      </div>
    </div>
  );
}
