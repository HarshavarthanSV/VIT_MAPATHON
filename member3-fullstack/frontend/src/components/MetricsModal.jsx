import React from 'react';

export default function MetricsModal({ isOpen, onClose, metrics, featureImportance }) {
  if (!isOpen) return null;

  const overall = metrics?.overall || {};
  const perClass = metrics?.per_class || {};

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <h2 className="modal-title">🤖 Random Forest Model Evaluation & Performance</h2>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Spatial Evaluation on Unseen Test Parcels (GroupShuffleSplit by Parcel ID)
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Key Metrics Overview */}
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="stat-item">
              <div className="stat-label">Overall Accuracy</div>
              <div className="stat-value" style={{ color: '#22c55e' }}>
                {overall.accuracy != null ? `${(overall.accuracy * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Precision (Weighted)</div>
              <div className="stat-value" style={{ color: '#38bdf8' }}>
                {overall.precision_weighted != null ? `${(overall.precision_weighted * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Recall (Weighted)</div>
              <div className="stat-value" style={{ color: '#f59e0b' }}>
                {overall.recall_weighted != null ? `${(overall.recall_weighted * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">F1-Score (Weighted)</div>
              <div className="stat-value" style={{ color: '#ec4899' }}>
                {overall.f1_score_weighted != null ? `${(overall.f1_score_weighted * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
          </div>


          {/* Per-class Metrics Table */}
          <div>
            <h3 style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.5rem' }}>
              Per-Class Classification Report
            </h3>
            <table className="table-custom">
              <thead>
                <tr>
                  <th>Crop Class</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1-Score</th>
                  <th>Test Support</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(perClass).map(([className, vals]) => (
                  <tr key={className}>
                    <td style={{ fontWeight: 600, color: className === 'Paddy' ? '#4caf50' : className === 'Banana' ? '#fbc02d' : '#90a4ae' }}>
                      {className}
                    </td>
                    <td>{((vals.precision || 0) * 100).toFixed(2)}%</td>
                    <td>{((vals.recall || 0) * 100).toFixed(2)}%</td>
                    <td>{((vals.f1_score || 0) * 100).toFixed(2)}%</td>
                    <td>{vals.support || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Evaluation Plots from Member 1 */}
          <div>
            <h3 style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.5rem' }}>
              Model Visualizations (Member 1 Outputs)
            </h3>
            <div className="modal-images-grid">
              <div className="modal-image-box">
                <img
                  src="/static/confusion_matrix.png"
                  alt="Confusion Matrix Heatmap"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="modal-image-label">Confusion Matrix Heatmap (Spatial Test Split)</div>
              </div>
              <div className="modal-image-box">
                <img
                  src="/static/feature_importance.png"
                  alt="Feature Importance Bar Chart"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="modal-image-label">Spectral & Temporal Feature Importance Rankings</div>
              </div>
            </div>
          </div>

          {/* Top Features Breakdown */}
          {featureImportance && (
            <div>
              <h3 style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.5rem' }}>
                Spectral Bands & Indices Importance Ranking
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
                {Object.entries(featureImportance)
                  .sort((a, b) => b[1] - a[1])
                  .map(([feat, score]) => (
                    <div
                      key={feat}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.4rem 0.6rem',
                        background: 'rgba(15, 23, 42, 0.5)',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '6px',
                        fontSize: '0.75rem'
                      }}
                    >
                      <span style={{ fontFamily: 'var(--font-mono)', color: feat.includes('NDVI') ? '#4caf50' : feat.includes('NDWI') ? '#38bdf8' : '#f8fafc' }}>
                        {feat}
                      </span>
                      <span style={{ fontWeight: 600, color: '#38bdf8' }}>
                        {(score * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
