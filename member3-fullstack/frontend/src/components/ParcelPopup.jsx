import React from 'react';

export const getCropColor = (crop) => {
  switch (crop?.toLowerCase()) {
    case 'paddy':
      return { fill: '#2e7d32', stroke: '#1b5e20', text: '#4caf50' };
    case 'banana':
      return { fill: '#fbc02d', stroke: '#f57f17', text: '#fbc02d' };
    default:
      return { fill: '#78909c', stroke: '#455a64', text: '#90a4ae' };
  }
};

export const createParcelPopupContent = (props) => {
  const crop = props.predicted_crop || 'Unknown';
  const colors = getCropColor(crop);
  const confPct = ((props.confidence || 0) * 100).toFixed(1);
  const pPaddy = ((props.prob_paddy || 0) * 100).toFixed(1);
  const pBanana = ((props.prob_banana || 0) * 100).toFixed(1);
  const pOther = ((props.prob_other || 0) * 100).toFixed(1);

  return `
    <div class="parcel-popup-card">
      <div class="popup-header">
        <span class="popup-id">${props.parcel_id || 'Parcel'}</span>
        <span class="popup-crop-badge" style="background: ${colors.fill}; color: #fff;">
          ${crop}
        </span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Confidence:</span>
        <span class="popup-metric-value" style="color: ${colors.text};">${confPct}%</span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Area (Hectares):</span>
        <span class="popup-metric-value">${(props.area_ha || 0).toFixed(2)} ha</span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Area (Sq. Km):</span>
        <span class="popup-metric-value">${(props.area_sq_km || 0).toFixed(4)} km²</span>
      </div>
      
      <div class="prob-container">
        <div style="font-size: 0.65rem; color: #94a3b8; margin-bottom: 2px;">Model Probabilities:</div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #4caf50;">Paddy</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pPaddy}%; background: #2e7d32;"></div>
          </div>
          <span>${pPaddy}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #fbc02d;">Banana</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pBanana}%; background: #fbc02d;"></div>
          </div>
          <span>${pBanana}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #90a4ae;">Other</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pOther}%; background: #78909c;"></div>
          </div>
          <span>${pOther}%</span>
        </div>
      </div>
    </div>
  `;
};

export default function ParcelPopup({ parcel }) {
  if (!parcel) return null;
  const props = parcel.properties || {};
  const crop = props.predicted_crop || 'Unknown';
  const colors = getCropColor(crop);

  return (
    <div className="panel-card" style={{ marginTop: '0.75rem' }}>
      <div className="popup-header">
        <span className="popup-id">{props.parcel_id}</span>
        <span className="popup-crop-badge" style={{ background: colors.fill, color: '#fff' }}>
          {crop}
        </span>
      </div>
      <div className="popup-metric-row">
        <span className="popup-metric-label">Confidence:</span>
        <span className="popup-metric-value" style={{ color: colors.text }}>
          {((props.confidence || 0) * 100).toFixed(1)}%
        </span>
      </div>
      <div className="popup-metric-row">
        <span className="popup-metric-label">Area:</span>
        <span className="popup-metric-value">
          {(props.area_ha || 0).toFixed(2)} ha ({(props.area_sq_km || 0).toFixed(4)} km²)
        </span>
      </div>
    </div>
  );
}
