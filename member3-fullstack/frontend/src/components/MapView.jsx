import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { getCropColor, createParcelPopupContent } from './ParcelPopup';

const STUDY_CENTER = [8.695, 77.502];
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
  activeBasemap = 'satellite',
  showPlaces = false,
  showInfra = true,
  showLabels = true,
  selectedTaluk = 'all',
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
  const hasFitInitialBoundsRef = useRef(false);

  // Initialize Leaflet Map (SVG Renderer for 100% vector reliability)
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: STUDY_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      preferCanvas: false // SVG renderer ensures path elements always draw
    });

    // Custom high-priority pane for Agricultural Parcels
    const parcelsPane = map.createPane('parcelsPane');
    parcelsPane.style.zIndex = '500';

    // Custom Zoom Control top-right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // --- BASE TILE LAYERS ---
    const satImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
    });

    const voyagerStreet = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    const darkMatter = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    });

    const topoMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '&copy; Esri &mdash; National Geographic, DeLorme, NAVTEQ'
    });

    // Reference labels overlay for satellite hybrid
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
      dark: darkMatter,
      topo: topoMap
    };

    // Default: Satellite + labels
    satImagery.addTo(map);
    hybridLabelsGroup.addTo(map);

    mapInstanceRef.current = map;

    // Invalidate size to guarantee correct container dimensions
    setTimeout(() => {
      map.invalidateSize();
    }, 150);

    const handleResize = () => map.invalidateSize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
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

  // Classified Agricultural Parcels Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !geojsonData) return;
    const map = mapInstanceRef.current;

    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }

    // Force map size re-calculation
    map.invalidateSize();

    const parcelStyle = (feature) => {
      const crop = feature.properties?.predicted_crop;
      const colors = getCropColor(crop);

      return {
        pane: 'parcelsPane',
        fillColor: colors.fill,
        weight: 2.2,
        opacity: 1.0,
        color: colors.stroke || '#ffffff',
        fillOpacity: 0.72
      };
    };

    const highlightStyle = {
      pane: 'parcelsPane',
      weight: 4.0,
      color: '#ffffff',
      fillOpacity: 0.95
    };

    const parcelLayer = L.geoJSON(geojsonData, {
      style: parcelStyle,
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {};
        const confPct = Math.round((props.confidence || 0) * 100);
        const areaHa = props.area_ha ? props.area_ha.toFixed(2) : (props.area_sq_km ? (props.area_sq_km * 100).toFixed(2) : '0.50');

        layer.bindTooltip(
          `<strong>${props.parcel_id}</strong><br/>` +
          `Crop: <strong>${props.predicted_crop}</strong> (${confPct}%)<br/>` +
          `Taluk: ${props.taluk || 'Study Area'}<br/>` +
          `Area: ${areaHa} ha`,
          { sticky: true, className: 'leaflet-custom-tooltip' }
        );

        layer.on({
          mouseover: (e) => {
            const l = e.target;
            l.setStyle(highlightStyle);
            l.bringToFront();
          },
          mouseout: (e) => {
            const l = e.target;
            parcelLayer.resetStyle(l);
          },
          click: (e) => {
            onSelectParcel(feature);
            L.DomEvent.stopPropagation(e);
            const popupContent = createParcelPopupContent(props);
            layer.bindPopup(popupContent, { maxWidth: 320 }).openPopup();
          }
        });
      }
    }).addTo(map);

    geojsonLayerRef.current = parcelLayer;

    // Auto-fit bounds on initial load of parcels
    if (!hasFitInitialBoundsRef.current && parcelLayer.getLayers().length > 0) {
      const bounds = parcelLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40] });
        hasFitInitialBoundsRef.current = true;
      }
    }
  }, [geojsonData, onSelectParcel]);

  // Fly / fit bounds when selectedTaluk changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    if (geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
      const bounds = geojsonLayerRef.current.getBounds();
      if (bounds.isValid()) {
        map.flyToBounds(bounds, { padding: [40, 40], duration: 1.2 });
        return;
      }
    }

    if (selectedTaluk && selectedTaluk.toLowerCase().includes('ambasamudram')) {
      map.flyTo([8.712, 77.445], 13, { duration: 1.2 });
    } else if (selectedTaluk && selectedTaluk.toLowerCase().includes('cheranmahadevi')) {
      map.flyTo([8.685, 77.55], 13, { duration: 1.2 });
    } else {
      map.flyTo(STUDY_CENTER, DEFAULT_ZOOM, { duration: 1.2 });
    }
  }, [selectedTaluk, geojsonData]);

  // Fit bounds button handler
  const handleFitParcels = () => {
    if (mapInstanceRef.current && geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
      const bounds = geojsonLayerRef.current.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    } else if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(STUDY_CENTER, DEFAULT_ZOOM);
    }
  };

  return (
    <div className="map-viewport-wrapper">
      <div ref={mapContainerRef} className="map-container-elem" />

      {/* Floating Action Controls top right */}
      <div style={{ position: 'absolute', top: '1rem', right: '1rem', zIndex: 700, display: 'flex', gap: '0.5rem' }}>
        <a
          href="http://localhost:8000/map"
          target="_blank"
          rel="noreferrer"
          className="map-recenter-pill-btn"
          title="Open Standalone Folium Fullscreen Map"
          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          🌐 Standalone Folium Map
        </a>
        <button
          onClick={handleFitParcels}
          className="map-recenter-pill-btn"
          title="Fit view to current parcels"
        >
          🎯 Fit All Parcels
        </button>
      </div>

      {/* Map Legend (Bottom Right) */}
      <div className="map-legend">
        <div className="legend-title">Classification Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#22c55e', border: '1.5px solid #14532d', borderRadius: 3 }} />
            <span>Paddy (நெல்)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#facc15', border: '1.5px solid #854d0e', borderRadius: 3 }} />
            <span>Banana (வாழை)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#c084fc', border: '1.5px solid #581c87', borderRadius: 3 }} />
            <span>Other / Fallow</span>
          </div>
          {showInfra && (
            <>
              <div className="legend-item">
                <span style={{ width: 20, height: 3, background: '#00e5ff', display: 'inline-block' }} />
                <span>Thamirabarani River</span>
              </div>
              <div className="legend-item">
                <span style={{ width: 20, height: 3, background: '#fb923c', display: 'inline-block' }} />
                <span>Major Highways</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
