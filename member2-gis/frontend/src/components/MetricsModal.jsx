import React from 'react';

export default function MetricsModal({ isOpen, onClose, metrics, featureImportance }) {
  if (!isOpen) return null;

  const overall = metrics?.overall || {};
  const perClass = metrics?.per_class || {};

  const accText = overall.test_accuracy != null ? `${(overall.test_accuracy * 100).toFixed(1)}%` : '--';
  const precText = overall.test_precision_macro != null ? `${(overall.test_precision_macro * 100).toFixed(1)}%` : '--';
  const recText = overall.test_recall_macro != null ? `${(overall.test_recall_macro * 100).toFixed(1)}%` : '--';
  const f1Text = overall.test_f1_macro != null ? `${(overall.test_f1_macro * 100).toFixed(1)}%` : '--';
  const cvText = overall.cv_5fold_accuracy_mean != null ? `${(overall.cv_5fold_accuracy_mean * 100).toFixed(1)}%` : '--';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <h2 className="modal-title">
              {metrics?.model_name ? `${metrics.model_name.replace(/_/g, ' ')} Performance & Evaluation` : 'ML Model Performance & Evaluation'}
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
              Spatial GroupShuffleSplit Evaluation (Zero parcel leakage across training/test splits)
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Key Metrics Overview */}
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
            <div className="stat-item">
              <div className="stat-label">Test Accuracy</div>
              <div className="stat-value" style={{ color: '#16a34a' }}>{accText}</div>
              <div className="stat-sub">Unseen test split</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Macro F1-Score</div>
              <div className="stat-value" style={{ color: '#2563eb' }}>{f1Text}</div>
              <div className="stat-sub">Unweighted mean</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Macro Precision</div>
              <div className="stat-value" style={{ color: '#0891b2' }}>{precText}</div>
              <div className="stat-sub">Across 3 classes</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Macro Recall</div>
              <div className="stat-value" style={{ color: '#d97706' }}>{recText}</div>
              <div className="stat-sub">Detection rate</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">5-Fold Spatial CV</div>
              <div className="stat-value" style={{ color: '#7c3aed' }}>{cvText}</div>
              <div className="stat-sub">Parcel grouped</div>
            </div>
          </div>

          {/* Per-class Metrics Table */}
          <div style={{ marginTop: '1.25rem' }}>
            <h3 style={{ fontSize: '0.9rem', color: '#0f172a', fontWeight: 600, marginBottom: '0.5rem' }}>
              Per-Class Classification Report
            </h3>
            <table className="table-custom">
              <thead>
                <tr>
                  <th>Crop Class</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1-Score</th>
                  <th>Test Samples</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(perClass).map(([className, vals]) => (
                  <tr key={className}>
                    <td style={{ fontWeight: 600, color: className === 'Paddy' ? '#16a34a' : className === 'Banana' ? '#d97706' : '#9333ea' }}>
                      {className}
                    </td>
                    <td>{vals.precision != null ? `${(vals.precision * 100).toFixed(1)}%` : '--'}</td>
                    <td>{vals.recall != null ? `${(vals.recall * 100).toFixed(1)}%` : '--'}</td>
                    <td>{vals.f1_score != null ? `${(vals.f1_score * 100).toFixed(1)}%` : '--'}</td>
                    <td style={{ fontWeight: 600 }}>{vals.support ?? '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Evaluation Plots from Member 1 */}
          <div style={{ marginTop: '1.25rem' }}>
            <h3 style={{ fontSize: '0.9rem', color: '#0f172a', fontWeight: 600, marginBottom: '0.5rem' }}>
              Model Diagnostic Visualizations
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
                <div className="modal-image-label">Top Spectral Band & Index Features Importance</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
