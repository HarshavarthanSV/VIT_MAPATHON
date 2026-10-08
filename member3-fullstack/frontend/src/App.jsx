import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import FilterPanel from './components/FilterPanel';
import StatisticsCard from './components/StatisticsCard';
import ParcelPopup from './components/ParcelPopup';
import MetricsModal from './components/MetricsModal';

export default function App() {
  const [geojsonData, setGeojsonData] = useState(null);
  const [infrastructureData, setInfrastructureData] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);

  const [visibleCrops, setVisibleCrops] = useState({
    Paddy: true,
    Banana: true,
    Other: true
  });
  const [selectedTaluk, setSelectedTaluk] = useState('all');
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [activeBasemap, setActiveBasemap] = useState('satellite');
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all GIS and ML layers from backend
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [parcelsRes, statsRes, metricsRes, fiRes, healthRes, infraRes] = await Promise.all([
          fetch('/api/parcels'),
          fetch('/api/statistics'),
          fetch('/api/metrics'),
          fetch('/api/feature-importance').catch(() => null),
          fetch('/api/health').catch(() => null),
          fetch('/api/infrastructure').catch(() => null)
        ]);

        if (!parcelsRes.ok) throw new Error(`Parcels fetch failed: ${parcelsRes.statusText}`);
        if (!statsRes.ok) throw new Error(`Statistics fetch failed: ${statsRes.statusText}`);

        const parcels = await parcelsRes.json();
        const stats = await statsRes.json();
        const metricsData = metricsRes.ok ? await metricsRes.json() : null;
        const fiData = fiRes && fiRes.ok ? await fiRes.json() : null;
        const health = healthRes && healthRes.ok ? await healthRes.json() : null;
        const infra = infraRes && infraRes.ok ? await infraRes.json() : null;

        setGeojsonData(parcels);
        setStatistics(stats);
        setMetrics(metricsData);
        setFeatureImportance(fiData);
        setHealthInfo(health);
        setInfrastructureData(infra);
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
  const filteredFeatures = allFeatures.filter((f) => {
    const crop = f.properties?.predicted_crop;
    const conf = f.properties?.confidence || 0;
    const taluk = f.properties?.taluk;

    if (!visibleCrops[crop]) return false;
    if (conf < minConfidence) return false;
    if (selectedTaluk !== 'all' && taluk !== selectedTaluk) return false;
    return true;
  });

  const displayedGeojson = geojsonData
    ? { ...geojsonData, features: filteredFeatures }
    : null;

  return (
    <div className="app-layout">
      {/* Top Header Navigation */}
      <header className="top-nav">
        <div className="brand-section">
          <div className="brand-badge">VIT MAPATHON</div>
          <div>
            <h1 className="brand-title">Agricultural Land Parcel & Crop Identification</h1>
            <div className="brand-breadcrumb">
              <span>🇮🇳 India</span>
              <span className="dot">•</span>
              <span style={{ color: '#38bdf8' }}>Tamil Nadu</span>
              <span className="dot">•</span>
              <span style={{ color: '#22c55e' }}>Tirunelveli District</span>
              <span className="dot">•</span>
              <span style={{ color: '#facc15' }}>Ambasamudram & Cheranmahadevi Taluks</span>
            </div>
          </div>
        </div>

        <div className="nav-actions">
          <div className="status-indicator">
            <span
              className="status-dot"
              style={{
                backgroundColor: healthInfo?.database?.postgis_connected ? '#22c55e' : '#38bdf8',
                boxShadow: `0 0 8px ${healthInfo?.database?.postgis_connected ? '#22c55e' : '#38bdf8'}`
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
              <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', borderRadius: '8px', fontSize: '0.75rem', color: '#fca5a5' }}>
                ⚠️ <strong>API Warning:</strong> {error}
              </div>
            )}

            {/* Study Area Statistics */}
            <StatisticsCard
              statistics={statistics}
              metrics={metrics}
            />

            {/* Spatial & Crop Filters */}
            <FilterPanel
              visibleCrops={visibleCrops}
              onToggleCrop={handleToggleCrop}
              selectedTaluk={selectedTaluk}
              onSelectTaluk={setSelectedTaluk}
              minConfidence={minConfidence}
              onChangeConfidence={setMinConfidence}
              statistics={statistics}
              displayedCount={filteredFeatures.length}
              totalCount={allFeatures.length}
              onResetFilters={handleResetFilters}
            />

            {/* Selected Parcel Inspector */}
            {selectedParcel && (
              <div className="panel-card">
                <div className="panel-card-title">
                  <span>🔍 Cadastral Parcel Inspector</span>
                </div>
                <ParcelPopup parcel={selectedParcel} />
              </div>
            )}
          </div>
        </aside>

        {/* Center / Right Leaflet GIS Map */}
        <main className="map-viewport-wrapper">
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem', animation: 'spin 2s infinite linear' }}>🛰️</div>
                <div style={{ fontWeight: 600, color: '#f8fafc' }}>Loading Tirunelveli Sentinel-2 Classified Parcels...</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>Ambasamudram & Cheranmahadevi Taluks</div>
              </div>
            </div>
          ) : (
            <MapView
              geojsonData={displayedGeojson}
              infrastructureData={infrastructureData}
              activeBasemap={activeBasemap}
              onChangeBasemap={setActiveBasemap}
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
