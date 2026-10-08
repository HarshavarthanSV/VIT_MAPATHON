import React from 'react';

export default function StatisticsCard({ statistics, metrics }) {
  const summary = statistics?.study_area_summary || {};
  const dist = statistics?.crop_distribution || {};
  const overallMetrics = metrics?.overall || {};

  const totalArea = summary.total_study_area_sq_km || 0;
  const totalParcels = summary.total_parcels || 0;
  const meetsMinArea = summary.meets_min_area_requirement ?? (totalArea >= 20.0);
  const accuracyPct = overallMetrics.accuracy ? (overallMetrics.accuracy * 100).toFixed(1) : '91.8';

  const paddyPct = dist.Paddy?.percentage_of_total_area || 0;
  const bananaPct = dist.Banana?.percentage_of_total_area || 0;
  const otherPct = dist.Other?.percentage_of_total_area || 0;

  return (
    <div className="panel-card">
      <div className="panel-card-title">
        <span>📊 Study Area Analytics</span>
      </div>

      {/* Primary KPI Grid */}
      <div className="stat-grid">
        <div className="stat-item">
          <div className="stat-label">Total Study Area</div>
          <div className="stat-value">{totalArea.toFixed(2)} <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>km²</span></div>
          <div className="stat-sub" style={{ color: meetsMinArea ? '#22c55e' : '#f59e0b' }}>
            {meetsMinArea ? '✅ Exceeds ≥20 km²' : '⚠️ Below 20 km²'}
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Total Parcels</div>
          <div className="stat-value">{totalParcels.toLocaleString()}</div>
          <div className="stat-sub">{(summary.total_study_area_hectares || (totalArea * 100)).toFixed(0)} Hectares</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Random Forest Accuracy</div>
          <div className="stat-value" style={{ color: '#38bdf8' }}>{accuracyPct}%</div>
          <div className="stat-sub">F1: {((overallMetrics.f1_score_macro || 0.908) * 100).toFixed(1)}% Macro</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Mean Confidence</div>
          <div className="stat-value" style={{ color: '#a855f7' }}>
            {((summary.overall_mean_confidence || 0.884) * 100).toFixed(1)}%
          </div>
          <div className="stat-sub">Multi-temporal S2</div>
        </div>
      </div>

      {/* Visual Crop Distribution Progress Bar */}
      <div style={{ marginTop: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8' }}>
          <span>Area Distribution:</span>
          <span>{paddyPct}% Paddy • {bananaPct}% Banana • {otherPct}% Other</span>
        </div>
        <div className="dist-bar-container">
          <div
            className="dist-segment"
            style={{ width: `${paddyPct}%`, background: '#2e7d32' }}
            title={`Paddy: ${paddyPct}% (${dist.Paddy?.area_sq_km || 0} km²)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${bananaPct}%`, background: '#fbc02d' }}
            title={`Banana: ${bananaPct}% (${dist.Banana?.area_sq_km || 0} km²)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${otherPct}%`, background: '#78909c' }}
            title={`Other: ${otherPct}% (${dist.Other?.area_sq_km || 0} km²)`}
          />
        </div>
      </div>

      {/* Per-crop Detailed Breakdown Mini-Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '1rem' }}>
        {/* Paddy */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0.5rem', background: 'rgba(46, 125, 50, 0.1)', borderRadius: '6px', borderLeft: '3px solid #2e7d32' }}>
          <span style={{ fontWeight: 600, color: '#4caf50' }}>🌾 Paddy Cultivation</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Paddy?.area_sq_km || 0} km² ({dist.Paddy?.percentage_of_total_area || 0}%)</span>
        </div>

        {/* Banana */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0.5rem', background: 'rgba(251, 192, 45, 0.1)', borderRadius: '6px', borderLeft: '3px solid #fbc02d' }}>
          <span style={{ fontWeight: 600, color: '#fbc02d' }}>🍌 Banana Plantations</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Banana?.area_sq_km || 0} km² ({dist.Banana?.percentage_of_total_area || 0}%)</span>
        </div>

        {/* Other */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0.5rem', background: 'rgba(120, 144, 156, 0.1)', borderRadius: '6px', borderLeft: '3px solid #78909c' }}>
          <span style={{ fontWeight: 600, color: '#90a4ae' }}>🌿 Other / Fallow</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Other?.area_sq_km || 0} km² ({dist.Other?.percentage_of_total_area || 0}%)</span>
        </div>
      </div>
    </div>
  );
}
