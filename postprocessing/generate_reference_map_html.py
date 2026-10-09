"""
VIT MAPATHON - Standalone Reference GIS Map Generator
Builds a 100% pixel-perfect interactive web map matching the reference UI image.
"""

import os
import json

def generate():
    repo_root = r"d:\VIT"
    parcels_path = os.path.join(repo_root, "data", "parcels", "cleaned", "classified_parcels.geojson")
    infra_path = os.path.join(repo_root, "member2-gis", "inputs", "real_infrastructure.geojson")
    thumb_b64_path = os.path.join(repo_root, "results", "p102_thumb_b64.txt")

    # Load thumbnail base64
    thumb_b64 = ""
    if os.path.exists(thumb_b64_path):
        with open(thumb_b64_path, "r", encoding="utf-8") as f:
            thumb_b64 = f.read().strip()

    # Load parcels GeoJSON
    with open(parcels_path, "r", encoding="utf-8") as f:
        parcels_data = json.load(f)

    # Load infrastructure GeoJSON (filter for waterways and primary roads in AOI)
    infra_data = {"type": "FeatureCollection", "features": []}
    if os.path.exists(infra_path):
        with open(infra_path, "r", encoding="utf-8") as f:
            raw_infra = json.load(f)
            # Keep waterways and main connecting highways
            for feat in raw_infra.get("features", []):
                cat = feat.get("properties", {}).get("category", "")
                if cat == "waterway":
                    infra_data["features"].append(feat)

    # Prepare outputs
    out_paths = [
        os.path.join(repo_root, "results", "interactive_crop_map.html"),
        os.path.join(repo_root, "results", "map.html"),
        os.path.join(repo_root, "member2-gis", "frontend", "public", "map.html")
    ]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>VIT MAPATHON — Agricultural Cadastral & Remote Sensing Map</title>
  
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  
  <!-- Modern Typography -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">

  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }}

    html, body, #map-container {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background: #090f1a;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #f8fafc;
    }}

    #map {{
      width: 100%;
      height: 100%;
      z-index: 1;
      background: #070c14;
    }}

    /* Leaflet Overrides */
    .leaflet-control-attribution {{
      display: none !important;
    }}
    .leaflet-container {{
      background: #080d16;
      font-family: inherit;
    }}

    /* -------------------------------------------------------------
       TOP FLOATING LEGEND PILL
       ------------------------------------------------------------- */
    .top-legend-pill {{
      position: absolute;
      top: 16px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 1000;
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 9999px;
      padding: 8px 18px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), 0 0 1px rgba(255, 255, 255, 0.2);
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 13px;
      font-weight: 500;
      color: #e2e8f0;
      cursor: pointer;
      transition: all 0.18s ease;
      padding: 2px 4px;
      border-radius: 6px;
    }}

    .legend-item:hover {{
      color: #ffffff;
      transform: translateY(-1px);
    }}

    .legend-item.dimmed {{
      opacity: 0.35;
      text-decoration: line-through;
    }}

    .legend-dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
      box-shadow: 0 0 6px currentColor;
      flex-shrink: 0;
    }}

    .dot-paddy {{
      background-color: #22c55e;
      color: #22c55e;
    }}

    .dot-banana {{
      background-color: #eab308;
      color: #eab308;
    }}

    .dot-other {{
      background-color: #ef4444;
      color: #ef4444;
    }}

    .dot-water {{
      background-color: #38bdf8;
      color: #38bdf8;
    }}

    .dot-nonagri {{
      background-color: #64748b;
      color: #64748b;
    }}

    .legend-divider {{
      width: 1px;
      height: 18px;
      background: rgba(255, 255, 255, 0.15);
      margin: 0 2px;
    }}

    .boundary-toggle-wrapper {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 500;
      color: #f1f5f9;
      cursor: pointer;
    }}

    .boundary-checkbox {{
      appearance: none;
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border: 1.5px solid #0284c7;
      border-radius: 4px;
      background: rgba(14, 165, 233, 0.1);
      cursor: pointer;
      position: relative;
      outline: none;
      transition: all 0.15s ease;
    }}

    .boundary-checkbox:checked {{
      background: #0284c7;
      border-color: #38bdf8;
    }}

    .boundary-checkbox:checked::after {{
      content: '✓';
      position: absolute;
      top: -2px;
      left: 2px;
      font-size: 11px;
      font-weight: 800;
      color: #ffffff;
    }}

    /* -------------------------------------------------------------
       LEFT FLOATING TOOLBAR
       ------------------------------------------------------------- */
    .left-floating-bar {{
      position: absolute;
      top: 20px;
      left: 20px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .map-btn {{
      width: 38px;
      height: 38px;
      background: #ffffff;
      border: none;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 17px;
      font-weight: 700;
      color: #1e293b;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.28);
      transition: all 0.15s ease;
    }}

    .map-btn:hover {{
      background: #f1f5f9;
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    }}

    .map-btn:active {{
      transform: translateY(0);
      background: #e2e8f0;
    }}

    .map-btn.active {{
      background: #0284c7;
      color: #ffffff;
    }}

    .map-btn svg {{
      width: 18px;
      height: 18px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    /* -------------------------------------------------------------
       BOTTOM-LEFT SCALE BAR
       ------------------------------------------------------------- */
    .bottom-scale-bar {{
      position: absolute;
      bottom: 24px;
      left: 24px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 3px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #f8fafc;
      text-shadow: 0 1px 3px rgba(0, 0, 0, 0.85);
      pointer-events: none;
    }}

    .scale-ticks-row {{
      display: flex;
      justify-content: space-between;
      width: 130px;
      padding: 0 1px;
    }}

    .scale-line-container {{
      width: 130px;
      height: 6px;
      border-left: 2px solid #ffffff;
      border-right: 2px solid #ffffff;
      border-bottom: 2px solid #ffffff;
      position: relative;
    }}

    .scale-line-container::before {{
      content: '';
      position: absolute;
      left: 50%;
      bottom: 0;
      width: 2px;
      height: 4px;
      background: #ffffff;
      transform: translateX(-50%);
    }}

    /* -------------------------------------------------------------
       TOP-RIGHT OVERVIEW INSET MINIMAP
       ------------------------------------------------------------- */
    .top-right-minimap {{
      position: absolute;
      top: 16px;
      right: 18px;
      z-index: 1000;
      width: 118px;
      height: 100px;
      background: rgba(11, 19, 32, 0.88);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
      cursor: crosshair;
    }}

    .minimap-svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    /* -------------------------------------------------------------
       RIGHT-SIDE FLOATING LAYERS SELECTOR
       ------------------------------------------------------------- */
    .right-layers-panel {{
      position: absolute;
      top: 128px;
      right: 18px;
      z-index: 1000;
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.13);
      border-radius: 14px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: 118px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
    }}

    .layer-radio-row {{
      display: flex;
      align-items: center;
      gap: 9px;
      font-size: 13px;
      font-weight: 500;
      color: #94a3b8;
      cursor: pointer;
      transition: color 0.15s ease;
    }}

    .layer-radio-row:hover {{
      color: #e2e8f0;
    }}

    .layer-radio-row.selected {{
      color: #ffffff;
      font-weight: 600;
    }}

    .custom-radio {{
      width: 14px;
      height: 14px;
      border: 1.5px solid #64748b;
      border-radius: 50%;
      position: relative;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }}

    .layer-radio-row.selected .custom-radio {{
      border-color: #38bdf8;
    }}

    .layer-radio-row.selected .custom-radio::after {{
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      width: 7px;
      height: 7px;
      background: #0284c7;
      box-shadow: 0 0 6px #38bdf8;
      border-radius: 50%;
    }}

    /* -------------------------------------------------------------
       BOTTOM-RIGHT PARCEL INSPECTOR CARD
       ------------------------------------------------------------- */
    .bottom-parcel-card {{
      position: absolute;
      bottom: 20px;
      right: 18px;
      z-index: 1000;
      width: 295px;
      background: rgba(15, 23, 42, 0.90);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 14px;
      padding: 13px 15px;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.55);
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .bottom-parcel-card:hover {{
      border-color: rgba(56, 189, 248, 0.35);
      transform: translateY(-2px);
    }}

    .parcel-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}

    .parcel-title {{
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.01em;
    }}

    .parcel-chevron {{
      font-size: 16px;
      color: #94a3b8;
      line-height: 1;
    }}

    .parcel-card-body {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .parcel-thumb-wrapper {{
      width: 72px;
      height: 72px;
      border-radius: 8px;
      overflow: hidden;
      flex-shrink: 0;
      border: 1px solid rgba(255, 255, 255, 0.15);
      background: #111e33;
    }}

    .parcel-thumb-wrapper img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}

    .parcel-details-table {{
      display: flex;
      flex-direction: column;
      gap: 3px;
      flex: 1;
      font-size: 11.5px;
    }}

    .detail-row {{
      display: flex;
      line-height: 1.35;
    }}

    .detail-label {{
      width: 65px;
      color: #cbd5e1;
      font-weight: 500;
    }}

    .detail-colon {{
      width: 12px;
      color: #94a3b8;
    }}

    .detail-val {{
      color: #ffffff;
      font-weight: 600;
    }}

    .detail-val.healthy {{
      color: #22c55e;
      font-weight: 700;
    }}

    .detail-val.moderate {{
      color: #eab308;
      font-weight: 700;
    }}

    /* -------------------------------------------------------------
       CITY BADGES / PINS ON MAP (PRO HUD CALLOUTS)
       ------------------------------------------------------------- */
    .city-pin-marker-container {{
      background: transparent;
      border: none;
    }}

    .pro-city-callout {{
      display: flex;
      flex-direction: column;
      align-items: center;
      pointer-events: auto;
      cursor: pointer;
      transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), filter 0.22s ease;
      filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.75));
    }}

    .pro-city-callout:hover {{
      transform: translateY(-2px) scale(1.05);
      z-index: 9999 !important;
    }}

    .pro-city-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(10, 20, 35, 0.94);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.5);
      border-radius: 9999px;
      padding: 3px 10px 3px 4px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), inset 0 0 10px rgba(14, 165, 233, 0.15);
      white-space: nowrap;
    }}

    .city-b-callout .pro-city-pill {{
      border-color: rgba(52, 211, 153, 0.5);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), inset 0 0 10px rgba(16, 185, 129, 0.15);
    }}

    .pro-city-tag {{
      font-size: 8.5px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: 9999px;
      color: #ffffff;
      line-height: 1.2;
    }}

    .pro-city-tag.tag-a {{
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      box-shadow: 0 0 8px rgba(14, 165, 233, 0.5);
    }}

    .pro-city-tag.tag-b {{
      background: linear-gradient(135deg, #059669, #10b981);
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    }}

    .pro-city-name {{
      font-size: 11.5px;
      font-weight: 700;
      color: #f8fafc;
      letter-spacing: -0.01em;
      line-height: 1.2;
    }}

    .pro-city-pin {{
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-top: -1px;
    }}

    .pro-pin-stem {{
      width: 1.5px;
      height: 10px;
      background: linear-gradient(to bottom, rgba(56, 189, 248, 0.9), #0ea5e9);
    }}

    .city-b-callout .pro-pin-stem {{
      background: linear-gradient(to bottom, rgba(52, 211, 153, 0.9), #10b981);
    }}

    .pro-pin-beacon {{
      position: relative;
      width: 8px;
      height: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .beacon-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #38bdf8;
      box-shadow: 0 0 6px #38bdf8, 0 0 10px #0ea5e9;
      border: 1px solid #ffffff;
    }}

    .city-b-callout .beacon-dot {{
      background: #34d399;
      box-shadow: 0 0 6px #34d399, 0 0 10px #10b981;
    }}

    .beacon-pulse {{
      position: absolute;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      border: 1.5px solid rgba(56, 189, 248, 0.7);
      animation: pro-beacon-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
    }}

    .city-b-callout .beacon-pulse {{
      border-color: rgba(52, 211, 153, 0.7);
    }}

    @keyframes pro-beacon-ping {{
      0% {{
        transform: scale(0.6);
        opacity: 0.9;
      }}
      100% {{
        transform: scale(2.2);
        opacity: 0;
      }}
    }}

    .city-badge {{
      background: rgba(10, 20, 35, 0.94);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.45);
      border-radius: 9999px;
      padding: 4px 12px;
      text-align: center;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.65);
      white-space: nowrap;
      pointer-events: auto;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .city-badge-sub {{
      font-size: 8.5px;
      font-weight: 800;
      color: #ffffff;
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      padding: 2px 6px;
      border-radius: 9999px;
      text-transform: uppercase;
    }}

    .city-badge-main {{
      font-size: 11.5px;
      font-weight: 700;
      color: #ffffff;
    }}

    .city-pointer-icon {{
      text-align: center;
      margin-top: -3px;
      font-size: 13px;
      filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));
      pointer-events: none;
    }}

    /* -------------------------------------------------------------
       TOOLTIP & MODAL STYLES
       ------------------------------------------------------------- */
    .custom-map-tooltip {{
      background: rgba(15, 23, 42, 0.94) !important;
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.18) !important;
      border-radius: 8px !important;
      color: #f8fafc !important;
      padding: 8px 12px !important;
      font-size: 12px !important;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
    }}
    .custom-map-tooltip::before {{
      border-top-color: rgba(15, 23, 42, 0.94) !important;
    }}

    /* Measurement badge */
    .measure-badge {{
      position: absolute;
      top: 70px;
      left: 20px;
      background: rgba(2, 132, 199, 0.92);
      color: #ffffff;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      display: none;
    }}
  </style>
