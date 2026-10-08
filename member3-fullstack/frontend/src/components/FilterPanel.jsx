import React from 'react';

export default function FilterPanel({
  visibleCrops,
  onToggleCrop,
  minConfidence,
  onChangeConfidence,
  activeBasemap,
  onChangeBasemap,
  statistics,
  displayedCount,
  totalCount,
  onResetFilters
}) {
  const cropDist = statistics?.crop_distribution || {};

  return (
    <div className="panel-card">
      <div className="panel-card-title">
        <span>🗺️ Layer & Crop Filters</span>
      </div>

      {/* Basemap Selection */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
          Basemap Imagery:
        </div>
        <div className="basemap-switch">
          <button
            className={`basemap-btn ${activeBasemap === 'satellite' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('satellite')}
          >
            🛰️ Satellite (Esri)
          </button>
          <button
            className={`basemap-btn ${activeBasemap === 'street' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('street')}
          >
            🗺️ Street (OSM)
          </button>
        </div>
      </div>

      {/* Crop Checkboxes */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>Crop Layers:</span>
          <span>{displayedCount} / {totalCount} Parcels</span>
        </div>

        <div className="crop-filters-list">
          {/* Paddy */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Paddy ? '#2e7d32' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Paddy ? 'rgba(46, 125, 50, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Paddy')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Paddy}
                onChange={() => onToggleCrop('Paddy')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#2e7d32', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#2e7d32' }} />
              <span className="crop-name" style={{ color: '#4caf50' }}>Paddy</span>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Paddy?.parcel_count || 0} parcels ({cropDist.Paddy?.area_hectares || 0} ha)
            </div>
          </div>

          {/* Banana */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Banana ? '#fbc02d' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Banana ? 'rgba(251, 192, 45, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Banana')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Banana}
                onChange={() => onToggleCrop('Banana')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#fbc02d', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#fbc02d' }} />
              <span className="crop-name" style={{ color: '#fbc02d' }}>Banana</span>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Banana?.parcel_count || 0} parcels ({cropDist.Banana?.area_hectares || 0} ha)
            </div>
          </div>

          {/* Other */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Other ? '#78909c' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Other ? 'rgba(120, 144, 156, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Other')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Other}
                onChange={() => onToggleCrop('Other')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#78909c', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#78909c' }} />
              <span className="crop-name" style={{ color: '#90a4ae' }}>Other</span>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Other?.parcel_count || 0} parcels ({cropDist.Other?.area_hectares || 0} ha)
            </div>
          </div>
        </div>
      </div>

      {/* Confidence Slider */}
      <div className="slider-container" style={{ marginBottom: '1rem' }}>
        <div className="slider-header">
          <span>Minimum Confidence:</span>
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
          <span>0% (All)</span>
          <span>50%</span>
          <span>100% (Strict)</span>
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={onResetFilters}
        style={{
          width: '100%',
          padding: '0.45rem',
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '6px',
          color: '#cbd5e1',
          fontSize: '0.75rem',
          cursor: 'pointer'
        }}
      >
        🔄 Reset All Filters
      </button>
    </div>
  );
}
