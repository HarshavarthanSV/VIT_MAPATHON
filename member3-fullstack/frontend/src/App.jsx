import React, { useState, useEffect, useMemo } from 'react';
import MapView from './components/MapView';
import FilterPanel from './components/FilterPanel';
import StatisticsCard from './components/StatisticsCard';
import ParcelPopup from './components/ParcelPopup';
import MetricsModal from './components/MetricsModal';

export default function App() {
  const [geojsonData, setGeojsonData] = useState(null);
  const [infrastructureData, setInfrastructureData] = useState(null);
  const [placesData, setPlacesData] = useState(null);
  const [talukAcreage, setTalukAcreage] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);

  // Filter States
  const [visibleCrops, setVisibleCrops] = useState({
    Paddy: true,
    Banana: true,
    Other: true
  });
  const [selectedTaluk, setSelectedTaluk] = useState('all');
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);

  // Basemap & Overlays
  const [activeBasemap, setActiveBasemap] = useState('satellite');
  const [showPlaces, setShowPlaces] = useState(false);
  const [showInfra, setShowInfra] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all GIS and ML layers from backend
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [parcelsRes, statsRes, metricsRes, fiRes, healthRes, infraRes, placesRes, talukRes] = await Promise.all([
          fetch('/api/parcels'),
          fetch('/api/statistics'),
          fetch('/api/metrics'),
          fetch('/api/feature-importance').catch(() => null),
          fetch('/api/health').catch(() => null),
          fetch('/api/infrastructure').catch(() => null),
          fetch('/api/places').catch(() => null),
          fetch('/api/taluk-acreage').catch(() => null)
        ]);

        if (!parcelsRes.ok) throw new Error(`Parcels fetch failed: ${parcelsRes.statusText}`);
        if (!statsRes.ok) throw new Error(`Statistics fetch failed: ${statsRes.statusText}`);

        const parcels = await parcelsRes.json();
        const stats = await statsRes.json();
        const metricsData = metricsRes.ok ? await metricsRes.json() : null;
        const fiData = fiRes && fiRes.ok ? await fiRes.json() : null;
        const health = healthRes && healthRes.ok ? await healthRes.json() : null;
        const infra = infraRes && infraRes.ok ? await infraRes.json() : null;
        const places = placesRes && placesRes.ok ? await placesRes.json() : [];
        const taluks = talukRes && talukRes.ok ? await talukRes.json() : [];

        setGeojsonData(parcels);
        setStatistics(stats);
        setMetrics(metricsData);
        setFeatureImportance(fiData);
        setHealthInfo(health);
        setInfrastructureData(infra);
        setPlacesData(places);
        setTalukAcreage(taluks);
      } catch (err) {
        console.error('Error fetching GIS data:', err);
        setError(err.message || 'Error connecting to backend API');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleToggleCrop = (crop) => {
    setVisibleCrops((prev) => ({
      ...prev,
      [crop]: !prev[crop]
    }));
  };

  const handleResetFilters = () => {
    setVisibleCrops({ Paddy: true, Banana: true, Other: true });
    setSelectedTaluk('all');
    setMinConfidence(0.0);
  };

  // Filter features based on crop, confidence, and taluk
  const allFeatures = geojsonData?.features || [];
  const filteredFeatures = useMemo(() => {
    return allFeatures.filter((f) => {
      const p = f.properties || {};
      const crop = p.predicted_crop;
      const conf = p.confidence ?? 0;
      const taluk = (p.taluk || '').toLowerCase();

      if (!visibleCrops[crop]) return false;
      if (conf < minConfidence) return false;

      if (selectedTaluk !== 'all') {
        const sel = selectedTaluk.toLowerCase();
        if (!taluk.includes(sel) && !sel.includes(taluk)) {
          return false;
        }
      }
      return true;
    });
  }, [allFeatures, visibleCrops, minConfidence, selectedTaluk]);

  // Dynamically compute real statistics reflecting active filters and taluk selection
  const dynamicStatistics = useMemo(() => {
    if (!geojsonData || allFeatures.length === 0) {
      return statistics;
    }

    let totalAreaHa = 0;
    let sumConf = 0;
    const cropMap = {
      Paddy: { count: 0, areaHa: 0, sumConf: 0 },
      Banana: { count: 0, areaHa: 0, sumConf: 0 },
      Other: { count: 0, areaHa: 0, sumConf: 0 }
    };

    filteredFeatures.forEach((f) => {
      const p = f.properties || {};
      const crop = p.predicted_crop || 'Other';
      const ha = Number(p.area_ha || (p.area_m2 ? p.area_m2 / 10000 : 0)) || 0;
      const conf = Number(p.confidence) || 0;

      totalAreaHa += ha;
      sumConf += conf;

      if (!cropMap[crop]) {
        cropMap[crop] = { count: 0, areaHa: 0, sumConf: 0 };
      }
      cropMap[crop].count += 1;
      cropMap[crop].areaHa += ha;
      cropMap[crop].sumConf += conf;
    });

    const totalCount = filteredFeatures.length;
    const meanConf = totalCount > 0 ? (sumConf / totalCount) : 0;
    const totalAreaAcres = totalAreaHa * 2.47105;
    const totalAreaSqKm = totalAreaHa / 100;

    // Study area geographic boundary from official AOI: Ambasamudram (122.14 km²), Cheranmahadevi (118.51 km²), Total (240.65 km²)
    let aoiKm2 = 240.65;
    if (selectedTaluk.toLowerCase().includes('ambasamudram')) {
      aoiKm2 = 122.14;
    } else if (selectedTaluk.toLowerCase().includes('cheranmahadevi')) {
      aoiKm2 = 118.51;
    }

    const cropDist = {};
    ['Paddy', 'Banana', 'Other'].forEach((crop) => {
      const item = cropMap[crop] || { count: 0, areaHa: 0, sumConf: 0 };
      const pctArea = totalAreaHa > 0 ? ((item.areaHa / totalAreaHa) * 100) : 0;
      const cMeanConf = item.count > 0 ? (item.sumConf / item.count) : 0;
      cropDist[crop] = {
        parcel_count: item.count,
        area_hectares: Number(item.areaHa.toFixed(2)),
        area_acres: Number((item.areaHa * 2.47105).toFixed(2)),
        area_sq_km: Number((item.areaHa / 100).toFixed(4)),
        percentage_of_total_area: Number(pctArea.toFixed(2)),
        mean_confidence: Number(cMeanConf.toFixed(4))
      };
    });

    return {
      study_area_summary: {
        total_study_area_sq_km: aoiKm2,
        total_study_area_hectares: aoiKm2 * 100,
        total_parcels: totalCount,
        total_parcels_area_hectares: Number(totalAreaHa.toFixed(2)),
        total_parcels_area_acres: Number(totalAreaAcres.toFixed(2)),
        total_parcels_area_sq_km: Number(totalAreaSqKm.toFixed(4)),
        overall_mean_confidence: Number(meanConf.toFixed(4)),
        selected_taluk: selectedTaluk,
        meets_min_area_requirement: aoiKm2 >= 20.0
      },
      crop_distribution: cropDist
    };
  }, [geojsonData, allFeatures, filteredFeatures, selectedTaluk, statistics]);

  const displayedGeojson = useMemo(() => {
    return geojsonData
      ? { ...geojsonData, features: filteredFeatures }
      : null;
  }, [geojsonData, filteredFeatures]);

  return (
    <div className="app-layout">
      {/* Top Header Navigation — White Professional Theme */}
      <header className="top-nav">
        <div className="brand-section">
          <div className="brand-badge">VIT MAPATHON 2026</div>
          <div>
            <h1 className="brand-title">Agricultural Land Parcel & Crop Identification</h1>
            <div className="brand-breadcrumb">
              <span>🇮🇳 India</span>
              <span className="dot">•</span>
              <span style={{ color: '#0284c7' }}>Tamil Nadu</span>
              <span className="dot">•</span>
              <span style={{ color: '#16a34a' }}>Tirunelveli District</span>
              <span className="dot">•</span>
              <span style={{ color: '#b45309', fontWeight: 600 }}>Ambasamudram & Cheranmahadevi Taluks</span>
            </div>
          </div>
        </div>

        <div className="nav-actions">
          <div className="status-indicator">
            <span
              className="status-dot"
              style={{
                backgroundColor: healthInfo?.database?.postgis_connected ? '#16a34a' : '#0284c7',
                boxShadow: `0 0 6px ${healthInfo?.database?.postgis_connected ? '#16a34a' : '#0284c7'}`
              }}
            />
            <span>
              {healthInfo?.database?.postgis_connected ? 'PostGIS Active' : 'Sentinel-2 Engine'}
            </span>
          </div>

          <button
            className="btn-primary"
            onClick={() => setIsMetricsOpen(true)}
          >
            📊 ML Evaluation & Metrics
          </button>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="dashboard-content">
        {/* Left Control Sidebar */}
        <aside className="sidebar-panel">
          <div className="sidebar-scrollable">
            {error && (
              <div style={{ padding: '0.75rem', background: '#fee2e2', border: '1px solid #ef4444', borderRadius: '8px', fontSize: '0.75rem', color: '#b91c1c' }}>
                ⚠️ <strong>API Error:</strong> {error}
              </div>
            )}

            {/* Dynamic Study Area Statistics */}
            <StatisticsCard
              statistics={dynamicStatistics}
              metrics={metrics}
              selectedTaluk={selectedTaluk}
              talukAcreage={talukAcreage}
            />

            {/* Spatial & Crop Filters */}
            <FilterPanel
              visibleCrops={visibleCrops}
              onToggleCrop={handleToggleCrop}
              selectedTaluk={selectedTaluk}
              onSelectTaluk={setSelectedTaluk}
              minConfidence={minConfidence}
              onChangeConfidence={setMinConfidence}
              activeBasemap={activeBasemap}
              onChangeBasemap={setActiveBasemap}
              showPlaces={showPlaces}
              onChangeShowPlaces={setShowPlaces}
              showInfra={showInfra}
              onChangeShowInfra={setShowInfra}
              showLabels={showLabels}
              onChangeShowLabels={setShowLabels}
              statistics={dynamicStatistics}
              displayedCount={filteredFeatures.length}
              totalCount={allFeatures.length}
              onResetFilters={handleResetFilters}
            />

            {/* Selected Parcel Inspector */}
            {selectedParcel && (
              <div className="panel-card">
                <div className="panel-card-title">
                  <span className="panel-title-text">🔍 Cadastral Parcel Inspector</span>
                </div>
                <ParcelPopup parcel={selectedParcel} />
              </div>
            )}
          </div>
        </aside>

        {/* Center / Right Leaflet GIS Map */}
        <main className="map-viewport-wrapper">
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem', animation: 'spin 2s infinite linear' }}>🛰️</div>
                <div style={{ fontWeight: 600, color: '#0f172a' }}>Loading Tirunelveli Sentinel-2 Classified Parcels...</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>Ambasamudram & Cheranmahadevi Taluks</div>
              </div>
            </div>
          ) : (
            <MapView
              geojsonData={displayedGeojson}
              infrastructureData={infrastructureData}
              placesData={placesData}
              activeBasemap={activeBasemap}
              showPlaces={showPlaces}
              showInfra={showInfra}
              showLabels={showLabels}
              selectedTaluk={selectedTaluk}
              selectedParcel={selectedParcel}
              onSelectParcel={setSelectedParcel}
              visibleCrops={visibleCrops}
              minConfidence={minConfidence}
            />
          )}
        </main>
      </div>

      {/* ML Evaluation Modal */}
      <MetricsModal
        isOpen={isMetricsOpen}
        onClose={() => setIsMetricsOpen(false)}
        metrics={metrics}
        featureImportance={featureImportance}
      />
    </div>
  );
}
