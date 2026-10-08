import React from 'react';
import { getCropColor } from './ParcelPopup';

export default function FilterPanel({
  visibleCrops,
  onToggleCrop,
  selectedTaluk,
  onSelectTaluk,
  minConfidence,
  onChangeConfidence,
  statistics,
  displayedCount,
  totalCount,
  onResetFilters
}) {
  const cropDist = statistics?.crop_distribution || {};
  const cropKeys = Object.keys(cropDist).length > 0
    ? Object.keys(cropDist)
    : Object.keys(visibleCrops || {});

  return (
    <div className="panel-card">
      <div className="panel-card-title">
        <span>⚙️ Crop & Spatial Filters</span>
      </div>

      {/* Taluk Filter Tabs */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: 600 }}>
          Study Area Taluk:
        </div>
        <div className="taluk-tabs-row">
          <button
            className={`taluk-tab-btn ${selectedTaluk === 'all' ? 'active' : ''}`}
            onClick={() => onSelectTaluk('all')}
          >
            Both Taluks
          </button>
          <button
            className={`taluk-tab-btn ${selectedTaluk.toLowerCase().includes('ambasamudram') ? 'active' : ''}`}
            onClick={() => onSelectTaluk('Ambasamudram')}
          >
            Ambasamudram
          </button>
          <button
            className={`taluk-tab-btn ${selectedTaluk.toLowerCase().includes('cheranmahadevi') ? 'active' : ''}`}
            onClick={() => onSelectTaluk('Cheranmahadevi')}
          >
            Cheranmahadevi
          </button>
        </div>
      </div>

      {/* Crop Checkboxes */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>Crop Categories:</span>
          <span className="count-pill">{displayedCount} / {totalCount} Parcels</span>
        </div>

        <div className="crop-filters-list">
          {cropKeys.map((cropName) => {
            const isVisible = visibleCrops[cropName] !== false;
            const colors = getCropColor(cropName);
            const distInfo = cropDist[cropName] || {};
            const subtitle = cropName === 'Paddy'
              ? 'River floodplains & canal tracts'
              : cropName === 'Banana'
              ? 'Perennial horticulture tracts'
              : cropName === 'Non-Crop'
              ? 'Bare soil, settlements, waterbodies'
              : 'Agricultural / Other land cover';

            return (
              <div
                key={cropName}
                className="crop-filter-row"
                style={{
                  borderColor: isVisible ? colors.stroke : 'rgba(255, 255, 255, 0.08)',
                  background: isVisible ? colors.bg : 'rgba(15, 23, 42, 0.4)'
                }}
                onClick={() => onToggleCrop(cropName)}
              >
                <div className="crop-filter-left">
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={() => onToggleCrop(cropName)}
                    onClick={(e) => e.stopPropagation()}
                    style={{ accentColor: colors.fill, cursor: 'pointer' }}
                  />
                  <span className="crop-color-pill" style={{ background: colors.fill }} />
                  <div>
                    <span className="crop-name" style={{ color: colors.text }}>
                      {cropName === 'Paddy' ? 'Paddy (நெல்)' : cropName === 'Banana' ? 'Banana (வாழை)' : cropName}
                    </span>
                    <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{subtitle}</div>
                  </div>
                </div>
                <div className="crop-stats-mini">
                  {distInfo.parcel_count != null ? `${distInfo.parcel_count} parcels` : ''}
                  <div style={{ color: colors.text }}>
                    {distInfo.area_hectares != null ? `${distInfo.area_hectares} ha` : ''}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confidence Slider */}
      <div className="slider-container" style={{ marginBottom: '1.25rem' }}>
        <div className="slider-header">
          <span style={{ fontWeight: 600 }}>Minimum Confidence Threshold:</span>
          <strong style={{ color: '#38bdf8' }}>{Math.round(minConfidence * 100)}%</strong>
        </div>
        <input
          type="range"
          min="0.0"
          max="1.0"
          step="0.05"
          value={minConfidence}
          onChange={(e) => onChangeConfidence(parseFloat(e.target.value))}
          className="slider-input"
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#64748b' }}>
          <span>0% (All Parcels)</span>
          <span>50%</span>
          <span>95% (High Precision)</span>
        </div>
      </div>

      {/* Reset Action */}
      <button
        onClick={onResetFilters}
        className="reset-btn"
      >
        🔄 Reset All Filters to Default
      </button>
    </div>
  );
}

