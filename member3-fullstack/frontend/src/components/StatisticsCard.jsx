import React from 'react';
import { getCropColor } from './ParcelPopup';

export default function StatisticsCard({ statistics, metrics }) {
  if (!statistics) {
    return (
      <div className="panel-card">
        <div className="panel-card-title">
          <span>📍 Study Area Geo-Analytics</span>
        </div>
        <div style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>
          No classified parcels available.
        </div>
      </div>
    );
  }

  const summary = statistics?.study_area_summary || {};
  const dist = statistics?.crop_distribution || {};
  const overallMetrics = metrics?.overall || {};

  const totalAreaHa = summary.total_study_area_hectares || (summary.total_study_area_sq_km ? summary.total_study_area_sq_km * 100 : 0);
  const totalAreaSqKm = summary.total_study_area_sq_km || (totalAreaHa / 100.0);
  const totalParcels = summary.total_parcels || 0;
  const meetsMinArea = summary.meets_min_area_requirement ?? (totalAreaSqKm >= 20.0);

  const accuracyPct = overallMetrics.accuracy != null ? (overallMetrics.accuracy * 100).toFixed(1) : null;
  const f1Pct = overallMetrics.f1_score_macro != null ? (overallMetrics.f1_score_macro * 100).toFixed(1) : null;
  const meanConfPct = summary.overall_mean_confidence != null ? (summary.overall_mean_confidence * 100).toFixed(1) : null;

  const cropEntries = Object.entries(dist);

  return (
    <div className="panel-card">
      <div className="panel-card-title">
        <span>📍 Study Area Geo-Analytics</span>
      </div>

      {/* Administrative Hierarchy Badge */}
      <div className="admin-hierarchy-box">
        <div className="hierarchy-row">
          <span className="h-lbl">State:</span>
          <span className="h-val">{summary.state || 'Tamil Nadu (தமிழ்நாடு)'}</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">District:</span>
          <span className="h-val">{summary.district || 'Tirunelveli District (திருநெல்வேலி)'}</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Taluks:</span>
          <span className="h-val highlight">{summary.study_area_taluks || 'Ambasamudram & Cheranmahadevi'}</span>
        </div>
        <div className="hierarchy-row">
          <span className="h-lbl">Water Basin:</span>
          <span className="h-val" style={{ color: '#00e5ff' }}>Thamirabarani River Basin</span>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="stat-grid" style={{ marginTop: '0.75rem' }}>
        <div className="stat-item">
          <div className="stat-label">Total Cadastral Area</div>
          <div className="stat-value">{totalAreaHa.toFixed(2)} <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>ha</span></div>
          <div className="stat-sub" style={{ color: meetsMinArea ? '#22c55e' : '#38bdf8' }}>
            {totalAreaSqKm.toFixed(2)} km² ({ (totalAreaHa * 2.47105).toFixed(1) } Acres)
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Total Parcels</div>
          <div className="stat-value">{totalParcels.toLocaleString()}</div>
          <div className="stat-sub">Audited Cadastral Units</div>
        </div>

        <div className="stat-item">
          <div className="stat-label">ML Model Accuracy</div>
          <div className="stat-value" style={{ color: '#38bdf8' }}>
            {accuracyPct != null ? `${accuracyPct}%` : '—'}
          </div>
          <div className="stat-sub">
            {f1Pct != null ? `F1: ${f1Pct}% Macro` : 'Evaluation Metrics'}
          </div>
        </div>

        <div className="stat-item">
          <div className="stat-label">Mean Confidence</div>
          <div className="stat-value" style={{ color: '#a855f7' }}>
            {meanConfPct != null ? `${meanConfPct}%` : '—'}
          </div>
          <div className="stat-sub">Sentinel-2 L2A</div>
        </div>
      </div>

      {/* Crop Distribution Progress Bar */}
      {cropEntries.length > 0 && (
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600 }}>Classification Area Share:</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>
              {cropEntries.map(([c, data]) => `${data.percentage_of_total_area}% ${c}`).join(' • ')}
            </span>
          </div>
          <div className="dist-bar-container">
            {cropEntries.map(([cropName, data]) => {
              const colors = getCropColor(cropName);
              return (
                <div
                  key={cropName}
                  className="dist-segment"
                  style={{ width: `${data.percentage_of_total_area}%`, background: colors.fill }}
                  title={`${cropName}: ${data.percentage_of_total_area}% (${data.area_hectares || 0} ha)`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Dynamic Breakdown Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '1rem' }}>
        {cropEntries.map(([cropName, data]) => {
          const colors = getCropColor(cropName);
          return (
            <div
              key={cropName}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.75rem',
                padding: '0.4rem 0.6rem',
                background: colors.bg,
                borderRadius: '6px',
                borderLeft: `3px solid ${colors.fill}`
              }}
            >
              <span style={{ fontWeight: 600, color: colors.text }}>
                {cropName === 'Paddy' ? '🌾 Paddy (Rice)' : cropName === 'Banana' ? '🍌 Banana (Plantation)' : `🏷️ ${cropName}`}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>
                {data.parcel_count} parcels ({data.area_hectares || 0} ha • {data.percentage_of_total_area || 0}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

