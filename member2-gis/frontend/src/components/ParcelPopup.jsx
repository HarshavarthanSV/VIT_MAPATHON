import React from 'react';

export const getCropColor = (crop) => {
  switch (crop?.toLowerCase()) {
    case 'paddy':
      return { fill: '#22c55e', stroke: '#ffffff', text: '#16a34a', badgeText: '#ffffff', bg: 'rgba(34, 197, 94, 0.15)' };
    case 'banana':
      return { fill: '#eab308', stroke: '#ffffff', text: '#ca8a04', badgeText: '#ffffff', bg: 'rgba(234, 179, 8, 0.15)' };
    case 'water':
      return { fill: '#0ea5e9', stroke: '#ffffff', text: '#0284c7', badgeText: '#ffffff', bg: 'rgba(14, 165, 233, 0.15)' };
    default:
      return { fill: '#ef4444', stroke: '#ffffff', text: '#dc2626', badgeText: '#ffffff', bg: 'rgba(239, 68, 68, 0.15)' };
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
        <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">${district}, ${state}</div>
      </div>

      <div class="popup-header">
        <span class="popup-id">${props.parcel_id || 'Parcel'}</span>
        <span class="popup-crop-badge" style="background: ${colors.fill}; color: ${colors.badgeText};">
          ${crop}
        </span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Model Confidence:</span>
        <span class="popup-metric-value" style="color: ${colors.text}; font-weight: 700;">${confPct}%</span>
      </div>
      
      <div class="popup-metric-row">
        <span class="popup-metric-label">Parcel Area:</span>
        <span class="popup-metric-value">${ha} ha <span style="font-size: 0.7rem; color: #64748b;">(${acres} acres)</span></span>
      </div>

      <div class="popup-metric-row">
        <span class="popup-metric-label">Spatial Area:</span>
        <span class="popup-metric-value">${sqkm} km²</span>
      </div>
      
      <div class="prob-container" style="margin-top: 8px;">
        <div style="font-size: 0.68rem; color: #475569; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">
          Sentinel-2 RF Probabilities:
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #15803d; font-weight: 600;">Paddy</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pPaddy}%; background: #16a34a;"></div>
          </div>
          <span style="font-family: var(--font-mono); font-weight: 600; color: #0f172a;">${pPaddy}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #854d0e; font-weight: 600;">Banana</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pBanana}%; background: #eab308;"></div>
          </div>
          <span style="font-family: var(--font-mono); font-weight: 600; color: #0f172a;">${pBanana}%</span>
        </div>
        <div class="prob-row">
          <span class="prob-crop-name" style="color: #6b21a8; font-weight: 600;">Other</span>
          <div class="prob-track">
            <div class="prob-fill" style="width: ${pOther}%; background: #9333ea;"></div>
          </div>
          <span style="font-family: var(--font-mono); font-weight: 600; color: #0f172a;">${pOther}%</span>
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
        <div style={{ fontSize: '0.7rem', color: '#475569', fontWeight: 700, marginBottom: '4px' }}>
          {props.model_name ? `${props.model_name.replace(/_/g, ' ')} Class Probabilities` : 'ML Class Probabilities'}
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#15803d' }}>Paddy</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_paddy || 0) * 100}%`, background: '#16a34a' }} />
          </div>
          <span style={{ fontWeight: 600, color: '#0f172a' }}>{((props.prob_paddy || 0) * 100).toFixed(1)}%</span>
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#854d0e' }}>Banana</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_banana || 0) * 100}%`, background: '#eab308' }} />
          </div>
          <span style={{ fontWeight: 600, color: '#0f172a' }}>{((props.prob_banana || 0) * 100).toFixed(1)}%</span>
        </div>
        <div className="prob-row">
          <span className="prob-crop-name" style={{ color: '#6b21a8' }}>Other</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_other || 0) * 100}%`, background: '#9333ea' }} />
          </div>
          <span style={{ fontWeight: 600, color: '#0f172a' }}>{((props.prob_other || 0) * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