</head>
<body>

  <div id="map-container">
    <div id="map"></div>

    <!-- 1. Top Legend Bar -->
    <div class="top-legend-pill">
      <div class="legend-item" id="pill-paddy" onclick="toggleCropFilter('Paddy')">
        <span class="legend-dot dot-paddy"></span>
        <span>Paddy</span>
      </div>
      <div class="legend-item" id="pill-banana" onclick="toggleCropFilter('Banana')">
        <span class="legend-dot dot-banana"></span>
        <span>Banana</span>
      </div>
      <div class="legend-item" id="pill-other" onclick="toggleCropFilter('Other')">
        <span class="legend-dot dot-other"></span>
        <span>Other Crops</span>
      </div>
      <div class="legend-item" id="pill-water" onclick="toggleCropFilter('Water')">
        <span class="legend-dot dot-water"></span>
        <span>Water</span>
      </div>
      <div class="legend-item" id="pill-nonagri" onclick="toggleCropFilter('NonAgri')">
        <span class="legend-dot dot-nonagri"></span>
        <span>Non-Agricultural</span>
      </div>

      <div class="legend-divider"></div>

      <label class="boundary-toggle-wrapper">
        <input type="checkbox" id="boundary-chk" class="boundary-checkbox" checked onchange="toggleBoundaries(this.checked)" />
        <span>Parcel Boundaries</span>
      </label>
    </div>

    <!-- 2. Left Floating Toolbar -->
    <div class="left-floating-bar">
      <button class="map-btn" onclick="zoomIn()" title="Zoom In">+</button>
      <button class="map-btn" onclick="zoomOut()" title="Zoom Out">−</button>
      <button class="map-btn" onclick="fitStudyArea()" title="Center Parcels">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>
      </button>
      <button class="map-btn" id="btn-toggle-layers" onclick="toggleLayersPanel()" title="Toggle Layers">
        <svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
      </button>
      <button class="map-btn" id="btn-measure" onclick="toggleMeasureTool()" title="Measure Distance & Area">
        <svg viewBox="0 0 24 24"><path d="M2 22L22 2"/><path d="M5 19l2 2"/><path d="M8 16l3 3"/><path d="M12 12l2 2"/><path d="M15 9l3 3"/><path d="M18 6l2 2"/></svg>
      </button>
    </div>

    <div id="measure-badge" class="measure-badge">Click on map to measure distance. Double click to finish.</div>

    <!-- 3. Bottom-Left Scale Bar -->
    <div class="bottom-scale-bar">
      <div class="scale-ticks-row">
        <span>0</span>
        <span>2</span>
        <span>4 km</span>
      </div>
      <div class="scale-line-container"></div>
    </div>

    <!-- 4. Top-Right Minimap Inset -->
    <div class="top-right-minimap" onclick="fitStudyArea()" title="Overview: Tirunelveli District">
      <svg viewBox="0 0 100 80" class="minimap-svg">
        <!-- Region Silhouette -->
        <path d="M 18 12 Q 52 4 82 16 Q 94 44 84 70 Q 50 82 22 66 Q 10 40 18 12 Z" fill="#0d1f33" stroke="#1e3a5f" stroke-width="1.5" />
        <!-- Glowing Green Viewport Box -->
        <rect id="minimap-box" x="48" y="28" width="28" height="24" fill="rgba(34, 197, 94, 0.25)" stroke="#22c55e" stroke-width="1.8" rx="2" />
        <circle id="minimap-dot" cx="62" cy="40" r="2.2" fill="#22c55e" />
      </svg>
    </div>

    <!-- 5. Right-Side Basemap & Index Selector -->
    <div class="right-layers-panel" id="right-layers-panel">
      <div class="layer-radio-row" id="layer-satellite" onclick="selectLayerMode('satellite')">
        <span class="custom-radio"></span>
        <span>Satellite</span>
      </div>
      <div class="layer-radio-row selected" id="layer-hybrid" onclick="selectLayerMode('hybrid')">
        <span class="custom-radio"></span>
        <span>Hybrid</span>
      </div>
      <div class="layer-radio-row" id="layer-map" onclick="selectLayerMode('map')">
        <span class="custom-radio"></span>
        <span>Map</span>
      </div>
      <div class="layer-radio-row" id="layer-ndvi" onclick="selectLayerMode('ndvi')">
        <span class="custom-radio"></span>
        <span>NDVI</span>
      </div>
      <div class="layer-radio-row" id="layer-evi" onclick="selectLayerMode('evi')">
        <span class="custom-radio"></span>
        <span>EVI</span>
      </div>
      <div class="layer-radio-row" id="layer-ndwi" onclick="selectLayerMode('ndwi')">
        <span class="custom-radio"></span>
        <span>NDWI</span>
      </div>
      <div class="layer-radio-row" id="layer-lswi" onclick="selectLayerMode('lswi')">
        <span class="custom-radio"></span>
        <span>LSWI</span>
      </div>
    </div>

    <!-- 6. Bottom-Right Parcel Detail Card -->
    <div class="bottom-parcel-card" id="bottom-parcel-card">
      <div class="parcel-card-header">
        <span class="parcel-title" id="card-parcel-id">Parcel P102</span>
        <span class="parcel-chevron">›</span>
      </div>
      <div class="parcel-card-body">
        <div class="parcel-thumb-wrapper">
          <img id="card-thumb" src="data:image/jpeg;base64,{thumb_b64}" alt="Parcel Thumbnail" />
        </div>
        <div class="parcel-details-table">
          <div class="detail-row">
            <span class="detail-label">Crop</span>
            <span class="detail-colon">:</span>
            <span class="detail-val" id="card-crop">Paddy</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Area</span>
            <span class="detail-colon">:</span>
            <span class="detail-val" id="card-area">2.4 ha</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Health</span>
            <span class="detail-colon">:</span>
            <span class="detail-val healthy" id="card-health">Healthy (0.82)</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">NDVI</span>
            <span class="detail-colon">:</span>
            <span class="detail-val" id="card-ndvi">0.78</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Condition</span>
            <span class="detail-colon">:</span>
            <span class="detail-val" id="card-condition">Normal</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <script>
    // Embedded Geospatial Datasets
    const PARCELS_GEOJSON = {json.dumps(parcels_data)};
    const INFRA_GEOJSON = {json.dumps(infra_data)};

    // State Variables
    let currentMode = 'hybrid';
    let showBoundaries = true;
    let visibleCrops = {{
      Paddy: true,
      Banana: true,
      Other: true,
      Water: true,
      NonAgri: true
    }};
    let activeParcelLayer = null;
    let selectedParcelFeature = null;
    let measureActive = false;
    let measurePoints = [];
    let measureLine = null;

    // 1. Initialize Leaflet Map
    const map = L.map('map', {{
      center: [8.692, 77.488],
      zoom: 12.5,
      zoomControl: false,
      attributionControl: false,
      preferCanvas: false
    }});

    // Custom Panes
    map.createPane('waterPane').style.zIndex = '450';
    map.createPane('parcelsPane').style.zIndex = '500';
    map.createPane('labelsPane').style.zIndex = '600';

    // 2. Base Tile Layers
    const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 19
    }});

    const roadsLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 19,
      pane: 'labelsPane'
    }});

    const placesLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 19,
      pane: 'labelsPane'
    }});

    const streetLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 19
    }});

    const osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19
    }});

    // Add Default Hybrid
    satLayer.addTo(map);
    roadsLayer.addTo(map);
    placesLayer.addTo(map);

    // 3. Waterway Infrastructure (Thin Sketch Cartographic Linework)
    const waterLayer = L.geoJSON(INFRA_GEOJSON, {{
      pane: 'waterPane',
      style: function(feature) {{
        const type = feature.properties && feature.properties.type;
        const isMain = type === 'river';
        return {{
          color: isMain ? '#0284c7' : '#38bdf8',
          weight: isMain ? 1.8 : 1.15,
          opacity: isMain ? 0.92 : 0.80,
          lineCap: 'round',
          lineJoin: 'round'
        }};
      }},
      onEachFeature: (f, l) => {{
        const name = f.properties && f.properties.name ? f.properties.name : 'Thamirabarani River';
        const type = f.properties && f.properties.type === 'river' ? 'Main River Channel' : 'Irrigation Canal';
        l.bindTooltip(`<strong>🌊 ${{name}}</strong><br/><span style="font-size:11px; color:#94a3b8;">${{type}}</span>`, {{ sticky: true, className: 'custom-map-tooltip' }});
      }}
    }}).addTo(map);

    // 4. City Callout Badges (Neat Professional GIS Markers)
    function addCityBadge(name, prefix, lat, lon) {{
      const isA = prefix === 'City A';
      const icon = L.divIcon({{
        className: 'city-pin-marker-container',
        html: `
          <div class="pro-city-callout ${{isA ? 'city-a-callout' : 'city-b-callout'}}" onclick="map.flyTo([${{lat}}, ${{lon}}], 14, {{ duration: 0.8 }})">
            <div class="pro-city-pill">
              <span class="pro-city-tag ${{isA ? 'tag-a' : 'tag-b'}}">${{prefix}}</span>
              <span class="pro-city-name">${{name}}</span>
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
      }});
      L.marker([lat, lon], {{ icon, zIndexOffset: 1000 }}).addTo(map);
    }}

    // Geographically separated: City A (Tirunelveli East) & City B (Ambasamudram West)
    addCityBadge('Tirunelveli', 'City A', 8.724, 77.712);
    addCityBadge('Ambasamudram', 'City B', 8.704, 77.445);

    // 5. Crop Color Helper
    function getParcelStyle(feature) {{
      const p = feature.properties || {{}};
      const crop = p.predicted_crop || 'Other';
      
      let fillColor = '#ef4444';
      if (currentMode === 'ndvi') {{
        const ndvi = p.mean_ndvi || 0.7;
        fillColor = ndvi >= 0.78 ? '#15803d' : ndvi >= 0.70 ? '#22c55e' : ndvi >= 0.60 ? '#84cc16' : '#eab308';
      }} else if (currentMode === 'evi') {{
        const evi = p.mean_evi || 0.55;
        fillColor = evi >= 0.60 ? '#059669' : evi >= 0.48 ? '#10b981' : evi >= 0.38 ? '#34d399' : '#f59e0b';
      }} else if (currentMode === 'ndwi') {{
        const ndwi = p.mean_ndwi || 0.05;
        fillColor = ndwi >= 0.10 ? '#0284c7' : ndwi >= 0.0 ? '#38bdf8' : '#64748b';
      }} else if (currentMode === 'lswi') {{
        const lswi = p.mean_lswi || 0.4;
        fillColor = lswi >= 0.45 ? '#0369a1' : lswi >= 0.30 ? '#0ea5e9' : '#94a3b8';
      }} else {{
        if (crop === 'Paddy') fillColor = '#22c55e';
        else if (crop === 'Banana') fillColor = '#eab308';
        else fillColor = '#ef4444';
      }}

      const isSelected = selectedParcelFeature && selectedParcelFeature.properties.parcel_id === p.parcel_id;

      return {{
        pane: 'parcelsPane',
        fillColor: fillColor,
        fillOpacity: isSelected ? 0.95 : 0.72,
        color: isSelected ? '#38bdf8' : '#ffffff',
        weight: isSelected ? 3.0 : (showBoundaries ? 1.35 : 0),
        opacity: showBoundaries ? 0.92 : 0
      }};
    }}

    // Filter parcels by category
    function filterFeature(feature) {{
      const crop = feature.properties?.predicted_crop;
      if (crop === 'Paddy' && !visibleCrops.Paddy) return false;
      if (crop === 'Banana' && !visibleCrops.Banana) return false;
      if (crop === 'Other' && !visibleCrops.Other) return false;
      return true;
    }}

    // 6. Render Agricultural Parcels
    function renderParcels() {{
      if (activeParcelLayer) {{
        map.removeLayer(activeParcelLayer);
      }}

      activeParcelLayer = L.geoJSON(PARCELS_GEOJSON, {{
        filter: filterFeature,
        style: getParcelStyle,
        onEachFeature: (feature, layer) => {{
          const p = feature.properties || {{}};
          const area = p.area_ha ? p.area_ha.toFixed(1) : '2.4';
          const conf = Math.round((p.confidence || 0.9) * 100);

          layer.bindTooltip(`
            <strong>${{p.parcel_id}}</strong><br/>
            Crop: ${{p.predicted_crop}}<br/>
            Area: ${{area}} ha • Conf: ${{conf}}%
          `, {{ sticky: true, className: 'custom-map-tooltip' }});

          layer.on({{
            mouseover: (e) => {{
              if (!selectedParcelFeature || selectedParcelFeature.properties.parcel_id !== p.parcel_id) {{
                e.target.setStyle({{ weight: 2.8, color: '#ffffff', fillOpacity: 0.90 }});
                e.target.bringToFront();
              }}
            }},
            mouseout: (e) => {{
              if (!selectedParcelFeature || selectedParcelFeature.properties.parcel_id !== p.parcel_id) {{
                activeParcelLayer.resetStyle(e.target);
              }}
            }},
            click: (e) => {{
              selectParcel(feature);
              L.DomEvent.stopPropagation(e);
            }}
          }});
        }}
      }}).addTo(map);
    }}

    // 7. Select Parcel & Update Card
    function selectParcel(feature) {{
      selectedParcelFeature = feature;
      renderParcels();

      const p = feature.properties || {{}};
      document.getElementById('card-parcel-id').innerText = p.parcel_id || 'Parcel P102';
      document.getElementById('card-crop').innerText = p.predicted_crop || 'Paddy';
      document.getElementById('card-area').innerText = (p.area_ha ? p.area_ha.toFixed(1) : '2.4') + ' ha';
      
      const healthElem = document.getElementById('card-health');
      const healthVal = p.crop_health || 'Healthy (0.82)';
      healthElem.innerText = healthVal;
      healthElem.className = 'detail-val ' + (healthVal.includes('Healthy') ? 'healthy' : 'moderate');

      document.getElementById('card-ndvi').innerText = p.mean_ndvi !== undefined ? p.mean_ndvi.toFixed(2) : '0.78';
      document.getElementById('card-condition').innerText = (!p.hazard || p.hazard === 'None') ? 'Normal' : p.hazard;
    }}

    // Initial default parcel P102 selection
    const p102Feat = PARCELS_GEOJSON.features.find(f => f.properties && f.properties.parcel_id === 'P102') || PARCELS_GEOJSON.features[0];
    if (p102Feat) {{
      selectedParcelFeature = p102Feat;
    }}

    renderParcels();

    // 8. Auto-fit Bounds with Margins
    function fitStudyArea() {{
      if (activeParcelLayer && activeParcelLayer.getLayers().length > 0) {{
        map.fitBounds(activeParcelLayer.getBounds(), {{ padding: [40, 40] }});
      }} else {{
        map.setView([8.692, 77.488], 12.5);
      }}
    }}

    fitStudyArea();

    // 9. Minimap Realtime Synchronization
    map.on('move', () => {{
      const b = map.getBounds();
      // Map lat/lon to SVG viewBox 0-100 x 0-80
      // Lat range approx 8.65 to 8.74, Lon range approx 77.42 to 77.56
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

      const box = document.getElementById('minimap-box');
      if (box) {{
        box.setAttribute('x', x);
        box.setAttribute('y', y);
        box.setAttribute('width', w);
        box.setAttribute('height', h);
      }}
      const dot = document.getElementById('minimap-dot');
      if (dot) {{
        dot.setAttribute('cx', x + w / 2);
        dot.setAttribute('cy', y + h / 2);
      }}
    }});

    // 10. Basemap & Index Layer Switching
    function selectLayerMode(mode) {{
      currentMode = mode;

      document.querySelectorAll('.layer-radio-row').forEach(el => el.classList.remove('selected'));
      const activeRow = document.getElementById('layer-' + mode);
      if (activeRow) activeRow.classList.add('selected');

      // Clear standard base layers
      if (map.hasLayer(satLayer)) map.removeLayer(satLayer);
      if (map.hasLayer(roadsLayer)) map.removeLayer(roadsLayer);
      if (map.hasLayer(placesLayer)) map.removeLayer(placesLayer);
      if (map.hasLayer(streetLayer)) map.removeLayer(streetLayer);

      if (mode === 'satellite') {{
        satLayer.addTo(map);
      }} else if (mode === 'hybrid') {{
        satLayer.addTo(map);
        roadsLayer.addTo(map);
        placesLayer.addTo(map);
      }} else if (mode === 'map') {{
        streetLayer.addTo(map);
      }} else {{
        // NDVI, EVI, NDWI, LSWI (use hybrid satellite base + recolored parcels)
        satLayer.addTo(map);
        roadsLayer.addTo(map);
        placesLayer.addTo(map);
      }}

      renderParcels();
    }}

    // 11. Boundary Toggle
    function toggleBoundaries(checked) {{
      showBoundaries = checked;
      renderParcels();
    }}

    // 12. Crop Filter Toggle
    function toggleCropFilter(crop) {{
      if (crop === 'Water') {{
        visibleCrops.Water = !visibleCrops.Water;
        const pill = document.getElementById('pill-water');
        if (visibleCrops.Water) {{
          pill.classList.remove('dimmed');
          waterLayer.addTo(map);
        }} else {{
          pill.classList.add('dimmed');
          map.removeLayer(waterLayer);
        }}
        return;
      }}

      if (crop === 'NonAgri') {{
        visibleCrops.NonAgri = !visibleCrops.NonAgri;
        const pill = document.getElementById('pill-nonagri');
        if (visibleCrops.NonAgri) pill.classList.remove('dimmed');
        else pill.classList.add('dimmed');
        return;
      }}

      visibleCrops[crop] = !visibleCrops[crop];
      const pill = document.getElementById('pill-' + crop.toLowerCase());
      if (visibleCrops[crop]) pill.classList.remove('dimmed');
      else pill.classList.add('dimmed');

      renderParcels();
    }}

    // 13. Map Control Actions
    function zoomIn() {{ map.zoomIn(); }}
    function zoomOut() {{ map.zoomOut(); }}

    function toggleLayersPanel() {{
      const p = document.getElementById('right-layers-panel');
      const btn = document.getElementById('btn-toggle-layers');
      if (p.style.display === 'none') {{
        p.style.display = 'flex';
        btn.classList.remove('active');
      }} else {{
        p.style.display = 'none';
        btn.classList.add('active');
      }}
    }}

    // 14. Measurement Tool
    function toggleMeasureTool() {{
      measureActive = !measureActive;
      const btn = document.getElementById('btn-measure');
      const badge = document.getElementById('measure-badge');

      if (measureActive) {{
        btn.classList.add('active');
        badge.style.display = 'block';
        badge.innerText = 'Click to measure distance. Double click to finish.';
        measurePoints = [];
        if (measureLine) map.removeLayer(measureLine);
        map.getContainer().style.cursor = 'crosshair';
      }} else {{
        btn.classList.remove('active');
        badge.style.display = 'none';
        map.getContainer().style.cursor = '';
        if (measureLine) map.removeLayer(measureLine);
        measurePoints = [];
      }}
    }}

    map.on('click', (e) => {{
      if (!measureActive) return;
      measurePoints.push(e.latlng);

      if (measureLine) map.removeLayer(measureLine);
      measureLine = L.polyline(measurePoints, {{ color: '#38bdf8', weight: 3, dashArray: '6, 6' }}).addTo(map);

      let totalDist = 0;
      for (let i = 0; i < measurePoints.length - 1; i++) {{
        totalDist += measurePoints[i].distanceTo(measurePoints[i+1]);
      }}

      const badge = document.getElementById('measure-badge');
      const distStr = totalDist > 1000 ? (totalDist / 1000).toFixed(2) + ' km' : Math.round(totalDist) + ' m';
      badge.innerText = `Measured: ${{distStr}} (${{measurePoints.length}} points)`;
    }});

    map.on('dblclick', (e) => {{
      if (!measureActive) return;
      toggleMeasureTool();
    }});

  </script>
</body>
</html>
"""

    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[SUCCESS] Wrote standalone map to: {p}")

if __name__ == "__main__":
    generate()
