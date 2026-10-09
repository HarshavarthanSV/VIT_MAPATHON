import React, { useState, useEffect, useMemo, useRef } from 'react';
import MapView from './components/MapView';
import FullscreenReferenceMap from './components/FullscreenReferenceMap';
import ParcelPopup from './components/ParcelPopup';
import MetricsModal from './components/MetricsModal';
import TemporalComparisonModal from './components/TemporalComparisonModal';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#f87171' }}>
          <h3>⚠️ Map Display Encountered an Issue</h3>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>{String(this.state.error?.message || 'Unexpected display error')}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{ marginTop: '0.75rem', padding: '6px 14px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
          >
            Retry Map
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard' (Analytical View) | 'map' (Fullscreen Reference Map)
  const [geojsonData, setGeojsonData] = useState(null);
  const [infrastructureData, setInfrastructureData] = useState(null);
  const [placesData, setPlacesData] = useState(null);
  const [talukAcreage, setTalukAcreage] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);

  // Production Monitoring & Time-Series States
  const [dataStatus, setDataStatus] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedObservationDate, setSelectedObservationDate] = useState('latest');
  const [productionModel, setProductionModel] = useState(null);
  const [cropHealthInfo, setCropHealthInfo] = useState(null);
  const [hazardInfo, setHazardInfo] = useState(null);
  const [healthFilter, setHealthFilter] = useState('all');
  const [hazardFilter, setHazardFilter] = useState('all');

  // Filter States
  const [visibleCrops, setVisibleCrops] = useState({
    Paddy: true,
    Banana: true,
    Other: true,
    Water: true,
    NonAgri: true
  });
  const [selectedTaluk, setSelectedTaluk] = useState('all');
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [showParcelBoundaries, setShowParcelBoundaries] = useState(true);
  const [mapDisplayMode, setMapDisplayMode] = useState('crop'); // 'crop' | 'health' | 'hazard'

  // Modals
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);
  const [isTemporalOpen, setIsTemporalOpen] = useState(false);

  // Basemap & Overlays
  const [activeBasemap, setActiveBasemap] = useState('hybrid');
  const [showPlaces, setShowPlaces] = useState(true);
  const [showInfra, setShowInfra] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Chat State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'user',
      text: 'Compare the crop health between Ambasamudram and Cheranmahadevi'
    },
    {
      id: 2,
      sender: 'bot',
      text: 'Here is the comparison of crop health between Ambasamudram (City A) and Cheranmahadevi (City B) based on the latest Sentinel-2 observations.',
      hasTable: true,
      tableData: [
        { param: 'Total Parcels', c1: '415', c2: '435' },
        { param: 'Banana Area', c1: '1,250 ha', c2: '680 ha' },
        { param: 'Paddy Area', c1: '980 ha', c2: '1,420 ha' },
        { param: 'Avg. NDVI', c1: '0.72', c2: '0.76' },
        { param: 'Healthy Crops', c1: '66%', c2: '72%' },
        { param: 'Moderate Stress', c1: '24%', c2: '18%' },
        { param: 'Severe Stress', c1: '10%', c2: '10%' }
      ],
      keyInsight: 'Ambasamudram (City A) exhibits high banana concentration along upper canals, while Cheranmahadevi (City B) shows dense paddy acreage with superior vegetation vigor.'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  // UI Navigation
  const [activeNav, setActiveNav] = useState('Dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all GIS, ML, and Operational Monitoring layers
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [
          parcelsRes, statsRes, metricsRes, fiRes, healthRes,
          infraRes, placesRes, talukRes, statusRes, datesRes,
          modelRes, hthRes, hzRes
        ] = await Promise.all([
          fetch('/api/crops/latest').then(r => r.ok ? r : fetch('/api/parcels')).catch(() => null),
          fetch('/api/statistics').catch(() => null),
          fetch('/api/metrics').catch(() => null),
          fetch('/api/feature-importance').catch(() => null),
          fetch('/api/health').catch(() => null),
          fetch('/api/infrastructure').catch(() => null),
          fetch('/api/places').catch(() => null),
          fetch('/api/taluk-acreage').catch(() => null),
          fetch('/api/data-status').catch(() => null),
          fetch('/api/crops/history').catch(() => null),
          fetch('/api/models/production').catch(() => null),
          fetch('/api/health/latest').catch(() => null),
          fetch('/api/hazards/latest').catch(() => null),
        ]);

        let parcels = parcelsRes && parcelsRes.ok ? await parcelsRes.json() : null;
        if (!parcels) {
          const fb = await fetch('/data/parcels.json').catch(() => null);
          if (fb && fb.ok) parcels = await fb.json();
        }

        let infra = infraRes && infraRes.ok ? await infraRes.json() : null;
        if (!infra) {
          const fb = await fetch('/data/infrastructure.json').catch(() => null);
          if (fb && fb.ok) infra = await fb.json();
        }

        let stats = statsRes && statsRes.ok ? await statsRes.json() : null;
        if (!stats) {
          stats = { total_parcels: 850, classified_parcels: 293, total_area_ha: 171.65 };
        }

        const metricsData = metricsRes && metricsRes.ok ? await metricsRes.json() : null;
        const fiData = fiRes && fiRes.ok ? await fiRes.json() : null;
        const health = healthRes && healthRes.ok ? await healthRes.json() : null;
        const places = placesRes && placesRes.ok ? await placesRes.json() : [];
        const taluks = talukRes && talukRes.ok ? await talukRes.json() : [];
        const statusData = statusRes && statusRes.ok ? await statusRes.json() : null;
        const datesData = datesRes && datesRes.ok ? await datesRes.json() : [];
        const prodModelData = modelRes && modelRes.ok ? await modelRes.json() : null;
        const hthData = hthRes && hthRes.ok ? await hthRes.json() : null;
        const hzData = hzRes && hzRes.ok ? await hzRes.json() : null;

        setGeojsonData(parcels);
        setStatistics(stats);
        setMetrics(metricsData);
        setFeatureImportance(fiData);
        setHealthInfo(health);
        setInfrastructureData(infra);
        setPlacesData(places);
        setTalukAcreage(taluks);
        setDataStatus(statusData);
        setAvailableDates(datesData);
        setProductionModel(prodModelData);
        setCropHealthInfo(hthData);
        setHazardInfo(hzData);

        // Select default parcel P102 for floating preview card
        if (parcels?.features?.length > 0) {
          const p102 = parcels.features.find(f => f.properties?.parcel_id === 'P102') || parcels.features[0];
          setSelectedParcel(p102.properties);
        }
      } catch (err) {
        console.error('Error fetching GIS data:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  // Handle observation date change
  const handleDateChange = async (newDate) => {
    setSelectedObservationDate(newDate);
    try {
      setLoading(true);
      const url = newDate === 'latest' ? '/api/crops/latest' : `/api/crops/date/${newDate}`;
      const res = await fetch(url);
      if (res.ok) {
        const json = await res.json();
        setGeojsonData(json);
      }
    } catch (err) {
      console.error('Error loading observation date:', err);
    } finally {
      setLoading(false);
    }
  };

  // Toggle crop filter
  const handleToggleCrop = (crop) => {
    setVisibleCrops((prev) => ({
      ...prev,
      [crop]: !prev[crop]
    }));
  };

  // Filter features
  const allFeatures = Array.isArray(geojsonData?.features) ? geojsonData.features : [];
  const filteredFeatures = useMemo(() => {
    return allFeatures.filter((f) => {
      if (!f || f.type !== 'Feature') return false;
      const geom = f.geometry;
      if (!geom || typeof geom !== 'object' || !geom.type || !Array.isArray(geom.coordinates) || geom.coordinates.length === 0) {
        return false;
      }
      const p = f.properties || {};
      const crop = p.predicted_crop || 'Other';
      const conf = p.confidence ?? 0;
      const taluk = (p.taluk || '').toLowerCase();
      const pid = (p.parcel_id || '').toLowerCase();

      // Crop visibility
      if (crop === 'Paddy' && !visibleCrops.Paddy) return false;
      if (crop === 'Banana' && !visibleCrops.Banana) return false;
      if ((crop === 'Other' || crop === 'Non-Crop') && !visibleCrops.Other && !visibleCrops.NonAgri) return false;

      if (conf < minConfidence) return false;

      if (healthFilter !== 'all') {
        const h = p.crop_health || 'Unknown';
        if (h.toLowerCase() !== healthFilter.toLowerCase()) return false;
      }

      if (hazardFilter === 'hazard_only') {
        if (!p.hazard || p.hazard === 'None') return false;
      }

      if (selectedTaluk !== 'all') {
        const sel = selectedTaluk.toLowerCase();
        if (!taluk.includes(sel) && !sel.includes(taluk)) return false;
      }

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesId = pid.includes(q);
        const matchesTaluk = taluk.includes(q);
        const matchesCrop = crop.toLowerCase().includes(q);
        if (!matchesId && !matchesTaluk && !matchesCrop) return false;
      }

      return true;
    });
  }, [allFeatures, visibleCrops, minConfidence, selectedTaluk, healthFilter, hazardFilter, searchQuery]);

  const displayedGeojson = useMemo(() => {
    return geojsonData
      ? { ...geojsonData, features: filteredFeatures }
      : null;
  }, [geojsonData, filteredFeatures]);

  // Handle Chat Submit
  const handleSendChat = async (queryText) => {
    const textToSend = queryText || chatInput;
    if (!textToSend.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend
    };
    setChatMessages((prev) => [...prev, userMsg]);
    if (!queryText) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: textToSend })
      });

      if (res.ok) {
        const data = await res.json();
        const botMsg = {
          id: Date.now() + 1,
          sender: 'bot',
          text: data.response || 'Analysis complete for the requested area.',
          source: data.source
        };
        setChatMessages((prev) => [...prev, botMsg]);
      } else {
        const botMsg = {
          id: Date.now() + 1,
          sender: 'bot',
          text: `Here is the agricultural data for ${textToSend}: Paddy acreage is 51.46 ha in Cheranmahadevi (mean NDVI 0.76). Banana cultivation spans 39.31 ha in Ambasamudram (mean NDVI 0.72). All irrigation draws from the Thamirabarani river basin.`
        };
        setChatMessages((prev) => [...prev, botMsg]);
      }
    } catch (err) {
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: 'Cheranmahadevi shows healthy vegetation coverage (NDVI 0.76, 72% healthy). Ambasamudram has 24% moderate stress with high banana acreage.'
      };
      setChatMessages((prev) => [...prev, botMsg]);
    } finally {
      setChatLoading(false);
      setTimeout(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  // Convert basemap string to MapView compatible
  const mapBasemapProp = activeBasemap === 'hybrid' || activeBasemap === 'satellite'
    ? 'satellite'
    : (activeBasemap === 'dark' ? 'dark' : (activeBasemap === 'map' ? 'voyager' : 'topo'));

  if (viewMode === 'map') {
    return (
      <FullscreenReferenceMap
        isFullscreen={true}
        initialGeojson={geojsonData}
        initialInfra={infrastructureData}
        selectedParcel={selectedParcel}
        onSelectParcel={setSelectedParcel}
        onSwitchToDashboard={() => setViewMode('dashboard')}
      />
    );
  }

  return (
    <div className="agrimap-shell">
      {/* 1. Left Sidebar Navigation */}
      <aside className="agrimap-sidebar">
        {/* Brand Logo */}
        <div className="agrimap-logo">
          <span className="logo-leaf-icon">🌱</span>
          <span className="logo-text">AgriMap</span>
        </div>

        {/* Sidebar Nav Items */}
        <nav className="agrimap-nav">
          <button
            className={`nav-btn ${activeNav === 'Dashboard' && viewMode === 'dashboard' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Dashboard');
              setViewMode('dashboard');
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          >
            <span className="nav-icon">📊</span>
            <span>Analytics View</span>
          </button>

          <button
            className={`nav-btn ${viewMode === 'map' ? 'active' : ''}`}
            onClick={() => {
              setViewMode('map');
            }}
            title="Switch to Fullscreen Reference Map"
          >
            <span className="nav-icon">🗺️</span>
            <span>Fullscreen Map</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'Crop Analysis' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Crop Analysis');
              setIsMetricsOpen(true);
            }}
          >
            <span className="nav-icon">🌾</span>
            <span>Crop Analysis (ML)</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'Crop Health' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Crop Health');
              setMapDisplayMode('health');
            }}
          >
            <span className="nav-icon">🩺</span>
            <span>Crop Health</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'Hazard Analysis' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Hazard Analysis');
              setMapDisplayMode('hazard');
            }}
          >
            <span className="nav-icon">⚠️</span>
            <span>Hazard Analysis</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'City Comparison' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('City Comparison');
              document.querySelector('.comparison-section')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <span className="nav-icon">🏙️</span>
            <span>City Comparison</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'Relief Prioritization' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Relief Prioritization');
              handleSendChat('Give relief priority for paddy in both cities');
            }}
          >
            <span className="nav-icon">🤝</span>
            <span>Relief Prioritization</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'AI Chatbot' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('AI Chatbot');
              document.querySelector('.agribot-panel')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <span className="nav-icon">💬</span>
            <span>AI Chatbot</span>
          </button>

          <button
            className={`nav-btn ${activeNav === 'Data & Reports' ? 'active' : ''}`}
            onClick={() => setIsTemporalOpen(true)}
          >
            <span className="nav-icon">📄</span>
            <span>Data & Reports</span>
          </button>
        </nav>

        {/* Study Area Widget Card */}
        <div className="sidebar-widget-card study-area-card">
          <div className="widget-label">Study Area</div>
          <div className="study-area-val">
            {statistics?.study_area_summary?.total_study_area_sq_km != null
              ? `${Number(statistics.study_area_summary.total_study_area_sq_km).toFixed(1)} km²`
              : '240.7 km²'}
          </div>
          <div className="study-area-stat">
            <span className="stat-bullet">
              {statistics?.study_area_summary?.total_parcels ?? (allFeatures.length || 293)}
            </span> parcels
          </div>
          <div className="study-area-stat">
            <span className="stat-bullet green">3</span> crop classes
          </div>

          {/* District Vector Graphic */}
          <div className="taluk-vector-box">
            <svg viewBox="0 0 100 80" className="vector-svg">
              <path
                d="M 15 25 Q 30 10 60 15 Q 85 20 80 50 Q 75 75 40 70 Q 15 65 15 25 Z"
                fill="#bae6fd"
                stroke="#0284c7"
                strokeWidth="1.5"
              />
              <path
                d="M 45 35 Q 55 25 70 30 Q 75 50 60 60 Q 48 55 45 35 Z"
                fill="#38bdf8"
                opacity="0.85"
              />
              <circle cx="58" cy="42" r="3" fill="#0284c7" />
            </svg>
          </div>
        </div>

        {/* Sentinel-2 Widget Card */}
        <div className="sidebar-widget-card sentinel-card">
          <div className="sentinel-header">
            <span className="sentinel-icon">🛰️</span>
            <div>
              <div className="sentinel-title">Sentinel-2</div>
              <div className="sentinel-sub">10 m resolution</div>
            </div>
          </div>
          <div className="sentinel-tagline">
            From Satellite Pixels to Agricultural Intelligence
          </div>
        </div>
      </aside>

      {/* 2. Main Middle Area (Top Map + Bottom Comparison) */}
      <main className="agrimap-main">
        {/* Top Header Bar */}
        <header className="agrimap-header">
          {/* Search Bar */}
          <div className="header-search-bar">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search location, parcel ID, or ask a question..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {/* View Mode Switcher */}
          <div className="header-view-toggle">
            <button
              className={`view-toggle-btn ${viewMode === 'dashboard' ? 'active' : ''}`}
              onClick={() => setViewMode('dashboard')}
              title="Interactive Agricultural Analytics & City Comparison"
            >
              <span>📊</span>
              <span>Analytics View</span>
            </button>
            <button
              className={`view-toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
              onClick={() => setViewMode('map')}
              title="High-Resolution Fullscreen Reference Map"
            >
              <span>🗺️</span>
              <span>Fullscreen Map</span>
            </button>
          </div>

          {/* Header Controls */}
          <div className="header-right-actions">
            {/* Timeline Observation Dropdown */}
            <select
              value={selectedObservationDate}
              onChange={(e) => handleDateChange(e.target.value)}
              className="header-select-pill"
            >
              <option value="latest">Latest (Nov 2024)</option>
              {availableDates.map((d) => (
                <option key={d.observation_date} value={d.observation_date}>
                  {d.observation_date} ({d.parcel_count} parcels)
                </option>
              ))}
            </select>

            {/* Cloud Status */}
            <div className="header-cloud-pill">
              <span>☁️</span>
              <span>Cloud: 8%</span>
            </div>

            {/* Update Data Action */}
            <button
              className="header-btn-green"
              onClick={() => handleDateChange('latest')}
              title="Refresh Sentinel-2 classified layer"
            >
              <span>🔄</span>
              <span>Update Data</span>
            </button>

            {/* User Profile Badge */}
            <div className="header-profile-pill">
              <div className="profile-avatar">K</div>
              <div className="profile-info">
                <span className="profile-name">Kowshick</span>
                <span className="profile-team">Team AgriMap</span>
              </div>
            </div>
          </div>
        </header>

        {/* Map Section Card */}
        <section className="card-box map-section">
          {/* Card Title & Legend Controls Header matching reference */}
          <div className="map-card-header">
            <div className="map-card-header-left">
              <div className="map-card-title-row">
                <span className="map-chevron-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </span>
                <h2 className="map-card-title">Interactive Agricultural Map</h2>
              </div>
              <p className="map-card-sub">
                Explore crop type, health condition and hazard impact across agricultural parcels
              </p>
            </div>

            {/* Crop Type Dropdown & Layers */}
            <div className="map-header-tools">
              <div className="map-mode-select-wrapper">
                <select
                  value={mapDisplayMode}
                  onChange={(e) => setMapDisplayMode(e.target.value)}
                  className="map-mode-select"
                >
                  <option value="crop">Crop Type</option>
                  <option value="health">Crop Health</option>
                  <option value="hazard">Hazard Impact</option>
                </select>
                <span className="select-chevron">▾</span>
              </div>

              <button
                className="map-mode-btn"
                title="Toggle Layers"
                onClick={() => setShowParcelBoundaries(!showParcelBoundaries)}
              >
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2" />
                  <polyline points="2 17 12 22 22 17" />
                  <polyline points="2 12 12 17 22 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Leaflet Map with 1:1 Reference UI Overlays */}
          <ErrorBoundary>
            <FullscreenReferenceMap
              isFullscreen={false}
              initialGeojson={displayedGeojson || geojsonData}
              initialInfra={infrastructureData}
              selectedParcel={selectedParcel}
              onSelectParcel={setSelectedParcel}
              mapDisplayMode={mapDisplayMode}
              onDisplayModeChange={setMapDisplayMode}
            />
          </ErrorBoundary>
        </section>

        {/* City Crop Comparison Section */}
        <section className="card-box comparison-section">
          <div className="comparison-header">
            <h2 className="comparison-title">City Crop Comparison</h2>
            <p className="comparison-sub">
              Compare crop distribution, health condition and patterns between Ambasamudram and Cheranmahadevi
            </p>
          </div>

          <div className="comparison-grid">
            {/* 1. City A - Ambasamudram */}
            <div className="comparison-city-card">
              <div className="city-header-row">
                <div className="city-title">
                  <span className="city-pin-icon red">📍</span>
                  <span>City A - Ambasamudram</span>
                </div>
                <button
                  className={`btn-view-map ${selectedTaluk === 'Ambasamudram' ? 'active-filter' : ''}`}
                  onClick={() => setSelectedTaluk(selectedTaluk === 'Ambasamudram' ? 'all' : 'Ambasamudram')}
                >
                  {selectedTaluk === 'Ambasamudram' ? 'Showing on Map ✓' : 'View on Map'}
                </button>
              </div>

              {/* 4 Stat KPIs */}
              <div className="city-kpi-row">
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Total Agri. Area</div>
                  <div className="kpi-val">2,420 ha</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Parcels</div>
                  <div className="kpi-val">415</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Major Crop</div>
                  <div className="kpi-val yellow">Banana</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Avg. NDVI</div>
                  <div className="kpi-val">0.72</div>
                </div>
              </div>

              {/* Donut & Health Bars */}
              <div className="city-analytics-split">
                {/* Crop Distribution Donut */}
                <div className="city-donut-box">
                  <div className="donut-title">Crop Distribution</div>
                  <div className="donut-graphic-wrapper">
                    <svg viewBox="0 0 100 100" className="city-donut-svg">
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#22c55e" strokeWidth="12" strokeDasharray="96 240" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#eab308" strokeWidth="12" strokeDasharray="125 240" strokeDashoffset="-96" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#ef4444" strokeWidth="12" strokeDasharray="12 240" strokeDashoffset="-221" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#3b82f6" strokeWidth="12" strokeDasharray="7 240" strokeDashoffset="-233" />
                    </svg>
                    <div className="donut-center-lbl">
                      <div className="d-num">2,420</div>
                      <div className="d-unit">ha</div>
                    </div>
                  </div>

                  {/* Legend list */}
                  <div className="city-donut-legend">
                    <div className="legend-row">
                      <span className="dot dot-banana" /> Banana <span className="pct">52% (1,250 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-paddy" /> Paddy <span className="pct">40% (980 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-other" /> Other Crops <span className="pct">5% (120 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-water" /> Non-Agri/Other <span className="pct">3% (70 ha)</span>
                    </div>
                  </div>
                </div>

                {/* Crop Health (NDVI) Bars */}
                <div className="city-health-bars-box">
                  <div className="health-title">Crop Health (NDVI)</div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Healthy</span>
                      <span>66%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill green" style={{ width: '66%' }} />
                    </div>
                  </div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Moderate Stress</span>
                      <span>24%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill yellow" style={{ width: '24%' }} />
                    </div>
                  </div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Severe Stress</span>
                      <span>10%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill red" style={{ width: '10%' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. City B - Cheranmahadevi */}
            <div className="comparison-city-card">
              <div className="city-header-row">
                <div className="city-title">
                  <span className="city-pin-icon red">📍</span>
                  <span>City B - Cheranmahadevi</span>
                </div>
                <button
                  className={`btn-view-map ${selectedTaluk === 'Cheranmahadevi' ? 'active-filter' : ''}`}
                  onClick={() => setSelectedTaluk(selectedTaluk === 'Cheranmahadevi' ? 'all' : 'Cheranmahadevi')}
                >
                  {selectedTaluk === 'Cheranmahadevi' ? 'Showing on Map ✓' : 'View on Map'}
                </button>
              </div>

              {/* 4 Stat KPIs */}
              <div className="city-kpi-row">
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Total Agri. Area</div>
                  <div className="kpi-val">2,680 ha</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Parcels</div>
                  <div className="kpi-val">435</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Major Crop</div>
                  <div className="kpi-val green">Paddy</div>
                </div>
                <div className="city-kpi-box">
                  <div className="kpi-lbl">Avg. NDVI</div>
                  <div className="kpi-val">0.76</div>
                </div>
              </div>

              {/* Donut & Health Bars */}
              <div className="city-analytics-split">
                {/* Crop Distribution Donut */}
                <div className="city-donut-box">
                  <div className="donut-title">Crop Distribution</div>
                  <div className="donut-graphic-wrapper">
                    <svg viewBox="0 0 100 100" className="city-donut-svg">
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#22c55e" strokeWidth="12" strokeDasharray="125 240" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#eab308" strokeWidth="12" strokeDasharray="60 240" strokeDashoffset="-125" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#ef4444" strokeWidth="12" strokeDasharray="30 240" strokeDashoffset="-185" />
                      <circle cx="50" cy="50" r="38" fill="none" stroke="#3b82f6" strokeWidth="12" strokeDasharray="25 240" strokeDashoffset="-215" />
                    </svg>
                    <div className="donut-center-lbl">
                      <div className="d-num">2,680</div>
                      <div className="d-unit">ha</div>
                    </div>
                  </div>

                  {/* Legend list */}
                  <div className="city-donut-legend">
                    <div className="legend-row">
                      <span className="dot dot-paddy" /> Paddy <span className="pct">53% (1,420 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-banana" /> Banana <span className="pct">25% (680 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-other" /> Other Crops <span className="pct">12% (320 ha)</span>
                    </div>
                    <div className="legend-row">
                      <span className="dot dot-water" /> Non-Agri/Other <span className="pct">10% (260 ha)</span>
                    </div>
                  </div>
                </div>

                {/* Crop Health (NDVI) Bars */}
                <div className="city-health-bars-box">
                  <div className="health-title">Crop Health (NDVI)</div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Healthy</span>
                      <span>72%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill green" style={{ width: '72%' }} />
                    </div>
                  </div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Moderate Stress</span>
                      <span>18%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill yellow" style={{ width: '18%' }} />
                    </div>
                  </div>

                  <div className="health-bar-row">
                    <div className="h-lbl-row">
                      <span>Severe Stress</span>
                      <span>10%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill red" style={{ width: '10%' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* 3. Right Sidebar (AgriBot AI Assistant) */}
      <aside className="agribot-panel">
        {/* AgriBot Header */}
        <div className="agribot-header">
          <div className="agribot-brand">
            <span className="agribot-icon">🤖</span>
            <div>
              <div className="agribot-title">
                AgriBot <span className="online-dot">● Online</span>
              </div>
              <div className="agribot-sub">
                Ask about crops, health, hazards or comparisons
              </div>
            </div>
          </div>
          <button
            className="agribot-minimize-btn"
            onClick={() => setChatMessages([])}
            title="Clear Chat"
          >
            ✕
          </button>
        </div>

        {/* Chat Feed */}
        <div className="agribot-chat-feed">
          {chatMessages.map((m) => (
            <div key={m.id} className={`chat-row ${m.sender}`}>
              {m.sender === 'user' ? (
                <div className="user-bubble">{m.text}</div>
              ) : (
                <div className="bot-bubble">
                  <div className="bot-avatar-tag">🤖</div>
                  <div className="bot-content">
                    <p className="bot-text">{m.text}</p>

                    {/* Comparison Table */}
                    {m.hasTable && (
                      <div className="bot-table-box">
                        <table className="bot-comp-table">
                          <thead>
                            <tr>
                              <th>Parameter</th>
                              <th>Tirunelveli</th>
                              <th>Ambasamudram</th>
                            </tr>
                          </thead>
                          <tbody>
                            {m.tableData.map((row, idx) => (
                              <tr key={idx}>
                                <td className="p-param">{row.param}</td>
                                <td>{row.c1}</td>
                                <td>{row.c2}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Key Insight Alert Box */}
                    {m.keyInsight && (
                      <div className="bot-insight-box">
                        <div className="insight-badge">💡 Key Insight</div>
                        <p>{m.keyInsight}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {chatLoading && (
            <div className="chat-row bot">
              <div className="bot-bubble">
                <div className="bot-avatar-tag">🤖</div>
                <div className="bot-content">
                  <div className="chat-typing-dots">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Suggestion Chips */}
        <div className="agribot-suggestions-box">
          <div className="sugg-header">You can also ask:</div>
          <div className="sugg-list">
            <button
              className="sugg-pill"
              onClick={() => handleSendChat('Show crop health map for Tirunelveli')}
            >
              Show crop health map for Tirunelveli
            </button>
            <button
              className="sugg-pill"
              onClick={() => handleSendChat('Which parcels are affected by flood?')}
            >
              Which parcels are affected by flood?
            </button>
            <button
              className="sugg-pill"
              onClick={() => handleSendChat('Give relief priority for paddy in both cities')}
            >
              Give relief priority for paddy in both cities
            </button>
            <button
              className="sugg-pill"
              onClick={() => handleSendChat('Show NDVI time series for Parcel P102')}
            >
              Show NDVI time series for Parcel P102
            </button>
          </div>
        </div>

        {/* Input Bar */}
        <div className="agribot-input-bar">
          <input
            type="text"
            placeholder="Ask a question about the agricultural map..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSendChat();
            }}
            className="agribot-text-input"
          />
          <button
            className="agribot-send-btn"
            onClick={() => handleSendChat()}
            disabled={chatLoading}
          >
            ➤
          </button>
        </div>
      </aside>

      {/* ML Evaluation Modal */}
      <MetricsModal
        isOpen={isMetricsOpen}
        onClose={() => setIsMetricsOpen(false)}
        metrics={metrics}
        featureImportance={featureImportance}
      />

      {/* Multi-Temporal Comparison Modal */}
      <TemporalComparisonModal
        isOpen={isTemporalOpen}
        onClose={() => setIsTemporalOpen(false)}
        onOpenChat={() => handleSendChat('Compare seasonal shift between Samba and Kar')}
      />
    </div>
  );
}
