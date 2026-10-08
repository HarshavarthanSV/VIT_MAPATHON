import React from 'react';

export const getCropColor = (crop) => {
  switch (crop?.toLowerCase()) {
    case 'paddy':
      return { fill: '#16a34a', stroke: '#15803d', text: '#22c55e', bg: 'rgba(22, 163, 74, 0.2)' };
    case 'banana':
      return { fill: '#eab308', stroke: '#ca8a04', text: '#facc15', bg: 'rgba(234, 179, 8, 0.2)' };
    case 'non-crop':
    case 'other':
      return { fill: '#64748b', stroke: '#475569', text: '#94a3b8', bg: 'rgba(100, 116, 139, 0.2)' };
    case 'water':
      return { fill: '#0284c7', stroke: '#0369a1', text: '#38bdf8', bg: 'rgba(2, 132, 199, 0.2)' };
    default:
      return { fill: '#64748b', stroke: '#475569', text: '#94a3b8', bg: 'rgba(100, 116, 139, 0.2)' };
  }
};

export const getSeverityColor = (severity) => {
  switch (severity) {
    case 'Severe Damage':
      return { fill: '#8e44ad', stroke: '#6c3483', text: '#d7bde2' };
    case 'High Damage':
      return { fill: '#e74c3c', stroke: '#c0392b', text: '#f5b7b1' };
    case 'Moderate Damage':
      return { fill: '#e67e22', stroke: '#d35400', text: '#f8c471' };
    case 'Low Damage':
      return { fill: '#f1c40f', stroke: '#d4ac0d', text: '#f9e79f' };
    default:
      return { fill: '#64748b', stroke: '#475569', text: '#94a3b8' };
  }
};

export const createParcelPopupContent = (props) => {
  const crop = props.predicted_crop || props.crop || 'Unknown';
  const colors = getCropColor(crop);
  const confPct = ((props.confidence || 0) * 100).toFixed(1);
  const pPaddy = ((props.prob_paddy || 0) * 100).toFixed(1);
  const pBanana = ((props.prob_banana || 0) * 100).toFixed(1);
  const pOther = ((props.prob_other || 0) * 100).toFixed(1);

  const village = props.village || 'Ambasamudram Field';
  const taluk = props.taluk || 'Ambasamudram Taluk';
  const district = props.district || 'Tirunelveli District';
  const state = props.state || 'Tamil Nadu';

  const ha = (props.area_ha || props.parcel_area_ha || 0).toFixed(2);
  const acres = ((props.area_ha || props.parcel_area_ha || 0) * 2.47105).toFixed(2);
  const sqkm = (props.area_sq_km || 0).toFixed(4);

  const hasHazard = props.affected_area_ha !== undefined;
  const affHa = (props.affected_area_ha || 0).toFixed(2);
  const dmgPct = (props.damage_percentage || 0).toFixed(1);
  const severity = props.severity || 'No Damage / Unaffected';
  const sevColor = getSeverityColor(severity);
  const relief = props.recommended_relief_inr ? `₹${Number(props.recommended_relief_inr).toLocaleString('en-IN')}` : null;

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

      ${hasHazard && (props.affected_area_ha > 0 || severity !== 'No Damage / Unaffected') ? `
        <div style="margin: 6px 0; padding: 6px; background: rgba(15, 23, 42, 0.8); border: 1px solid ${sevColor.stroke}; border-radius: 6px;">
          <div style="font-size: 0.65rem; font-weight: bold; color: ${sevColor.text}; text-transform: uppercase; margin-bottom: 2px;">
            ⚠️ Flood Inundation Damage:
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
            <span>Severity:</span>
            <strong style="color: ${sevColor.fill};">${severity}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
            <span>Inundated Area:</span>
            <span>${affHa} ha (${dmgPct}%)</span>
          </div>
          ${relief ? `
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; margin-top: 2px; color: #38bdf8;">
              <span>Rec. Relief (INR):</span>
              <strong>${relief}</strong>
            </div>
          ` : ''}
        </div>
      ` : ''}
      
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
          <span class="prob-crop-name" style="color: #94a3b8;">Non-Crop</span>
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
  const crop = props.predicted_crop || props.crop || 'Unknown';
  const colors = getCropColor(crop);

  const village = props.village || 'Ambasamudram Rural';
  const taluk = props.taluk || 'Ambasamudram Taluk';
  const district = props.district || 'Tirunelveli District';
  const state = props.state || 'Tamil Nadu';

  const ha = (props.area_ha || props.parcel_area_ha || 0).toFixed(2);
  const acres = ((props.area_ha || props.parcel_area_ha || 0) * 2.47105).toFixed(2);

  const affHa = (props.affected_area_ha || 0).toFixed(2);
  const dmgPct = (props.damage_percentage || 0).toFixed(1);
  const severity = props.severity || 'No Damage / Unaffected';
  const sevColor = getSeverityColor(severity);
  const relief = props.recommended_relief_inr ? `₹${Number(props.recommended_relief_inr).toLocaleString('en-IN')}` : null;

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

      {props.affected_area_ha > 0 && (
        <div className="inspector-box" style={{ marginTop: '0.5rem', background: 'rgba(15, 23, 42, 0.9)', border: `1px solid ${sevColor.stroke}` }}>
          <div className="inspector-lbl" style={{ color: sevColor.text }}>⚠️ Hazard Impact ({props.hazard_type || 'Flood'})</div>
          <div className="inspector-val" style={{ color: sevColor.fill, fontSize: '0.9rem' }}>{severity} ({dmgPct}%)</div>
          <div className="inspector-sub">Inundated: {affHa} ha {relief && `• Relief: ${relief}`}</div>
        </div>
      )}

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
          <span className="prob-crop-name" style={{ color: '#94a3b8' }}>Non-Crop</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${(props.prob_other || 0) * 100}%`, background: '#64748b' }} />
          </div>
          <span>{((props.prob_other || 0) * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
