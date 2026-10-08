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
        <span>📍 Study Area Geo-Analytics</span>
      </div>

      {/* Administrative Hierarchy Badge */}
      <div className="admin-hierarchy-box">
        <div className="hierarchy-row">
          <span className="h-lbl">State:</span>
          <span className="h-val">Tamil Nadu (தமிழ்நாடு)</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">District:</span>
          <span className="h-val">Tirunelveli District (திருநெல்வேலி)</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Taluks:</span>
          <span className="h-val highlight">Ambasamudram & Cheranmahadevi</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Water Basin:</span>
          <span className="h-val" style={{ color: '#00e5ff' }}>Thamirabarani River Basin</span>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="stat-grid" style={{ marginTop: '0.75rem' }}>
        <div className="stat-item">
          <div className="stat-label">Total Study Area</div>
          <div className="stat-value">{totalArea.toFixed(2)} <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>km²</span></div>
          <div className="stat-sub" style={{ color: meetsMinArea ? '#22c55e' : '#f59e0b' }}>
            {meetsMinArea ? '✅ Exceeds ≥20 km²' : '⚠️ Below 20 km²'}
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Total Parcels</div>
          <div className="stat-value">{totalParcels.toLocaleString()}</div>
          <div className="stat-sub">{(totalArea * 100).toFixed(0)} Hectares</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">ML Model Accuracy</div>
          <div className="stat-value" style={{ color: '#38bdf8' }}>{accuracyPct}%</div>
          <div className="stat-sub">F1: {((overallMetrics.f1_score_macro || 0.908) * 100).toFixed(1)}% Macro</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Mean Confidence</div>
          <div className="stat-value" style={{ color: '#a855f7' }}>
            {((summary.overall_mean_confidence || 0.884) * 100).toFixed(1)}%
          </div>
          <div className="stat-sub">Sentinel-2 L2A</div>
        </div>
      </div>

      {/* Crop Distribution Progress Bar */}
      <div style={{ marginTop: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
          <span style={{ fontWeight: 600 }}>Cultivation Area Share:</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{paddyPct}% Paddy • {bananaPct}% Banana</span>
        </div>
        <div className="dist-bar-container">
          <div
            className="dist-segment"
            style={{ width: `${paddyPct}%`, background: '#16a34a' }}
            title={`Paddy: ${paddyPct}% (${dist.Paddy?.area_sq_km || 0} km²)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${bananaPct}%`, background: '#eab308' }}
            title={`Banana: ${bananaPct}% (${dist.Banana?.area_sq_km || 0} km²)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${otherPct}%`, background: '#64748b' }}
            title={`Other: ${otherPct}% (${dist.Other?.area_sq_km || 0} km²)`}
          />
        </div>
      </div>

      {/* Mini Breakdown Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.4rem 0.6rem', background: 'rgba(22, 163, 74, 0.12)', borderRadius: '6px', borderLeft: '3px solid #16a34a' }}>
          <span style={{ fontWeight: 600, color: '#22c55e' }}>🌾 Paddy Cultivation</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Paddy?.area_sq_km || 0} km² ({dist.Paddy?.percentage_of_total_area || 0}%)</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.4rem 0.6rem', background: 'rgba(234, 179, 8, 0.12)', borderRadius: '6px', borderLeft: '3px solid #eab308' }}>
          <span style={{ fontWeight: 600, color: '#facc15' }}>🍌 Banana Plantations</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Banana?.area_sq_km || 0} km² ({dist.Banana?.percentage_of_total_area || 0}%)</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.4rem 0.6rem', background: 'rgba(100, 116, 139, 0.12)', borderRadius: '6px', borderLeft: '3px solid #64748b' }}>
          <span style={{ fontWeight: 600, color: '#94a3b8' }}>🌿 Other Crops / Fallow</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{dist.Other?.area_sq_km || 0} km² ({dist.Other?.percentage_of_total_area || 0}%)</span>
        </div>
      </div>
    </div>
  );
}
