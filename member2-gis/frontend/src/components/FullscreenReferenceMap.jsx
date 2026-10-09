import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';

export default function FullscreenReferenceMap({
  initialGeojson = null,
  initialInfra = null,
  onSwitchToDashboard = null,
  isFullscreen = true,
  selectedParcel: externalSelectedParcel = null,
  onSelectParcel = null,
  mapDisplayMode = 'crop',
  onDisplayModeChange = null
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const activeParcelLayerRef = useRef(null);
  const waterLayerRef = useRef(null);
  const satLayerRef = useRef(null);
  const roadsLayerRef = useRef(null);
  const placesLayerRef = useRef(null);
  const streetLayerRef = useRef(null);
  const measureLineRef = useRef(null);
  const cityMarkersLayerRef = useRef(null);

  // Datasets
  const [geojsonData, setGeojsonData] = useState(initialGeojson);
  const [infraData, setInfraData] = useState(initialInfra);

  // UI Interactive States
  const [currentMode, setCurrentMode] = useState('hybrid'); // 'satellite', 'hybrid', 'map', 'ndvi', 'evi', 'ndwi', 'lswi'
  const [showBoundaries, setShowBoundaries] = useState(true);
  const [showLayersPanel, setShowLayersPanel] = useState(true);
  const [measureActive, setMeasureActive] = useState(false);
  const [measureInfo, setMeasureInfo] = useState('');
  const measurePointsRef = useRef([]);

  const [visibleCrops, setVisibleCrops] = useState({
    Paddy: true,
    Banana: true,
    Other: true,
    Water: true,
    NonAgri: true
  });

  const [selectedParcel, setSelectedParcel] = useState(
    externalSelectedParcel || {
      parcel_id: 'Parcel P102',
      predicted_crop: 'Paddy',
      area_ha: 2.4,
      crop_health: 'Healthy (0.82)',
      mean_ndvi: 0.78,
      hazard: 'None'
    }
  );

  const [minimapBox, setMinimapBox] = useState({ x: 48, y: 28, w: 28, h: 24, cx: 62, cy: 40 });

  // 1. Fetch fallback static datasets if props not provided, and sync with parent props
  useEffect(() => {
    if (initialGeojson) {
      setGeojsonData(initialGeojson);
      if (!externalSelectedParcel) {
        const p102 = initialGeojson?.features?.find(f => {
          const pid = f.properties?.parcel_id || '';
          return pid === 'P102' || pid === 'PARCEL_0102' || pid.includes('102');
        }) || initialGeojson?.features?.[0];
        if (p102) setSelectedParcel(p102.properties);
      }
    } else if (!geojsonData) {
      fetch('/data/parcels.json')
        .then(r => r.json())
        .then(data => {
          setGeojsonData(data);
          const p102 = data?.features?.find(f => {
            const pid = f.properties?.parcel_id || '';
            return pid === 'P102' || pid === 'PARCEL_0102' || pid.includes('102');
          }) || data?.features?.[0];
          if (p102) setSelectedParcel(p102.properties);
        })
        .catch(err => console.error('Error fetching fallback parcels:', err));
    }
  }, [initialGeojson]);

  useEffect(() => {
    if (initialInfra) {
      setInfraData(initialInfra);
    } else if (!infraData) {
      fetch('/data/infrastructure.json')
        .then(r => r.json())
        .then(data => setInfraData(data))
        .catch(err => console.error('Error fetching fallback infra:', err));
    }
  }, [initialInfra]);

  useEffect(() => {
    if (externalSelectedParcel) {
      setSelectedParcel(externalSelectedParcel);
    }
  }, [externalSelectedParcel]);

  // 2. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [8.692, 77.488],
      zoom: 12.5,
      zoomControl: false,
      attributionControl: false,
      preferCanvas: false
    });

    mapInstanceRef.current = map;

    // Custom Panes
    map.createPane('waterPane').style.zIndex = '450';
    map.createPane('parcelsPane').style.zIndex = '500';
    map.createPane('labelsPane').style.zIndex = '600';

    // Base Tile Layers
    const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    });
    satLayerRef.current = satLayer;

    const roadsLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      pane: 'labelsPane'
    });
    roadsLayerRef.current = roadsLayer;

    const placesLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      pane: 'labelsPane'
    });
    placesLayerRef.current = placesLayer;

    const streetLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    });
    streetLayerRef.current = streetLayer;

    // Default to Hybrid
    satLayer.addTo(map);
    roadsLayer.addTo(map);
    placesLayer.addTo(map);

    // City Callout Badges Layer
    const cityLayer = L.layerGroup().addTo(map);
    cityMarkersLayerRef.current = cityLayer;
    cityLayer.clearLayers();

    const addCityPin = (name, prefix, lat, lon) => {
      const icon = L.divIcon({
        className: 'city-pin-marker-container',
        html: `
          <div class="city-badge">
            <div class="city-badge-sub">${prefix}</div>
            <div class="city-badge-main">${name}</div>
          </div>
          <div class="city-pointer-icon">📍</div>
        `,
        iconSize: [160, 54],
        iconAnchor: [80, 52]
      });

      const marker = L.marker([lat, lon], { icon, zIndexOffset: 1000 }).addTo(cityLayer);
      marker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        map.flyTo([lat, lon], 13.5, { duration: 0.8 });
      });
    };

    // Authentic Geography:
    // City A: Ambasamudram (West) at [8.704, 77.448]
    // City B: Cheranmahadevi (East) at [8.704, 77.525]
    addCityPin('Ambasamudram', 'City A', 8.704, 77.448);
    addCityPin('Cheranmahadevi', 'City B', 8.704, 77.525);

    // Minimap sync listener
    const updateMinimap = () => {
      const b = map.getBounds();
      const minLon = 77.41, maxLon = 77.57;
      const minLat = 8.64, maxLat = 8.75;

      const normW = Math.max(0, Math.min(1, (b.getWest() - minLon) / (maxLon - minLon)));
      const normE = Math.max(0, Math.min(1, (b.getEast() - minLon) / (maxLon - minLon)));
      const normN = Math.max(0, Math.min(1, (b.getNorth() - minLat) / (maxLat - minLat)));
      const normS = Math.max(0, Math.min(1, (b.getSouth() - minLat) / (maxLat - minLat)));

      const x = Math.max(5, Math.min(85, normW * 100));
      const y = Math.max(5, Math.min(65, (1 - normN) * 80));
      const w = Math.max(16, Math.min(60, (normE - normW) * 100));
      const h = Math.max(12, Math.min(50, (normN - normS) * 80));

      setMinimapBox({ x, y, w, h, cx: x + w / 2, cy: y + h / 2 });
    };

    map.on('move', updateMinimap);

    // Click listener for measurement tool
    map.on('click', (e) => {
      if (!measurePointsRef.current.isMeasuring) return;
      const pts = measurePointsRef.current.points;
      pts.push(e.latlng);

      if (measureLineRef.current) map.removeLayer(measureLineRef.current);
      measureLineRef.current = L.polyline(pts, { color: '#38bdf8', weight: 3, dashArray: '6, 6' }).addTo(map);

      let totalDist = 0;
      for (let i = 0; i < pts.length - 1; i++) {
        totalDist += pts[i].distanceTo(pts[i + 1]);
      }
      const distStr = totalDist > 1000 ? (totalDist / 1000).toFixed(2) + ' km' : Math.round(totalDist) + ' m';
      setMeasureInfo(`Measured: ${distStr} (${pts.length} points)`);
    });

    map.on('dblclick', () => {
      if (!measurePointsRef.current.isMeasuring) return;
      stopMeasurement();
    });

    // Invalidate size on mount and container resize
    const ro = new ResizeObserver(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });

    if (mapContainerRef.current) {
      ro.observe(mapContainerRef.current);
    }

    const t1 = setTimeout(() => {
      if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
    }, 150);

    const t2 = setTimeout(() => {
      if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
    }, 450);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      ro.disconnect();
      if (cityMarkersLayerRef.current) {
        cityMarkersLayerRef.current.clearLayers();
        cityMarkersLayerRef.current = null;
      }
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 3. Render Infrastructure / River Ribbon
  useEffect(() => {
    if (!mapInstanceRef.current || !infraData) return;
    const map = mapInstanceRef.current;

    if (waterLayerRef.current) {
      map.removeLayer(waterLayerRef.current);
      waterLayerRef.current = null;
    }

    if (!visibleCrops.Water) return;

    const riverFeatures = {
      type: 'FeatureCollection',
      features: (infraData.features || []).filter(f => f.properties?.category === 'waterway')
    };

    const waterLayer = L.geoJSON(riverFeatures, {
      pane: 'waterPane',
      style: (feature) => {
        const type = feature.properties?.type;
        const isMainRiver = type === 'river';
        return {
          color: isMainRiver ? '#0284c7' : '#38bdf8',
          weight: isMainRiver ? 1.8 : 1.15,
          opacity: isMainRiver ? 0.92 : 0.80,
          lineCap: 'round',
          lineJoin: 'round'
        };
      },
      onEachFeature: (f, l) => {
        const name = f.properties?.name || 'Thamirabarani River';
        const typeLabel = f.properties?.type === 'river' ? 'Main River Channel' : (f.properties?.type === 'canal' ? 'Irrigation Canal' : 'Stream');
        l.bindTooltip(`<strong>🌊 ${name}</strong><br/><span style="font-size:11px; color:#94a3b8;">${typeLabel}</span>`, {
          sticky: true,
          className: 'custom-map-tooltip'
        });
      }
    }).addTo(map);

    waterLayerRef.current = waterLayer;
  }, [infraData, visibleCrops.Water]);

  // 4. Render Classified Agricultural Parcels
  useEffect(() => {
    if (!mapInstanceRef.current || !geojsonData) return;
    const map = mapInstanceRef.current;

    if (activeParcelLayerRef.current) {
      map.removeLayer(activeParcelLayerRef.current);
      activeParcelLayerRef.current = null;
    }

    const parcelStyle = (feature) => {
      const p = feature.properties || {};
      const crop = p.predicted_crop || 'Other';

      let fillColor = '#ef4444';
      if (currentMode === 'ndvi') {
        const ndvi = p.mean_ndvi || 0.7;
        fillColor = ndvi >= 0.78 ? '#15803d' : ndvi >= 0.70 ? '#22c55e' : ndvi >= 0.60 ? '#84cc16' : '#eab308';
      } else if (currentMode === 'evi') {
        const evi = p.mean_evi || 0.55;
        fillColor = evi >= 0.60 ? '#059669' : evi >= 0.48 ? '#10b981' : evi >= 0.38 ? '#34d399' : '#f59e0b';
      } else if (currentMode === 'ndwi') {
        const ndwi = p.mean_ndwi || 0.05;
        fillColor = ndwi >= 0.10 ? '#0284c7' : ndwi >= 0.0 ? '#38bdf8' : '#64748b';
      } else if (currentMode === 'lswi') {
        const lswi = p.mean_lswi || 0.4;
        fillColor = lswi >= 0.45 ? '#0369a1' : lswi >= 0.30 ? '#0ea5e9' : '#94a3b8';
      } else if (mapDisplayMode === 'health') {
        const ndvi = p.mean_ndvi || 0.7;
        fillColor = ndvi >= 0.75 ? '#22c55e' : ndvi >= 0.60 ? '#eab308' : '#ef4444';
      } else if (mapDisplayMode === 'hazard') {
        const haz = String(p.hazard || '').toLowerCase();
        fillColor = haz.includes('flood') ? '#0284c7' : haz.includes('pest') ? '#dc2626' : '#22c55e';
      } else {
        if (crop === 'Paddy') fillColor = '#22c55e';
        else if (crop === 'Banana') fillColor = '#eab308';
        else fillColor = '#ef4444';
      }

      const isSelected = selectedParcel && (
        selectedParcel.parcel_id === p.parcel_id ||
        (p.parcel_id && selectedParcel.parcel_id && (
          p.parcel_id.replace('PARCEL_0', 'P').replace('PARCEL_', 'P') === String(selectedParcel.parcel_id).replace('Parcel ', '').trim()
        ))
      );

      return {
        pane: 'parcelsPane',
        fillColor: fillColor,
        fillOpacity: isSelected ? 0.95 : 0.72,
        color: isSelected ? '#38bdf8' : '#ffffff',
        weight: isSelected ? 3.0 : (showBoundaries ? 1.35 : 0),
        opacity: showBoundaries ? 0.92 : 0
      };
    };

    const parcelLayer = L.geoJSON(geojsonData, {
      filter: (feature) => {
        const crop = feature.properties?.predicted_crop;
        if (crop === 'Paddy' && !visibleCrops.Paddy) return false;
        if (crop === 'Banana' && !visibleCrops.Banana) return false;
        if (crop === 'Other' && !visibleCrops.Other) return false;
        return true;
      },
      style: parcelStyle,
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {};
        const area = p.area_ha ? p.area_ha.toFixed(1) : '2.4';
        const conf = Math.round((p.confidence || 0.9) * 100);

        layer.bindTooltip(
          `<strong>${p.parcel_id}</strong><br/>Crop: ${p.predicted_crop}<br/>Area: ${area} ha • Conf: ${conf}%`,
          { sticky: true, className: 'custom-map-tooltip' }
        );

        layer.on({
          mouseover: (e) => {
            if (!selectedParcel || selectedParcel.parcel_id !== p.parcel_id) {
              e.target.setStyle({ weight: 2.8, color: '#ffffff', fillOpacity: 0.90 });
              e.target.bringToFront();
            }
          },
          mouseout: (e) => {
            if (!selectedParcel || selectedParcel.parcel_id !== p.parcel_id) {
              parcelLayer.resetStyle(e.target);
            }
          },
          click: (e) => {
            setSelectedParcel(p);
            if (onSelectParcel) {
              onSelectParcel(p);
            }
            L.DomEvent.stopPropagation(e);
          }
        });
      }
    }).addTo(map);

    activeParcelLayerRef.current = parcelLayer;
  }, [geojsonData, visibleCrops, showBoundaries, currentMode, mapDisplayMode, selectedParcel]);

  // 5. Basemap & Index Layer Switching
  const handleSelectMode = (mode) => {
    setCurrentMode(mode);
    const map = mapInstanceRef.current;
    if (!map) return;

    const sat = satLayerRef.current;
    const roads = roadsLayerRef.current;
    const places = placesLayerRef.current;
    const street = streetLayerRef.current;

    if (map.hasLayer(sat)) map.removeLayer(sat);
    if (map.hasLayer(roads)) map.removeLayer(roads);
    if (map.hasLayer(places)) map.removeLayer(places);
    if (map.hasLayer(street)) map.removeLayer(street);

    if (mode === 'satellite') {
      sat.addTo(map);
    } else if (mode === 'hybrid') {
      sat.addTo(map);
      roads.addTo(map);
      places.addTo(map);
    } else if (mode === 'map') {
      street.addTo(map);
    } else {
      // Spectral indices: keep hybrid satellite base underneath
      sat.addTo(map);
      roads.addTo(map);
      places.addTo(map);
    }
  };

  // 6. Action Handlers
  const handleZoomIn = () => mapInstanceRef.current?.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current?.zoomOut();

  const handleFitParcels = () => {
    const map = mapInstanceRef.current;
    const layer = activeParcelLayerRef.current;
    if (map && layer && layer.getLayers().length > 0) {
      map.fitBounds(layer.getBounds(), { padding: [40, 40] });
    } else if (map) {
      map.setView([8.692, 77.488], 12.5);
    }
  };

  const toggleCrop = (crop) => {
    setVisibleCrops(prev => ({ ...prev, [crop]: !prev[crop] }));
  };

  const toggleMeasure = () => {
    const next = !measureActive;
    setMeasureActive(next);
    measurePointsRef.current = { isMeasuring: next, points: [] };

    const map = mapInstanceRef.current;
    if (map) {
      map.getContainer().style.cursor = next ? 'crosshair' : '';
      if (!next && measureLineRef.current) {
        map.removeLayer(measureLineRef.current);
        measureLineRef.current = null;
      }
    }

    if (next) {
      setMeasureInfo('Click on map to measure distance. Double click to finish.');
    } else {
      setMeasureInfo('');
    }
  };

  const stopMeasurement = () => {
    setMeasureActive(false);
    measurePointsRef.current = { isMeasuring: false, points: [] };
    const map = mapInstanceRef.current;
    if (map) {
      map.getContainer().style.cursor = '';
      if (measureLineRef.current) {
        map.removeLayer(measureLineRef.current);
        measureLineRef.current = null;
      }
    }
    setMeasureInfo('');
  };

  return (
    <div className={isFullscreen ? "ref-map-fullscreen-wrapper" : "ref-map-dashboard-wrapper"}>
      {/* Leaflet Map Canvas */}
      <div ref={mapContainerRef} className="ref-map-canvas" />

      {/* Prominent Top Switch to Analytical View Button (only in fullscreen mode) */}
      {isFullscreen && onSwitchToDashboard && (
        <button
          onClick={onSwitchToDashboard}
          className="top-switch-analytics-btn"
          title="Switch to Interactive Analytical Dashboard"
        >
          <span className="btn-icon">📊</span>
          <span>Analytics View</span>
        </button>
      )}

      {/* Top Legend Bar */}
      <div className="top-legend-pill">
        <div
          className={`legend-item ${visibleCrops.Paddy ? '' : 'dimmed'}`}
          onClick={() => toggleCrop('Paddy')}
        >
          <span className="legend-dot dot-paddy" />
          <span>Paddy</span>
        </div>
        <div
          className={`legend-item ${visibleCrops.Banana ? '' : 'dimmed'}`}
          onClick={() => toggleCrop('Banana')}
        >
          <span className="legend-dot dot-banana" />
          <span>Banana</span>
        </div>
        <div
          className={`legend-item ${visibleCrops.Other ? '' : 'dimmed'}`}
          onClick={() => toggleCrop('Other')}
        >
          <span className="legend-dot dot-other" />
          <span>Other Crops</span>
        </div>
        <div
          className={`legend-item ${visibleCrops.Water ? '' : 'dimmed'}`}
          onClick={() => toggleCrop('Water')}
        >
          <span className="legend-dot dot-water" />
          <span>Water</span>
        </div>
        <div
          className={`legend-item ${visibleCrops.NonAgri ? '' : 'dimmed'}`}
          onClick={() => toggleCrop('NonAgri')}
        >
          <span className="legend-dot dot-nonagri" />
          <span>Non-Agricultural</span>
        </div>

        <div className="legend-divider" />

        <label className="boundary-toggle-wrapper">
          <input
            type="checkbox"
            className="boundary-checkbox"
            checked={showBoundaries}
            onChange={(e) => setShowBoundaries(e.target.checked)}
          />
          <span>Parcel Boundaries</span>
        </label>
      </div>

      {/* Left Floating Toolbar */}
      <div className="left-floating-bar">
        <button className="map-btn" onClick={handleZoomIn} title="Zoom In">+</button>
        <button className="map-btn" onClick={handleZoomOut} title="Zoom Out">−</button>
        <button className="map-btn" onClick={handleFitParcels} title="Center Study Parcels">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>
        </button>
        <button
          className={`map-btn ${showLayersPanel ? '' : 'active'}`}
          onClick={() => setShowLayersPanel(!showLayersPanel)}
          title="Toggle Layers"
        >
          <svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
        </button>
        <button
          className={`map-btn ${measureActive ? 'active' : ''}`}
          onClick={toggleMeasure}
          title="Measure Distance & Area"
        >
          <svg viewBox="0 0 24 24"><path d="M2 22L22 2"/><path d="M5 19l2 2"/><path d="M8 16l3 3"/><path d="M12 12l2 2"/><path d="M15 9l3 3"/><path d="M18 6l2 2"/></svg>
        </button>
      </div>

      {/* Live Measurement Badge */}
      {measureActive && (
        <div className="measure-badge" style={{ display: 'block' }}>
          {measureInfo}
        </div>
      )}

      {/* Bottom-Left Scale Bar */}
      <div className="bottom-scale-bar">
        <div className="scale-ticks-row">
          <span>0</span>
          <span>2</span>
          <span>4 km</span>
        </div>
        <div className="scale-line-container" />
      </div>

      {/* Top-Right Overview Minimap Inset */}
      <div className="top-right-minimap" onClick={handleFitParcels} title="Overview: Tirunelveli District">
        <svg viewBox="0 0 100 80" className="minimap-svg">
          <path d="M 18 12 Q 52 4 82 16 Q 94 44 84 70 Q 50 82 22 66 Q 10 40 18 12 Z" fill="#e0f2fe" stroke="#0284c7" strokeWidth="1.5" />
          <rect
            x={minimapBox.x}
            y={minimapBox.y}
            width={minimapBox.w}
            height={minimapBox.h}
            fill="rgba(34, 197, 94, 0.25)"
            stroke="#22c55e"
            strokeWidth="1.8"
            rx="2"
          />
          <circle cx={minimapBox.cx} cy={minimapBox.cy} r="2.2" fill="#22c55e" />
        </svg>
      </div>

      {/* Right-Side Layers Panel */}
      {showLayersPanel && (
        <div className="right-layers-panel">
          {['satellite', 'hybrid', 'map', 'ndvi', 'evi', 'ndwi', 'lswi'].map((mode) => (
            <div
              key={mode}
              className={`layer-radio-row ${currentMode === mode ? 'selected' : ''}`}
              onClick={() => handleSelectMode(mode)}
            >
              <span className="custom-radio" />
              <span>{mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Bottom-Right Parcel Inspector Card */}
      {selectedParcel && (
        <div className="bottom-parcel-card">
          <div className="parcel-card-header">
            <span className="parcel-title">
              {selectedParcel.parcel_id
                ? (selectedParcel.parcel_id.startsWith('PARCEL_')
                    ? selectedParcel.parcel_id.replace('PARCEL_0', 'Parcel P').replace('PARCEL_', 'Parcel P')
                    : (selectedParcel.parcel_id.startsWith('Parcel') ? selectedParcel.parcel_id : `Parcel ${selectedParcel.parcel_id}`))
                : 'Parcel P102'}
            </span>
            <span className="parcel-chevron">›</span>
          </div>
          <div className="parcel-card-body">
            <div className="parcel-thumb-wrapper">
              <img
                src="/parcel_p102_thumb.jpg"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = '/api/parcels/thumbnail';
                }}
                alt="Parcel Thumbnail"
              />
            </div>
            <div className="parcel-details-table">
              <div className="detail-row">
                <span className="detail-label">Crop</span>
                <span className="detail-colon">:</span>
                <span className="detail-val">{selectedParcel.predicted_crop || 'Paddy'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Area</span>
                <span className="detail-colon">:</span>
                <span className="detail-val">
                  {(selectedParcel.area_ha ? Number(selectedParcel.area_ha).toFixed(1) : '2.4')} ha
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Health</span>
                <span className="detail-colon">:</span>
                <span className={`detail-val ${String(selectedParcel.crop_health || '').includes('Healthy') ? 'healthy' : 'moderate'}`}>
                  {selectedParcel.crop_health || 'Healthy (0.82)'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">NDVI</span>
                <span className="detail-colon">:</span>
                <span className="detail-val">
                  {selectedParcel.mean_ndvi !== undefined && selectedParcel.mean_ndvi !== null ? Number(selectedParcel.mean_ndvi).toFixed(2) : '0.78'}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Condition</span>
                <span className="detail-colon">:</span>
                <span className="detail-val">
                  {!selectedParcel.hazard || selectedParcel.hazard === 'None' ? 'Normal' : selectedParcel.hazard}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Switch to Detailed Dashboard Button (only in fullscreen mode if provided) */}
      {isFullscreen && onSwitchToDashboard && (
        <button
          onClick={onSwitchToDashboard}
          className="ref-map-switch-btn"
          title="Switch to Analytics Dashboard"
        >
          📊 Analytics View
        </button>
      )}
    </div>
  );
}
