import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { getCropColor, createParcelPopupContent } from './ParcelPopup';

const STUDY_CENTER = [8.70, 77.49];
const DEFAULT_ZOOM = 12;

// Settlement coordinates across Ambasamudram and Cheranmahadevi Taluks
const SETTLEMENTS = [
  { name: "Ambasamudram", role: "Taluk Headquarters", lat: 8.7082, lon: 77.4383, taluk: "Ambasamudram", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Cheranmahadevi", role: "Taluk Headquarters", lat: 8.6793, lon: 77.5617, taluk: "Cheranmahadevi", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Kallidaikurichi", role: "Agricultural Town", lat: 8.6809, lon: 77.4651, taluk: "Ambasamudram", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Veeravanallur", role: "Major Weaving & Agrarian Center", lat: 8.6895, lon: 77.5222, taluk: "Cheranmahadevi", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Pattamadai", role: "Famous Korai Mat Heritage Hub", lat: 8.6674, lon: 77.5844, taluk: "Cheranmahadevi", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Brahmadesam", role: "Heritage Village & Farmlands", lat: 8.7307, lon: 77.4468, taluk: "Ambasamudram", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Mannarkovil", role: "Temple Town & Irrigated Tracts", lat: 8.7281, lon: 77.4344, taluk: "Ambasamudram", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Ariyanayakipuram", role: "River Basin Farmlands", lat: 8.7211, lon: 77.5448, taluk: "Cheranmahadevi", district: "Tirunelveli", state: "Tamil Nadu" },
  { name: "Thiruppudaimaruthur", role: "Bird Sanctuary & Paddy Fields", lat: 8.7273, lon: 77.4994, taluk: "Ambasamudram", district: "Tirunelveli", state: "Tamil Nadu" }
];

export default function MapView({
  geojsonData,
  infrastructureData,
  hazardData,
  showInundationLayer = false,
  isDamageMode = false,
  activeBasemap,
  onChangeBasemap,
  selectedParcel,
  onSelectParcel,
  visibleCrops,
  minConfidence
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const baseLayersGroupRef = useRef({});
  const labelOverlayGroupRef = useRef(null);
  const geojsonLayerRef = useRef(null);
  const settlementsLayerRef = useRef(null);
  const infraLayerRef = useRef(null);
  const hazardLayerRef = useRef(null);

  const [showPlaces, setShowPlaces] = useState(true);
  const [showInfra, setShowInfra] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: STUDY_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      preferCanvas: true
    });

    // Custom Zoom Control top-right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // --- BASE TILE LAYERS ---
    // 1. Satellite Imagery (Esri World Imagery)
    const satImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
    });

    // 2. CartoDB Voyager (Street Map with full place & street names)
    const voyagerStreet = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    // 3. OpenStreetMap Standard
    const osmStreet = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    });

    // 4. CartoDB Dark Matter (Sleek Dark Theme)
    const darkMatter = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    // 5. Topographic Map
    const topoMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '&copy; Esri &mdash; National Geographic, DeLorme, NAVTEQ'
    });

    // --- REFERENCE LABELS OVERLAY FOR SATELLITE HYBRID ---
    // Adds place names, state names, district names, and roads over satellite imagery!
    const placesOverlay = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      pane: 'shadowPane'
    });
    const roadsOverlay = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      pane: 'shadowPane'
    });

    const hybridLabelsGroup = L.layerGroup([roadsOverlay, placesOverlay]);
    labelOverlayGroupRef.current = hybridLabelsGroup;

    baseLayersGroupRef.current = {
      satellite: satImagery,
      voyager: voyagerStreet,
      osm: osmStreet,
      dark: darkMatter,
      topo: topoMap
    };

    // Default: Satellite
    satImagery.addTo(map);
    hybridLabelsGroup.addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Basemap & Label Overlays
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;
    const layers = baseLayersGroupRef.current;

    // Remove all base tile layers
    Object.values(layers).forEach(layer => {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    });

    // Add selected base layer
    const activeLayer = layers[activeBasemap] || layers.satellite;
    activeLayer.addTo(map);

    // Satellite hybrid labels
    if (labelOverlayGroupRef.current) {
      if (activeBasemap === 'satellite' && showLabels) {
        if (!map.hasLayer(labelOverlayGroupRef.current)) {
          labelOverlayGroupRef.current.addTo(map);
        }
      } else {
        if (map.hasLayer(labelOverlayGroupRef.current)) {
          map.removeLayer(labelOverlayGroupRef.current);
        }
      }
    }
  }, [activeBasemap, showLabels]);

  // Settlements / Town Markers Layer
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    if (settlementsLayerRef.current) {
      map.removeLayer(settlementsLayerRef.current);
      settlementsLayerRef.current = null;
    }

    if (!showPlaces) return;

    const markers = SETTLEMENTS.map(settlement => {
      const isHQ = settlement.role.includes("Headquarters");
      const pinColor = isHQ ? "#38bdf8" : "#f59e0b";

      const icon = L.divIcon({
        className: 'settlement-map-marker',
        html: `
          <div class="settlement-pin-wrapper">
            <div class="settlement-pin-dot" style="background: ${pinColor}; box-shadow: 0 0 10px ${pinColor};"></div>
            <div class="settlement-pin-label">${settlement.name}</div>
          </div>
        `,
        iconSize: [120, 36],
        iconAnchor: [60, 18]
      });

      const marker = L.marker([settlement.lat, settlement.lon], { icon });
      marker.bindPopup(`
        <div style="font-family: var(--font-family); color: #f8fafc; padding: 4px;">
          <div style="font-size: 0.95rem; font-weight: 700; color: ${pinColor};">${settlement.name}</div>
          <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 2px;">${settlement.role}</div>
          <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 4px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px;">
            ${settlement.taluk} Taluk • ${settlement.district} • ${settlement.state}
          </div>
        </div>
      `, { maxWidth: 280 });

      return marker;
    });

    const group = L.layerGroup(markers).addTo(map);
    settlementsLayerRef.current = group;
  }, [showPlaces]);

  // Infrastructure (Waterways & Roads) Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !infrastructureData) return;
    const map = mapInstanceRef.current;

    if (infraLayerRef.current) {
      map.removeLayer(infraLayerRef.current);
      infraLayerRef.current = null;
    }

    if (!showInfra) return;

    const infraLayer = L.geoJSON(infrastructureData, {
      style: (feature) => {
        const cat = feature.properties?.category;
        if (cat === "waterway") {
          return {
            color: "#00e5ff",
            weight: 3.5,
            opacity: 0.85,
            dashArray: "1, 2"
          };
        } else {
          return {
            color: "#fb923c",
            weight: 2.2,
            opacity: 0.8
          };
        }
      },
      onEachFeature: (feature, layer) => {
        const name = feature.properties?.name || "Local Infrastructure";
        const cat = feature.properties?.category === "waterway" ? "🌊 Waterway / Canal" : "🛣️ Road Corridor";
        layer.bindTooltip(`<strong>${name}</strong><br><small>${cat}</small>`, { sticky: true });
      }
    }).addTo(map);

    infraLayerRef.current = infraLayer;
  }, [infrastructureData, showInfra]);

  // Inundation / Hazard Footprint Layer
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    if (hazardLayerRef.current) {
      map.removeLayer(hazardLayerRef.current);
      hazardLayerRef.current = null;
    }

    if (!showInundationLayer || !hazardData) return;

    const hGeojson = hazardData.geojson || hazardData;
    if (!hGeojson || !hGeojson.features) return;

    const layer = L.geoJSON(hGeojson, {
      style: {
        fillColor: '#00e5ff',
        fillOpacity: 0.7,
        color: '#0284c7',
        weight: 1.2
      },
      onEachFeature: (feature, l) => {
        const ha = (feature.properties?.area_ha || 0).toFixed(2);
        l.bindTooltip(`<strong>🌊 Flood Inundation Footprint</strong><br>Area: ${ha} ha<br><small>Sentinel-2 Change Detection</small>`, { sticky: true });
      }
    }).addTo(map);

    hazardLayerRef.current = layer;
  }, [hazardData, showInundationLayer]);

  // Classified Agricultural Parcels Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !geojsonData) return;
    const map = mapInstanceRef.current;

    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }

    const parcelStyle = (feature) => {
      const props = feature.properties || {};
      const crop = props.predicted_crop || props.crop;

      if (isDamageMode) {
        const sev = props.severity || 'No Damage / Unaffected';
        switch (sev) {
          case 'Severe Damage':
            return { fillColor: '#8e44ad', weight: 2, opacity: 1, color: '#6c3483', fillOpacity: 0.85 };
          case 'High Damage':
            return { fillColor: '#e74c3c', weight: 2, opacity: 1, color: '#c0392b', fillOpacity: 0.85 };
          case 'Moderate Damage':
            return { fillColor: '#e67e22', weight: 1.8, opacity: 0.95, color: '#d35400', fillOpacity: 0.8 };
          case 'Low Damage':
            return { fillColor: '#f1c40f', weight: 1.5, opacity: 0.95, color: '#d4ac0d', fillOpacity: 0.75 };
          default:
            return { fillColor: '#334155', weight: 1, opacity: 0.5, color: '#1e293b', fillOpacity: 0.35 };
        }
      }

      const colors = getCropColor(crop);
      return {
        fillColor: colors.fill,
        weight: 1.5,
        opacity: 0.95,
        color: colors.stroke,
        fillOpacity: 0.65
      };
    };

    const onEachFeature = (feature, layer) => {
      const popupHtml = createParcelPopupContent(feature.properties);
      layer.bindPopup(popupHtml, { maxWidth: 320 });

      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({
            weight: 3,
            fillOpacity: 0.9,
            color: '#ffffff'
          });
          l.bringToFront();
        },
        mouseout: (e) => {
          geojsonLayerRef.current?.resetStyle(e.target);
        },
        click: (e) => {
          if (onSelectParcel) {
            onSelectParcel(feature);
          }
        }
      });
    };

    const filterFeature = (feature) => {
      const crop = feature.properties?.predicted_crop || feature.properties?.crop;
      const conf = feature.properties?.confidence || 0;

      if (visibleCrops && !visibleCrops[crop]) return false;
      if (minConfidence !== undefined && conf < minConfidence) return false;
      return true;
    };

    const parcelLayer = L.geoJSON(geojsonData, {
      style: parcelStyle,
      onEachFeature,
      filter: filterFeature
    }).addTo(map);

    geojsonLayerRef.current = parcelLayer;
  }, [geojsonData, visibleCrops, minConfidence, onSelectParcel, isDamageMode]);

  const handleFlyTo = (lat, lon, zoom = 14) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([lat, lon], zoom, { duration: 1.2 });
    }
  };

  const handleRecenter = () => {
    if (mapInstanceRef.current) {
      if (geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
        mapInstanceRef.current.fitBounds(geojsonLayerRef.current.getBounds(), { padding: [40, 40] });
      } else {
        mapInstanceRef.current.setView(STUDY_CENTER, DEFAULT_ZOOM);
      }
    }
  };

  return (
    <div className="map-viewport-wrapper">
      <div ref={mapContainerRef} className="map-container-elem" />

      {/* Top Floating Breadcrumb Bar */}
      <div className="map-floating-breadcrumbs">
        <span className="crumb-badge">INDIA</span>
        <span className="crumb-arrow">›</span>
        <span className="crumb-badge">TAMIL NADU</span>
        <span className="crumb-arrow">›</span>
        <span className="crumb-badge">TIRUNELVELI DISTRICT</span>
        <span className="crumb-arrow">›</span>
        <span className="crumb-badge highlighted">AMBASAMUDRAM & CHERANMAHADEVI TALUKS</span>
      </div>

      {/* Quick Jump-to-Settlement Bar */}
      <div className="map-quick-jump-bar">
        <span className="jump-title">⚡ Quick Jump:</span>
        <button onClick={handleRecenter} className="jump-pill active">Study Area (All)</button>
        <button onClick={() => handleFlyTo(8.7082, 77.4383, 14)} className="jump-pill">Ambasamudram</button>
        <button onClick={() => handleFlyTo(8.6793, 77.5617, 14)} className="jump-pill">Cheranmahadevi</button>
        <button onClick={() => handleFlyTo(8.6809, 77.4651, 14)} className="jump-pill">Kallidaikurichi</button>
        <button onClick={() => handleFlyTo(8.6895, 77.5222, 14)} className="jump-pill">Veeravanallur</button>
        <button onClick={() => handleFlyTo(8.6674, 77.5844, 14)} className="jump-pill">Pattamadai</button>
        <button onClick={() => handleFlyTo(8.7307, 77.4468, 14)} className="jump-pill">Brahmadesam</button>
      </div>

      {/* Floating Layer Settings Control */}
      <div className="map-layer-controls-box">
        <div className="ctrl-title">🗺️ Basemap & Overlay Layers</div>
        
        {/* Basemap Picker */}
        <div className="basemap-pills-row">
          <button
            className={`map-pill-btn ${activeBasemap === 'satellite' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('satellite')}
            title="Esri Satellite Imagery + Place & Street Names"
          >
            🛰️ Satellite (Hybrid)
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'voyager' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('voyager')}
            title="Detailed Street Map with All Roads & Villages"
          >
            🗺️ Street (Voyager)
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'dark' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('dark')}
            title="High-Contrast Dark GIS Basemap"
          >
            🌙 Dark GIS
          </button>
          <button
            className={`map-pill-btn ${activeBasemap === 'topo' ? 'active' : ''}`}
            onClick={() => onChangeBasemap('topo')}
            title="Topographic Elevation Map"
          >
            ⛰️ Topo
          </button>
        </div>

        {/* Feature Overlays Toggles */}
        <div className="overlay-toggles-row">
          <label className="toggle-chk-label">
            <input
              type="checkbox"
              checked={showPlaces}
              onChange={(e) => setShowPlaces(e.target.checked)}
            />
            <span>Town & Village Pins</span>
          </label>
          <label className="toggle-chk-label">
            <input
              type="checkbox"
              checked={showInfra}
              onChange={(e) => setShowInfra(e.target.checked)}
            />
            <span>Thamirabarani River & Highways</span>
          </label>
          {activeBasemap === 'satellite' && (
            <label className="toggle-chk-label">
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
              />
              <span>Street & Place Name Labels</span>
            </label>
          )}
        </div>
      </div>

      {/* Map Legend */}
      <div className="map-legend">
        <div className="legend-title">GIS Layers & Classification Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#16a34a', border: '1.5px solid #15803d', borderRadius: 3 }} />
            <span>Paddy (நெல்)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#eab308', border: '1.5px solid #ca8a04', borderRadius: 3 }} />
            <span>Banana (வாழை)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#64748b', border: '1.5px solid #475569', borderRadius: 3 }} />
            <span>Other / Fallow</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 20, height: 3, background: '#00e5ff', display: 'inline-block' }} />
            <span>Thamirabarani River</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 20, height: 3, background: '#fb923c', display: 'inline-block' }} />
            <span>State Highways</span>
          </div>
        </div>
      </div>
    </div>
  );
}
