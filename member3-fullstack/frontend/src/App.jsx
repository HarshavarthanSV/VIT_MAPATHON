import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import FilterPanel from './components/FilterPanel';
import StatisticsCard from './components/StatisticsCard';
import ParcelPopup from './components/ParcelPopup';
import MetricsModal from './components/MetricsModal';

export default function App() {
  const [geojsonData, setGeojsonData] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);

  const [visibleCrops, setVisibleCrops] = useState({
    Paddy: true,
    Banana: true,
    Other: true
  });
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [activeBasemap, setActiveBasemap] = useState('satellite');
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all initial data from FastAPI backend
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch parcels, statistics, metrics, and health in parallel
        const [parcelsRes, statsRes, metricsRes, fiRes, healthRes] = await Promise.all([
          fetch('/api/parcels'),
          fetch('/api/statistics'),
          fetch('/api/metrics'),
          fetch('/api/feature-importance').catch(() => null),
          fetch('/api/health').catch(() => null)
        ]);

        if (!parcelsRes.ok) {
          throw new Error(`Failed to fetch parcels: ${parcelsRes.statusText}`);
        }
        if (!statsRes.ok) {
          throw new Error(`Failed to fetch statistics: ${statsRes.statusText}`);
        }

        const parcelsData = await parcelsRes.json();
        const statsData = await statsRes.json();
        const metricsData = metricsRes.ok ? await metricsRes.json() : null;
        const fiData = fiRes && fiRes.ok ? await fiRes.json() : null;
        const healthData = healthRes && healthRes.ok ? await healthRes.json() : null;

        setGeojsonData(parcelsData);
        setStatistics(statsData);
        setMetrics(metricsData);
        setFeatureImportance(fiData);
        setHealthInfo(healthData);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
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
    setMinConfidence(0.0);
  };

  // Compute displayed count
  const allFeatures = geojsonData?.features || [];
  const displayedCount = allFeatures.filter((f) => {
    const crop = f.properties?.predicted_crop;
    const conf = f.properties?.confidence || 0;
    return visibleCrops[crop] && conf >= minConfidence;
  }).length;

  return (
    <div className="app-layout">
      {/* Top Navigation Bar */}
      <header className="top-nav">
        <div className="brand-section">
          <span className="brand-badge">VIT MAPATHON</span>
          <div>
            <h1 className="brand-title">Agricultural Land Parcel & Crop Identification</h1>
            <p className="brand-subtitle">
              Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District (Lat 8.70° N, Lon 77.49° E)
            </p>
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
              {healthInfo?.database?.postgis_connected ? 'PostGIS Active' : 'GeoJSON Engine'}
            </span>
          </div>

          <button
            className="btn-primary"
            onClick={() => setIsMetricsOpen(true)}
          >
            📊 Model Evaluation & Metrics
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="dashboard-content">
        {/* Left Control & Analytics Sidebar */}
        <aside className="sidebar-panel">
          <div className="sidebar-scrollable">
            {error && (
              <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', borderRadius: '8px', fontSize: '0.75rem', color: '#fca5a5' }}>
                ⚠️ <strong>API Warning:</strong> {error}
              </div>
            )}

            {/* Analytics Card */}
            <StatisticsCard
              statistics={statistics}
              metrics={metrics}
            />

            {/* Filter Panel */}
            <FilterPanel
              visibleCrops={visibleCrops}
              onToggleCrop={handleToggleCrop}
              minConfidence={minConfidence}
              onChangeConfidence={setMinConfidence}
              activeBasemap={activeBasemap}
              onChangeBasemap={setActiveBasemap}
              statistics={statistics}
              displayedCount={displayedCount}
              totalCount={allFeatures.length}
              onResetFilters={handleResetFilters}
            />

            {/* Selected Parcel Inspector */}
            {selectedParcel && (
              <div className="panel-card">
                <div className="panel-card-title">
                  <span>🔍 Selected Parcel Inspector</span>
                </div>
                <ParcelPopup parcel={selectedParcel} />
              </div>
            )}
          </div>
        </aside>

        {/* Center / Right Interactive GIS Map */}
        <main className="map-viewport-wrapper">
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
              <div>
                <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem', textAlign: 'center' }}>🛰️</div>
                <div>Loading Sentinel-2 classified parcels...</div>
              </div>
            </div>
          ) : (
            <MapView
              geojsonData={geojsonData}
              activeBasemap={activeBasemap}
              selectedParcel={selectedParcel}
              onSelectParcel={setSelectedParcel}
              visibleCrops={visibleCrops}
              minConfidence={minConfidence}
            />
          )}
        </main>
      </div>

      {/* ML Metrics & Confusion Matrix Modal */}
      <MetricsModal
        isOpen={isMetricsOpen}
        onClose={() => setIsMetricsOpen(false)}
        metrics={metrics}
        featureImportance={featureImportance}
      />
    </div>
  );
}
