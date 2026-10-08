import React from 'react';

export const getCropColor = (crop) => {
  switch (crop?.toLowerCase()) {
    case 'paddy':
      return { fill: '#22c55e', stroke: '#14532d', text: '#4ade80', bg: 'rgba(34, 197, 94, 0.25)' };
    case 'banana':
      return { fill: '#facc15', stroke: '#854d0e', text: '#fde047', bg: 'rgba(250, 204, 21, 0.25)' };
    default:
      return { fill: '#c084fc', stroke: '#581c87', text: '#e9d5ff', bg: 'rgba(192, 132, 252, 0.25)' };
  }
};

export const createParcelPopupContent = (props) => {
  const crop = props.predicted_crop || 'Unknown';
  const colors = getCropColor(crop);
  const confPct = ((props.confidence || 0) * 100).toFixed(1);
  const pPaddy = ((props.prob_paddy || 0) * 100).toFixed(1);
  const pBanana = ((props.prob_banana || 0) * 100).toFixed(1);
  const pOther = ((props.prob_other || 0) * 100).toFixed(1);

  const village = props.village || 'Ambasamudram Field';
  const taluk = props.taluk || 'Ambasamudram Taluk';
  const district = props.district || 'Tirunelveli District';
  const state = props.state || 'Tamil Nadu';

  const ha = (props.area_ha || 0).toFixed(2);
  const acres = ((props.area_ha || 0) * 2.47105).toFixed(2);
  const sqkm = (props.area_sq_km || 0).toFixed(4);

  return `
    <div class="parcel-popup-card">
      <div class="popup-location-tag">
        📍 <strong>${village}</strong>, ${taluk}
        <div style="font-size: 0.65rem; color: #94a3b8;">${district}, ${state}</div>
      </div>

      <div class="popup-header">
        <span class="popup-id">${props.parcel_id || 'Parcel'}</span>
        <span class="popup-crop-badge" style="background: ${colors.fill}; color: #ffffff; box-shadow: 0 0 10px ${colors.fill}66;">
          ${crop}
        </span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Model Confidence:</span>
        <span class="popup-metric-value" style="color: ${colors.text}; font-weight: 700;">${confPct}%</span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Parcel Area:</span>
        <span class="popup-metric-value">${ha} ha <span style="font-size: 0.65rem; color: #94a3b8;">(${acres} acres)</span></span>
      </div>

      <div class="popup-metric-row">
        <span class="popup-metric-label">Spatial Area:</span>
        <span class="popup-metric-value">${sqkm} km²</span>
      </div>
      
      <div class="prob-container">
        <div style="font-size: 0.65rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 3px;">
          S-2 Random Forest Probabilities:
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #22c55e;">Paddy</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pPaddy}%; background: #16a34a;"></div>
          </div>
          <span style="font-family: var(--font-mono);">${pPaddy}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #facc15;">Banana</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pBanana}%; background: #eab308;"></div>
          </div>
          <span style="font-family: var(--font-mono);">${pBanana}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #94a3b8;">Other</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pOther}%; background: #64748b;"></div>
          </div>
          <span style="font-family: var(--font-mono);">${pOther}%</span>
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

  const village = props.village || 'Ambasamudram Rural';
  const taluk = props.taluk || 'Ambasamudram Taluk';
  const district = props.district || 'Tirunelveli District';
  const state = props.state || 'Tamil Nadu';

  const ha = (props.area_ha || 0).toFixed(2);
  const acres = ((props.area_ha || 0) * 2.47105).toFixed(2);
  const sqkm = (props.area_sq_km || 0).toFixed(4);

  return (
    <div className="inspector-card">
      <div className="inspector-loc">
        <span className="loc-pin">📍</span>
        <div>
          <div className="loc-village">{village}</div>
          <div className="loc-admin">{taluk} • {district}, {state}</div>
        </div>
      </div>

      <div className="inspector-crop-row">
        <span className="inspector-id">{props.parcel_id}</span>
        <span className="inspector-badge" style={{ background: colors.fill, color: '#fff' }}>
          {crop}
        </span>
      </div>

      <div className="inspector-grid">
        <div className="inspector-box">
          <div className="inspector-lbl">Model Confidence</div>
          <div className="inspector-val" style={{ color: colors.text }}>
            {((props.confidence || 0) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="inspector-box">
          <div className="inspector-lbl">Area (Hectares)</div>
          <div className="inspector-val">{ha} <span style={{ fontSize: '0.7rem' }}>ha</span></div>
          <div className="inspector-sub">{acres} Acres</div>
        </div>
      </div>

      <div className="prob-container" style={{ marginTop: '0.75rem' }}>
        <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>
          Random Forest Class Probabilities
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#22c55e' }}>Paddy</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_paddy || 0) * 100}%`, background: '#16a34a' }} />
          </div>
          <span>{((props.prob_paddy || 0) * 100).toFixed(1)}%</span>
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#facc15' }}>Banana</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_banana || 0) * 100}%`, background: '#eab308' }} />
          </div>
          <span>{((props.prob_banana || 0) * 100).toFixed(1)}%</span>
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#94a3b8' }}>Other</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_other || 0) * 100}%`, background: '#64748b' }} />
          </div>
          <span>{((props.prob_other || 0) * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
