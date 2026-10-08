import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { getCropColor, createParcelPopupContent } from './ParcelPopup';

export default function MapView({
  geojsonData,
  infrastructureData,
  placesData,
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
      center: [8.695, 77.502],
      zoom: 12,
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

    // Esri World Street Map (100% Free, NO API KEY, Zero Watermarks)
    const streetMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS'
    });

    // Esri Dark Gray Canvas (100% Free, NO API KEY, Zero Watermarks)
    const darkMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
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
      voyager: streetMap,
      dark: darkMap,
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

  // Settlements / Town Markers Layer (from placesData or fallback)
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    if (settlementsLayerRef.current) {
      map.removeLayer(settlementsLayerRef.current);
      settlementsLayerRef.current = null;
    }

    if (!showPlaces || !placesData || placesData.length === 0) return;

    const markers = placesData.map(place => {
      const isHQ = place.name === "Ambasamudram" || place.name === "Cheranmahadevi";
      const pinColor = isHQ ? "#0284c7" : "#d97706";

      const icon = L.divIcon({
        className: 'settlement-map-marker',
        html: `
          <div class="settlement-pin-wrapper">
            <div class="settlement-pin-dot" style="background: ${pinColor}; box-shadow: 0 0 8px ${pinColor};"></div>
            <div class="settlement-pin-label">${place.name}</div>
          </div>
        `,
        iconSize: [120, 36],
        iconAnchor: [60, 18]
      });

      const marker = L.marker([place.lat, place.lon], { icon });
      marker.bindPopup(`
        <div style="font-family: inherit; color: #0f172a; padding: 4px;">
          <div style="font-size: 0.95rem; font-weight: 700; color: ${pinColor};">${place.name}</div>
          <div style="font-size: 0.75rem; color: #475569; margin-top: 2px;">${place.display_name || place.taluk}</div>
          <div style="font-size: 0.7rem; color: #64748b; margin-top: 4px; border-top: 1px solid #e2e8f0; padding-top: 4px;">
            ${place.taluk} Taluk • ${place.district} • ${place.state}
          </div>
        </div>
      `, { maxWidth: 280 });

      return marker;
    });

    const group = L.layerGroup(markers).addTo(map);
    settlementsLayerRef.current = group;
  }, [showPlaces, placesData]);

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
            color: "#0284c7",
            weight: 3.5,
            opacity: 0.85,
            dashArray: "1, 2"
          };
        } else {
          return {
            color: "#ea580c",
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
        fillOpacity: 0.75
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
        map.fitBounds(bounds, { padding: [50, 50] });
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
        map.flyToBounds(bounds, { padding: [50, 50], duration: 1.0 });
        return;
      }
    }

    if (selectedTaluk && selectedTaluk.toLowerCase().includes('ambasamudram')) {
      map.flyTo([8.712, 77.445], 13, { duration: 1.0 });
    } else if (selectedTaluk && selectedTaluk.toLowerCase().includes('cheranmahadevi')) {
      map.flyTo([8.685, 77.55], 13, { duration: 1.0 });
    } else {
      map.flyTo([8.695, 77.502], 12, { duration: 1.0 });
    }
  }, [selectedTaluk, geojsonData]);

  // Fit bounds button handler
  const handleFitParcels = () => {
    if (mapInstanceRef.current && geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
      const bounds = geojsonLayerRef.current.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
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
          style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '5px' }}
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

      {/* Clean White Professional Map Legend (Bottom Right) */}
      <div className="map-legend">
        <div className="legend-title">Classification Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#16a34a', border: '1.5px solid #14532d', borderRadius: 3 }} />
            <span>Paddy (நெல்)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#eab308', border: '1.5px solid #854d0e', borderRadius: 3 }} />
            <span>Banana (வாழை)</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#9333ea', border: '1.5px solid #581c87', borderRadius: 3 }} />
            <span>Other / Fallow</span>
          </div>
          {showInfra && (
            <>
              <div className="legend-item">
                <span style={{ width: 20, height: 3, background: '#0284c7', display: 'inline-block' }} />
                <span>Thamirabarani River</span>
              </div>
              <div className="legend-item">
                <span style={{ width: 20, height: 3, background: '#ea580c', display: 'inline-block' }} />
                <span>Major Highways</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
