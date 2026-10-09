import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { getCropColor, createParcelPopupContent } from './ParcelPopup';

export default function MapView({
  geojsonData,
  infrastructureData,
  placesData,
  activeBasemap = 'satellite',
  showParcelBoundaries = true,
  showPlaces = false,
  showInfra = true,
  showLabels = true,
  selectedTaluk = 'all',
  selectedParcel,
  onSelectParcel,
  visibleCrops = { Paddy: true, Banana: true, Other: true, Water: true, NonAgri: true },
  minConfidence = 0.0
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const baseLayersGroupRef = useRef({});
  const labelOverlayGroupRef = useRef(null);
  const geojsonLayerRef = useRef(null);
  const settlementsLayerRef = useRef(null);
  const infraLayerRef = useRef(null);
  const cityPinsLayerRef = useRef(null);
  const hasFitInitialBoundsRef = useRef(false);

  // Initialize Leaflet Map (SVG Renderer for 100% vector reliability)
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [8.695, 77.492],
      zoom: 13,
      minZoom: 9,
      maxZoom: 19,
      zoomControl: false,
      preferCanvas: false // SVG renderer ensures path elements always draw with crisp vector edges
    });

    // Custom high-priority pane for Agricultural Parcels
    const parcelsPane = map.createPane('parcelsPane');
    parcelsPane.style.zIndex = '500';

    // Zoom Control on top-left (matching reference UI)
    L.control.zoom({ position: 'topleft' }).addTo(map);

    // Leaflet Scale Control on bottom-left (0 2 4 km)
    L.control.scale({ position: 'bottomleft', imperial: false, maxWidth: 120 }).addTo(map);

    // --- BASE TILE LAYERS ---
    const satImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
    });

    const streetMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; DeLorme, NAVTEQ, USGS'
    });

    const darkMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      attribution: 'Tiles &copy; Esri'
    });

    const topoMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '&copy; Esri &mdash; National Geographic'
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
      hybrid: satImagery,
      map: streetMap,
      voyager: streetMap,
      dark: darkMap,
      topo: topoMap
    };

    // Default: Satellite + labels
    satImagery.addTo(map);
    hybridLabelsGroup.addTo(map);

    // Add City Pin markers on map (Neat Professional GIS Markers)
    const pinGroup = L.layerGroup();
    
    const createProCityIcon = (name, prefix) => {
      const isA = prefix === 'City A';
      return L.divIcon({
        className: 'leaflet-city-pin-marker',
        html: `
          <div class="pro-city-callout ${isA ? 'city-a-callout' : 'city-b-callout'}">
            <div class="pro-city-pill">
              <span class="pro-city-tag ${isA ? 'tag-a' : 'tag-b'}">${prefix}</span>
              <span class="pro-city-name">${name}</span>
            </div>
            <div class="pro-city-pin">
              <div class="pro-pin-stem"></div>
              <div class="pro-pin-beacon">
                <span class="beacon-pulse"></span>
                <span class="beacon-dot"></span>
              </div>
            </div>
          </div>
        `,
        iconSize: [130, 40],
        iconAnchor: [65, 40]
      });
    };

    // City A: Ambasamudram Taluk Center (West)
    const markerA = L.marker([8.704, 77.448], { icon: createProCityIcon('Ambasamudram', 'City A') });
    markerA.on('click', () => map.flyTo([8.704, 77.448], 14, { duration: 0.8 }));
    pinGroup.addLayer(markerA);

    // City B: Cheranmahadevi Taluk Center (East)
    const markerB = L.marker([8.704, 77.525], { icon: createProCityIcon('Cheranmahadevi', 'City B') });
    markerB.on('click', () => map.flyTo([8.704, 77.525], 14, { duration: 0.8 }));
    pinGroup.addLayer(markerB);

    pinGroup.addTo(map);
    cityPinsLayerRef.current = pinGroup;

    mapInstanceRef.current = map;

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
      if ((activeBasemap === 'satellite' || activeBasemap === 'hybrid') && showLabels) {
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

    try {
      const rawInfra = Array.isArray(infrastructureData?.features) ? infrastructureData.features : [];
      const validInfra = rawInfra.filter(f => f && f.type === 'Feature' && f.geometry && typeof f.geometry.type === 'string' && Array.isArray(f.geometry.coordinates));
      const safeInfra = { ...infrastructureData, type: 'FeatureCollection', features: validInfra };

      const infraLayer = L.geoJSON(safeInfra, {
        filter: (feature) => {
          const cat = feature.properties?.category;
          if (cat === "waterway" && !visibleCrops.Water) return false;
          return true;
        },
        style: (feature) => {
          const cat = feature.properties?.category;
          const type = feature.properties?.type;
          if (cat === "waterway") {
            const isMain = type === "river";
            return {
              color: isMain ? "#0284c7" : "#38bdf8",
              weight: isMain ? 1.8 : 1.15,
              opacity: isMain ? 0.92 : 0.80,
              lineCap: "round",
              lineJoin: "round"
            };
          } else {
            return {
              color: "#ea580c",
              weight: 1.4,
              opacity: 0.70,
              lineCap: "round",
              lineJoin: "round"
            };
          }
        },
        onEachFeature: (feature, layer) => {
          const name = feature.properties?.name || "Local Infrastructure";
          const type = feature.properties?.type === "river" ? "Main River Channel" : (feature.properties?.type === "canal" ? "Irrigation Canal" : "Stream / Drainage");
          const cat = feature.properties?.category === "waterway" ? `🌊 ${name} (${type})` : `🛣️ ${name} (Road Corridor)`;
          layer.bindTooltip(`<strong>${cat}</strong>`, { sticky: true });
        }
      }).addTo(map);

      infraLayerRef.current = infraLayer;
    } catch (infraErr) {
      console.error('Error creating infrastructure layer:', infraErr);
    }
  }, [infrastructureData, showInfra, visibleCrops.Water]);

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
        weight: showParcelBoundaries ? 1.25 : 0,
        opacity: showParcelBoundaries ? 0.92 : 0,
        color: '#ffffff', // Crisp white parcel boundary outline
        fillOpacity: 0.72
      };
    };

    const highlightStyle = {
      pane: 'parcelsPane',
      weight: 3.5,
      color: '#ffffff',
      fillOpacity: 0.95
    };

    // Sanitize features to ensure valid GeoJSON geometry with coordinates
    const rawFeatures = Array.isArray(geojsonData?.features) ? geojsonData.features : [];
    const validFeatures = rawFeatures.filter((f) => {
      if (!f || f.type !== 'Feature') return false;
      const geom = f.geometry;
      return (
        geom &&
        typeof geom === 'object' &&
        typeof geom.type === 'string' &&
        Array.isArray(geom.coordinates) &&
        geom.coordinates.length > 0
      );
    });

    const safeGeojson = {
      ...geojsonData,
      type: 'FeatureCollection',
      features: validFeatures
    };

    let parcelLayer = null;
    try {
      parcelLayer = L.geoJSON(safeGeojson, {
        style: parcelStyle,
        onEachFeature: (feature, layer) => {
          const props = feature.properties || {};
          const confPct = Math.round((props.confidence || 0) * 100);
          const areaHa = props.area_ha ? Number(props.area_ha).toFixed(2) : (props.area_sq_km ? (Number(props.area_sq_km) * 100).toFixed(2) : '1.50');

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
              if (onSelectParcel) {
                onSelectParcel(props);
              }
              L.DomEvent.stopPropagation(e);
              const popupContent = createParcelPopupContent(props);
              layer.bindPopup(popupContent, { maxWidth: 320 }).openPopup();
            }
          });
        }
      }).addTo(map);

      geojsonLayerRef.current = parcelLayer;
    } catch (layerErr) {
      console.error('Error creating Leaflet parcel GeoJSON layer:', layerErr);
      return;
    }

    // Helper to verify bounds are valid WGS84 lat/lon coordinates
    const isValidWgs84 = (b) => {
      if (!b || !b.isValid()) return false;
      const s = b.getSouth(), n = b.getNorth(), w = b.getWest(), e = b.getEast();
      return s >= -90 && n <= 90 && w >= -180 && e <= 180 && (n - s) > 0.0001 && (e - w) > 0.0001;
    };

    // Auto-fit bounds on initial load of parcels
    if (parcelLayer && !hasFitInitialBoundsRef.current && parcelLayer.getLayers().length > 0) {
      const bounds = parcelLayer.getBounds();
      if (isValidWgs84(bounds)) {
        map.fitBounds(bounds, { padding: [35, 35], maxZoom: 14 });
        hasFitInitialBoundsRef.current = true;
      } else {
        map.setView([8.695, 77.492], 13);
        hasFitInitialBoundsRef.current = true;
      }
    }
  }, [geojsonData, showParcelBoundaries, onSelectParcel]);

  // Fly / fit bounds when selectedTaluk changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    const isValidWgs84 = (b) => {
      if (!b || !b.isValid()) return false;
      const s = b.getSouth(), n = b.getNorth(), w = b.getWest(), e = b.getEast();
      return s >= -90 && n <= 90 && w >= -180 && e <= 180 && (n - s) > 0.0001 && (e - w) > 0.0001;
    };

    if (selectedTaluk && selectedTaluk.toLowerCase().includes('ambasamudram')) {
      map.flyTo([8.704, 77.525], 13, { duration: 0.8 });
    } else if (selectedTaluk && selectedTaluk.toLowerCase().includes('cheranmahadevi')) {
      map.flyTo([8.692, 77.460], 13, { duration: 0.8 });
    } else {
      if (geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
        const bounds = geojsonLayerRef.current.getBounds();
        if (isValidWgs84(bounds)) {
          map.flyToBounds(bounds, { padding: [35, 35], maxZoom: 14, duration: 0.8 });
          return;
        }
      }
      map.flyTo([8.695, 77.492], 13, { duration: 0.8 });
    }
  }, [selectedTaluk]);

  // Fit bounds button handler
  const handleFitParcels = () => {
    if (mapInstanceRef.current) {
      const map = mapInstanceRef.current;
      if (geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
        const bounds = geojsonLayerRef.current.getBounds();
        const s = bounds.getSouth(), n = bounds.getNorth(), w = bounds.getWest(), e = bounds.getEast();
        if (bounds.isValid() && s >= -90 && n <= 90 && w >= -180 && e <= 180) {
          map.fitBounds(bounds, { padding: [35, 35], maxZoom: 14 });
          return;
        }
      }
      map.setView([8.695, 77.492], 13);
    }
  };

  return (
    <div className="map-viewport-wrapper">
      <div ref={mapContainerRef} className="map-container-elem" />

      {/* Floating Action Controls on map left toolbar */}
      <div className="map-left-floating-bar">
        <button
          onClick={handleFitParcels}
          className="map-tool-btn"
          title="Fit view to all parcels"
        >
          🎯
        </button>
        <button
          className="map-tool-btn"
          title="Toggle Layers"
        >
          🥞
        </button>
        <button
          className="map-tool-btn"
          title="Distance & Area Measurement"
        >
          📐
        </button>
      </div>
    </div>
  );
}
