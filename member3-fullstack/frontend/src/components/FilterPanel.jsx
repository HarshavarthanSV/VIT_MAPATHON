import React from 'react';

export default function FilterPanel({
  visibleCrops,
  onToggleCrop,
  selectedTaluk,
  onSelectTaluk,
  minConfidence,
  onChangeConfidence,
  activeBasemap,
  onChangeBasemap,
  showPlaces,
  onChangeShowPlaces,
  showInfra,
  onChangeShowInfra,
  showLabels,
  onChangeShowLabels,
  statistics,
  displayedCount,
  totalCount,
  onResetFilters
}) {
  const cropDist = statistics?.crop_distribution || {};

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
            className={`taluk-tab-btn ${selectedTaluk.startsWith('Ambasamudram') ? 'active' : ''}`}
            onClick={() => onSelectTaluk('Ambasamudram')}
          >
            Ambasamudram
          </button>
          <button
            className={`taluk-tab-btn ${selectedTaluk.startsWith('Cheranmahadevi') ? 'active' : ''}`}
            onClick={() => onSelectTaluk('Cheranmahadevi')}
          >
            Cheranmahadevi
          </button>
        </div>
      </div>

      {/* Basemap Selection in Sidebar */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: 600 }}>
          🗺️ Satellite & Basemap Layers:
        </div>
        <div className="basemap-pills-row">
          <button
            className={`map-pill-btn ${activeBasemap === 'satellite' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('satellite')}
            title="Esri Satellite Imagery"
          >
            🛰️ Satellite
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'voyager' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('voyager')}
            title="CartoDB Street Map"
          >
            🗺️ Street
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'dark' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('dark')}
            title="Dark Theme GIS"
          >
            🌙 Dark
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'topo' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('topo')}
            title="Topographic Elevation"
          >
            ⛰️ Topo
          </button>
        </div>
      </div>

      {/* Overlays Toggles in Sidebar */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: 600 }}>
          GIS Feature Overlays:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          <label className="toggle-chk-label" style={{ fontSize: '0.75rem' }}>
            <input
              type="checkbox"
              checked={showInfra}
              onChange={(e) => onChangeShowInfra(e.target.checked)}
            />
            <span>🌊 Thamirabarani River & Highways</span>
          </label>
          <label className="toggle-chk-label" style={{ fontSize: '0.75rem' }}>
            <input
              type="checkbox"
              checked={showPlaces}
              onChange={(e) => onChangeShowPlaces(e.target.checked)}
            />
            <span>📍 Town & Village Markers</span>
          </label>
          {activeBasemap === 'satellite' && (
            <label className="toggle-chk-label" style={{ fontSize: '0.75rem' }}>
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => onChangeShowLabels(e.target.checked)}
              />
              <span>🏷️ Place & Street Labels</span>
            </label>
          )}
        </div>
      </div>

      {/* Crop Checkboxes */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>Crop Categories:</span>
          <span className="count-pill">{displayedCount} / {totalCount} Parcels</span>
        </div>

        <div className="crop-filters-list">
          {/* Paddy */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Paddy ? '#16a34a' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Paddy ? 'rgba(22, 163, 74, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Paddy')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Paddy}
                onChange={() => onToggleCrop('Paddy')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#16a34a', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#16a34a' }} />
              <div>
                <span className="crop-name" style={{ color: '#4ade80' }}>Paddy (நெல்)</span>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Irrigated wetland crop</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Paddy?.parcel_count || 0} parcels
              <div style={{ color: '#4ade80' }}>{cropDist.Paddy?.area_hectares || 0} ha</div>
            </div>
          </div>

          {/* Banana */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Banana ? '#eab308' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Banana ? 'rgba(234, 179, 8, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Banana')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Banana}
                onChange={() => onToggleCrop('Banana')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#eab308', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#eab308' }} />
              <div>
                <span className="crop-name" style={{ color: '#facc15' }}>Banana (வாழை)</span>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Perennial horticulture tracts</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Banana?.parcel_count || 0} parcels
              <div style={{ color: '#facc15' }}>{cropDist.Banana?.area_hectares || 0} ha</div>
            </div>
          </div>

          {/* Other */}
          <div
            className="crop-filter-row"
            style={{
              borderColor: visibleCrops.Other ? '#64748b' : 'rgba(255, 255, 255, 0.08)',
              background: visibleCrops.Other ? 'rgba(100, 116, 139, 0.15)' : 'rgba(15, 23, 42, 0.4)'
            }}
            onClick={() => onToggleCrop('Other')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Other}
                onChange={() => onToggleCrop('Other')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#64748b', cursor: 'pointer' }}
              />
              <span className="crop-color-pill" style={{ background: '#64748b' }} />
              <div>
                <span className="crop-name" style={{ color: '#94a3b8' }}>Other Crops / Fallow</span>
                <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Dry crops, scrub, borders</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              {cropDist.Other?.parcel_count || 0} parcels
              <div style={{ color: '#94a3b8' }}>{cropDist.Other?.area_hectares || 0} ha</div>
            </div>
          </div>
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
