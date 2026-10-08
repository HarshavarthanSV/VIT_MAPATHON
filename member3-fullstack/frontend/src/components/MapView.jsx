import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { getCropColor, createParcelPopupContent } from './ParcelPopup';

const STUDY_CENTER = [8.70, 77.49];
const DEFAULT_ZOOM = 12;

export default function MapView({
  geojsonData,
  activeBasemap,
  selectedParcel,
  onSelectParcel,
  visibleCrops,
  minConfidence
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const geojsonLayerRef = useRef(null);
  const tileLayerRef = useRef(null);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: STUDY_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true,
      preferCanvas: true
    });

    // Basemap URLs
    const satelliteUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
    const streetUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

    const tileUrl = activeBasemap === 'satellite' ? satelliteUrl : streetUrl;
    const attribution = activeBasemap === 'satellite' 
      ? 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
      : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

    const tileLayer = L.tileLayer(tileUrl, {
      maxZoom: 19,
      attribution
    }).addTo(map);

    tileLayerRef.current = tileLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Basemap Layer when activeBasemap changes
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;

    const satelliteUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
    const streetUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

    const newUrl = activeBasemap === 'satellite' ? satelliteUrl : streetUrl;
    tileLayerRef.current.setUrl(newUrl);
  }, [activeBasemap]);

  // Update GeoJSON Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !geojsonData) return;

    const map = mapInstanceRef.current;

    // Remove existing GeoJSON layer
    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }

    const parcelStyle = (feature) => {
      const crop = feature.properties?.predicted_crop;
      const colors = getCropColor(crop);

      return {
        fillColor: colors.fill,
        weight: 1.5,
        opacity: 0.9,
        color: colors.stroke,
        fillOpacity: 0.6,
        dashArray: ''
      };
    };

    const onEachFeature = (feature, layer) => {
      // Bind popup
      const popupContent = createParcelPopupContent(feature.properties);
      layer.bindPopup(popupContent, { maxWidth: 300 });

      // Hover interactions
      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({
            weight: 3,
            fillOpacity: 0.85,
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

    // Filter features according to state
    const filterFeature = (feature) => {
      const crop = feature.properties?.predicted_crop;
      const conf = feature.properties?.confidence || 0;

      if (visibleCrops && !visibleCrops[crop]) {
        return false;
      }
      if (minConfidence !== undefined && conf < minConfidence) {
        return false;
      }
      return true;
    };

    const newGeojsonLayer = L.geoJSON(geojsonData, {
      style: parcelStyle,
      onEachFeature,
      filter: filterFeature
    }).addTo(map);

    geojsonLayerRef.current = newGeojsonLayer;
  }, [geojsonData, visibleCrops, minConfidence, onSelectParcel]);

  const handleRecenter = () => {
    if (mapInstanceRef.current) {
      if (geojsonLayerRef.current && geojsonLayerRef.current.getLayers().length > 0) {
        mapInstanceRef.current.fitBounds(geojsonLayerRef.current.getBounds(), { padding: [30, 30] });
      } else {
        mapInstanceRef.current.setView(STUDY_CENTER, DEFAULT_ZOOM);
      }
    }
  };

  return (
    <div className="map-viewport-wrapper">
      <div ref={mapContainerRef} />

      {/* Floating Info Overlay */}
      <div className="map-floating-overlay">
        <span>📍 <strong>Ambasamudram & Cheranmahadevi</strong> (8.70° N, 77.49° E)</span>
        <button
          onClick={handleRecenter}
          className="btn-primary"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
          title="Recenter Map Bounds"
        >
          Reset View
        </button>
      </div>

      {/* Legend Box */}
      <div className="map-legend">
        <div className="legend-title">Crop Classification Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#2e7d32', border: '1px solid #1b5e20', borderRadius: 3, display: 'inline-block' }}></span>
            <span>Paddy</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#fbc02d', border: '1px solid #f57f17', borderRadius: 3, display: 'inline-block' }}></span>
            <span>Banana</span>
          </div>
          <div className="legend-item">
            <span style={{ width: 14, height: 14, background: '#78909c', border: '1px solid #455a64', borderRadius: 3, display: 'inline-block' }}></span>
            <span>Other</span>
          </div>
        </div>
      </div>
    </div>
  );
}
