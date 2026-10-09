import React, { useState, useEffect } from 'react';

export default function TemporalComparisonModal({ isOpen, onClose, onOpenChat }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('comparison'); // 'comparison' | 'suggestions'

  useEffect(() => {
    if (!isOpen) return;
    async function fetchTemporal() {
      try {
        setLoading(true);
        const res = await fetch('/api/temporal-comparison');
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error('Error loading temporal data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTemporal();
  }, [isOpen]);

  if (!isOpen) return null;

  const p1 = data?.period_1 || {};
  const p2 = data?.period_2 || {};
  const deltas = data?.deltas || {};
  const suggestions = data?.ai_suggestions || [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-card-wide" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-badge" style={{ background: '#eff6ff', color: '#2563eb' }}>
                SENTINEL-2 MULTI-TEMPORAL
              </span>
              <h2 className="modal-title">Bi-Seasonal Crop Comparison & AI Agronomic Advisory</h2>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '3px' }}>
              Comparing {p1.short_name || 'Baseline Observation'} vs {p2.short_name || 'Peak Observation'} across Ambasamudram & Cheranmahadevi
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <a
              href="/api/reports/download-pdf"
              download="VIT_MAPATHON_Agricultural_Cadastral_Report.pdf"
              className="btn-primary"
              style={{ textDecoration: 'none', background: '#0284c7' }}
              title="Download Formal PDF Assessment Report"
            >
              📄 Download PDF Report
            </a>
            <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
          </div>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="modal-tabs-bar">
          <button
            className={`modal-tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
            onClick={() => setActiveTab('comparison')}
          >
            📊 Multi-Temporal Comparison Matrix
          </button>
          <button
            className={`modal-tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`}
            onClick={() => setActiveTab('suggestions')}
          >
            💡 AI Agronomic Suggestions for Next Season ({suggestions.length})
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
              <div style={{ fontSize: '2rem', animation: 'spin 2s infinite linear' }}>🛰️</div>
              <div style={{ marginTop: '0.5rem', fontWeight: 600 }}>Loading Multi-Temporal Sentinel-2 Stacks...</div>
            </div>
          ) : activeTab === 'comparison' ? (
            <>
              {/* Season Headers Banner */}
              <div className="temporal-periods-grid">
                <div className="temporal-period-card period-card-1">
                  <div className="period-badge">PERIOD 1 (BASELINE)</div>
                  <div className="period-name">{p1.name}</div>
                  <div className="period-sub">
                    <span>🗓️ {p1.timeframe}</span> • <span>💧 {p1.moisture_status}</span>
                  </div>
                  <p className="period-desc">{p1.description}</p>
                </div>

                <div className="temporal-period-card period-card-2">
                  <div className="period-badge" style={{ background: '#dcfce7', color: '#15803d', borderColor: '#bbf7d0' }}>
                    PERIOD 2 (ACTIVE HARVEST)
                  </div>
                  <div className="period-name">{p2.name}</div>
                  <div className="period-sub">
                    <span>🗓️ {p2.timeframe}</span> • <span>🌊 {p2.moisture_status}</span>
                  </div>
                  <p className="period-desc">{p2.description}</p>
                </div>
              </div>

              {/* Side-by-Side Comparison Metrics Table */}
              <div style={{ marginTop: '1.25rem' }}>
                <h3 style={{ fontSize: '0.9rem', color: '#0f172a', fontWeight: 700, marginBottom: '0.6rem' }}>
                  📐 Crop Acreage & Spectral Index Dynamics
                </h3>
                <table className="table-custom">
                  <thead>
                    <tr>
                      <th style={{ width: '28%' }}>Agronomic & Remote Sensing Metric</th>
                      <th style={{ width: '22%' }}>{p1.short_name || 'Period 1 (Baseline)'}</th>
                      <th style={{ width: '22%' }}>{p2.short_name || 'Period 2 (Peak)'}</th>
                      <th style={{ width: '14%' }}>Net Shift (Δ)</th>
                      <th style={{ width: '14%' }}>Observation</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#166534' }}>🌾 Paddy Cultivated Area</td>
                      <td>{p1.paddy_area_ha ?? '--'} ha ({p1.paddy_parcels ?? '--'} parcels)</td>
                      <td>{p2.paddy_area_ha ?? '--'} ha ({p2.paddy_parcels ?? '--'} parcels)</td>
                      <td>
                        <span className="delta-chip-positive">
                          {deltas.paddy_area_ha_delta > 0 ? `+${deltas.paddy_area_ha_delta}` : deltas.paddy_area_ha_delta} ha ({deltas.paddy_pct_delta > 0 ? `+${deltas.paddy_pct_delta}` : deltas.paddy_pct_delta}%)
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Monsoon expansion</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#854d0e' }}>🍌 Banana Plantation Area</td>
                      <td>{p1.banana_area_ha ?? '--'} ha ({p1.banana_parcels ?? '--'} parcels)</td>
                      <td>{p2.banana_area_ha ?? '--'} ha ({p2.banana_parcels ?? '--'} parcels)</td>
                      <td>
                        <span className="delta-chip-neutral">
                          {deltas.banana_area_ha_delta > 0 ? `+${deltas.banana_area_ha_delta}` : deltas.banana_area_ha_delta} ha ({deltas.banana_pct_delta > 0 ? `+${deltas.banana_pct_delta}` : deltas.banana_pct_delta}%)
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Perennial stability</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#6b21a8' }}>🍂 Fallow & Other Plots</td>
                      <td>{p1.other_area_ha ?? '--'} ha ({p1.other_parcels ?? '--'} parcels)</td>
                      <td>{p2.other_area_ha ?? '--'} ha ({p2.other_parcels ?? '--'} parcels)</td>
                      <td>
                        <span className="delta-chip-positive" style={{ background: '#fef3c7', color: '#b45309', borderColor: '#fde68a' }}>
                          {deltas.other_area_ha_delta > 0 ? `+${deltas.other_area_ha_delta}` : deltas.other_area_ha_delta} ha ({deltas.other_pct_delta > 0 ? `+${deltas.other_pct_delta}` : deltas.other_pct_delta}%)
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Converted to wetland</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#0f172a' }}>📈 Mean Vegetation Vigor (NDVI)</td>
                      <td>{p1.mean_ndvi ?? '--'} {p1.vegetation_stage ? `(${p1.vegetation_stage})` : ''}</td>
                      <td>{p2.mean_ndvi ?? '--'} {p2.vegetation_stage ? `(${p2.vegetation_stage})` : ''}</td>
                      <td>
                        <span className="delta-chip-positive">
                          {deltas.ndvi_pct_delta > 0 ? `+${deltas.ndvi_pct_delta}` : deltas.ndvi_pct_delta}%
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Peak canopy growth</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#0284c7' }}>💧 Canopy Water Moisture (NDWI)</td>
                      <td>{p1.mean_ndwi ?? '--'}</td>
                      <td>{p2.mean_ndwi ?? '--'}</td>
                      <td>
                        <span className="delta-chip-positive" style={{ background: '#e0f2fe', color: '#0284c7', borderColor: '#bae6fd' }}>
                          {deltas.ndwi_pct_delta > 0 ? `+${deltas.ndwi_pct_delta}` : deltas.ndwi_pct_delta}%
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Canal recharge</td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600, color: '#475569' }}>🌱 Soil-Adjusted Index (SAVI)</td>
                      <td>{p1.mean_savi ?? '--'}</td>
                      <td>{p2.mean_savi ?? '--'}</td>
                      <td>
                        <span className="delta-chip-positive">
                          {deltas.savi_pct_delta > 0 ? `+${deltas.savi_pct_delta}` : deltas.savi_pct_delta}%
                        </span>
                      </td>
                      <td style={{ fontSize: '0.72rem', color: '#64748b' }}>Dense soil coverage</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Key Insights Box */}
              <div className="insights-box">
                <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '6px', fontSize: '0.85rem' }}>
                  🔍 Sentinel-2 Geospatial Findings
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.78rem', color: '#334155', lineHeight: 1.6 }}>
                  {data?.key_insights?.map((insight, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{insight}</li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            /* AI Suggestions Tab */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ padding: '0.75rem 1rem', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', fontSize: '0.8rem', color: '#1e40af' }}>
                💡 <strong>Target Season: Navarai / Summer 2026</strong> — Recommended agronomic interventions derived from Sentinel-2 temporal trajectory and soil conditions in the Thamirabarani basin.
              </div>

              <div className="suggestions-grid">
                {suggestions.map((s, idx) => (
                  <div key={s.id || idx} className="suggestion-card">
                    <div className="suggestion-header">
                      <span className="suggestion-cat">{s.category}</span>
                      <span className="suggestion-num">#{idx + 1}</span>
                    </div>
                    <h4 className="suggestion-title">{s.title}</h4>
                    <div className="suggestion-action">
                      <strong>Action Plan:</strong> {s.action}
                    </div>
                    <div className="suggestion-impact">
                      <strong>Expected Agronomic Impact:</strong> {s.impact}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: '0.75rem', textAlign: 'center', padding: '1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <p style={{ fontSize: '0.8rem', color: '#475569', marginBottom: '8px' }}>
                  Have specific field or plot questions? Consult the Agri-AI Assistant.
                </p>
                <button
                  className="btn-primary"
                  onClick={() => {
                    onClose();
                    if (onOpenChat) onOpenChat();
                  }}
                  style={{ margin: '0 auto' }}
                >
                  💬 Open Agri-AI Chatbot Assistant
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
