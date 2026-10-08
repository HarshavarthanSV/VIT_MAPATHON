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
        <span className="panel-title-text">⚙️ Spatial & Crop Filters</span>
      </div>

      {/* Taluk Filter Tabs */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div className="filter-section-label">
          Administrative Division:
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
        <div className="filter-section-label">
          Satellite & Basemap Layers:
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
            title="CartoDB Voyager Street Map"
          >
            🗺️ Street
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'dark' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('dark')}
            title="CartoDB Dark Matter GIS"
          >
            🌙 Dark
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'topo' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('topo')}
            title="Topographic Elevation Map"
          >
            ⛰️ Topo
          </button>
        </div>
      </div>

      {/* Overlays Toggles */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div className="filter-section-label">
          Vector Overlays:
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <label className="toggle-chk-label">
            <input
              type="checkbox"
              checked={showInfra}
              onChange={(e) => onChangeShowInfra(e.target.checked)}
            />
            <span>🌊 Thamirabarani River & Roads</span>
          </label>
          <label className="toggle-chk-label">
            <input
              type="checkbox"
              checked={showPlaces}
              onChange={(e) => onChangeShowPlaces(e.target.checked)}
            />
            <span>📍 Town & Village Markers</span>
          </label>
          {activeBasemap === 'satellite' && (
            <label className="toggle-chk-label">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => onChangeShowLabels(e.target.checked)}
              />
              <span>🏷️ Street & Place Name Labels</span>
            </label>
          )}
        </div>
      </div>

      {/* Crop Categories Checkboxes */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span className="filter-section-label" style={{ marginBottom: 0 }}>Target Crops:</span>
          <span className="count-pill">{displayedCount} / {totalCount} Parcels</span>
        </div>

        <div className="crop-filters-list">
          {/* Paddy */}
          <div
            className={`crop-filter-row ${visibleCrops.Paddy ? 'selected-paddy' : ''}`}
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
              <span className="crop-color-indicator" style={{ background: '#16a34a' }} />
              <div>
                <span className="crop-name" style={{ color: '#166534', fontWeight: 600 }}>Paddy (நெல்)</span>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Wetland irrigated crop</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{cropDist.Paddy?.parcel_count ?? 0} parcels</div>
              <div style={{ color: '#16a34a', fontWeight: 600 }}>{cropDist.Paddy?.area_hectares ?? 0} ha</div>
            </div>
          </div>

          {/* Banana */}
          <div
            className={`crop-filter-row ${visibleCrops.Banana ? 'selected-banana' : ''}`}
            onClick={() => onToggleCrop('Banana')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Banana}
                onChange={() => onToggleCrop('Banana')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#d97706', cursor: 'pointer' }}
              />
              <span className="crop-color-indicator" style={{ background: '#eab308' }} />
              <div>
                <span className="crop-name" style={{ color: '#854d0e', fontWeight: 600 }}>Banana (வாழை)</span>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Perennial horticulture</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{cropDist.Banana?.parcel_count ?? 0} parcels</div>
              <div style={{ color: '#b45309', fontWeight: 600 }}>{cropDist.Banana?.area_hectares ?? 0} ha</div>
            </div>
          </div>

          {/* Other */}
          <div
            className={`crop-filter-row ${visibleCrops.Other ? 'selected-other' : ''}`}
            onClick={() => onToggleCrop('Other')}
          >
            <div className="crop-filter-left">
              <input
                type="checkbox"
                checked={visibleCrops.Other}
                onChange={() => onToggleCrop('Other')}
                onClick={(e) => e.stopPropagation()}
                style={{ accentColor: '#9333ea', cursor: 'pointer' }}
              />
              <span className="crop-color-indicator" style={{ background: '#9333ea' }} />
              <div>
                <span className="crop-name" style={{ color: '#6b21a8', fontWeight: 600 }}>Other Crops / Fallow</span>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Dry crops, fallow, scrub</div>
              </div>
            </div>
            <div className="crop-stats-mini">
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{cropDist.Other?.parcel_count ?? 0} parcels</div>
              <div style={{ color: '#7e22ce', fontWeight: 600 }}>{cropDist.Other?.area_hectares ?? 0} ha</div>
            </div>
          </div>
        </div>
      </div>

      {/* Confidence Slider */}
      <div className="slider-container" style={{ marginBottom: '1.25rem' }}>
        <div className="slider-header">
          <span style={{ fontWeight: 600, fontSize: '0.75rem', color: '#334155' }}>Minimum Model Confidence:</span>
          <strong style={{ color: '#2563eb', fontSize: '0.85rem' }}>{Math.round(minConfidence * 100)}%</strong>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#64748b', marginTop: '2px' }}>
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
        🔄 Reset Filters to Default
      </button>
    </div>
  );
}
