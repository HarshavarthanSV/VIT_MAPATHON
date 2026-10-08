import React from 'react';

export default function StatisticsCard({ statistics, metrics, selectedTaluk, talukAcreage }) {
  const summary = statistics?.study_area_summary || null;
  const dist = statistics?.crop_distribution || {};
  const overallMetrics = metrics?.overall || null;

  const totalStudyAreaKm2 = summary?.total_study_area_sq_km;
  const totalParcels = summary?.total_parcels ?? 0;
  const parcelAreaHa = summary?.total_parcels_area_hectares ?? 0;
  const parcelAreaAcres = summary?.total_parcels_area_acres ?? 0;
  const meetsMinArea = totalStudyAreaKm2 ? totalStudyAreaKm2 >= 20.0 : true;

  // Real ML metrics from trained Random Forest model (model_metrics.json)
  const accuracyText = overallMetrics?.test_accuracy != null
    ? `${(overallMetrics.test_accuracy * 100).toFixed(1)}%`
    : '--';

  const f1MacroText = overallMetrics?.test_f1_macro != null
    ? `${(overallMetrics.test_f1_macro * 100).toFixed(1)}% Macro`
    : '--';

  // Mean confidence computed dynamically from active parcels
  const meanConfText = summary?.overall_mean_confidence != null && summary?.total_parcels > 0
    ? `${(summary.overall_mean_confidence * 100).toFixed(1)}%`
    : '--';

  const paddy = dist?.Paddy || {};
  const banana = dist?.Banana || {};
  const other = dist?.Other || {};

  const paddyPct = paddy.percentage_of_total_area || 0;
  const bananaPct = banana.percentage_of_total_area || 0;
  const otherPct = other.percentage_of_total_area || 0;

  // Active Taluk name label
  let activeTalukDisplay = 'Ambasamudram & Cheranmahadevi';
  if (selectedTaluk && selectedTaluk.toLowerCase().includes('ambasamudram')) {
    activeTalukDisplay = 'Ambasamudram Taluk';
  } else if (selectedTaluk && selectedTaluk.toLowerCase().includes('cheranmahadevi')) {
    activeTalukDisplay = 'Cheranmahadevi Taluk';
  }

  return (
    <div className="panel-card">
      <div className="panel-card-title">
        <span className="panel-title-text">📍 Study Area Geo-Analytics</span>
        <span className="status-chip-live">LIVE ML</span>
      </div>

      {/* Administrative Hierarchy Box */}
      <div className="admin-hierarchy-box">
        <div className="hierarchy-row">
          <span className="h-lbl">State:</span>
          <span className="h-val">Tamil Nadu</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">District:</span>
          <span className="h-val">Tirunelveli District</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Taluk Division:</span>
          <span className="h-val highlight">{activeTalukDisplay}</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Hydrology:</span>
          <span className="h-val" style={{ color: '#0284c7' }}>Thamirabarani Basin</span>
        </div>
      </div>

      {/* KPI Stat Cards Grid */}
      <div className="stat-grid">
        <div className="stat-item">
          <div className="stat-label">Total Study Area</div>
          <div className="stat-value">
            {totalStudyAreaKm2 != null ? totalStudyAreaKm2.toFixed(2) : '--'}
            <span className="stat-unit"> km²</span>
          </div>
          <div className="stat-sub" style={{ color: meetsMinArea ? '#16a34a' : '#d97706' }}>
            {meetsMinArea ? '✅ Exceeds ≥20 km²' : '⚠️ Below 20 km²'}
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Classified Parcels</div>
          <div className="stat-value" style={{ color: '#0f172a' }}>
            {totalParcels.toLocaleString()}
          </div>
          <div className="stat-sub">
            {parcelAreaHa > 0 ? `${parcelAreaHa.toFixed(1)} ha (${parcelAreaAcres.toFixed(1)} ac)` : '0 ha'}
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">ML Model Accuracy</div>
          <div className="stat-value" style={{ color: '#2563eb' }}>
            {accuracyText}
          </div>
          <div className="stat-sub">F1: {f1MacroText}</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Mean Confidence</div>
          <div className="stat-value" style={{ color: '#7c3aed' }}>
            {meanConfText}
          </div>
          <div className="stat-sub">Sentinel-2 L2A</div>
        </div>
      </div>

      {/* Cultivation Area Share Progress Bar */}
      <div style={{ marginTop: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#475569', marginBottom: '6px' }}>
          <span style={{ fontWeight: 600 }}>Cultivation Area Share:</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0f172a' }}>
            {paddyPct}% Paddy • {bananaPct}% Banana
          </span>
        </div>
        <div className="dist-bar-container">
          <div
            className="dist-segment"
            style={{ width: `${paddyPct}%`, background: '#16a34a' }}
            title={`Paddy: ${paddyPct}% (${paddy.area_hectares || 0} ha)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${bananaPct}%`, background: '#eab308' }}
            title={`Banana: ${bananaPct}% (${banana.area_hectares || 0} ha)`}
          />
          <div
            className="dist-segment"
            style={{ width: `${otherPct}%`, background: '#9333ea' }}
            title={`Other: ${otherPct}% (${other.area_hectares || 0} ha)`}
          />
        </div>
      </div>

      {/* Mini Breakdown Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginTop: '1rem' }}>
        <div className="crop-stat-pill crop-stat-paddy">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="crop-dot" style={{ background: '#16a34a' }} />
            <span style={{ fontWeight: 600, color: '#166534' }}>Paddy (நெல்)</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#14532d' }}>
            {paddy.area_hectares ? `${paddy.area_hectares} ha (${paddy.parcel_count} parcels)` : '0 ha'} • {paddyPct}%
          </span>
        </div>

        <div className="crop-stat-pill crop-stat-banana">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="crop-dot" style={{ background: '#eab308' }} />
            <span style={{ fontWeight: 600, color: '#854d0e' }}>Banana (வாழை)</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#713f12' }}>
            {banana.area_hectares ? `${banana.area_hectares} ha (${banana.parcel_count} parcels)` : '0 ha'} • {bananaPct}%
          </span>
        </div>

        <div className="crop-stat-pill crop-stat-other">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="crop-dot" style={{ background: '#9333ea' }} />
            <span style={{ fontWeight: 600, color: '#6b21a8' }}>Other Crops / Fallow</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#581c87' }}>
            {other.area_hectares ? `${other.area_hectares} ha (${other.parcel_count} parcels)` : '0 ha'} • {otherPct}%
          </span>
        </div>
      </div>
    </div>
  );
}
