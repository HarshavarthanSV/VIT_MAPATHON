"""
VIT MAPATHON — Standalone Open-Source Interactive GIS Map Generator
Uses Folium / Leaflet to generate a 100% interactive standalone HTML map
for Ambasamudram & Cheranmahadevi Taluks with all 293 classified parcels.
"""

import os
import json
import folium
from folium import plugins
import geopandas as gpd

def generate_interactive_map():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parcels_path = os.path.join(repo_root, "data", "parcels", "cleaned", "classified_parcels.geojson")
    aoi_path = os.path.join(repo_root, "data", "aoi", "study_area.geojson")
    output_html = os.path.join(repo_root, "results", "interactive_crop_map.html")
    
    # Load parcels GeoJSON
    with open(parcels_path, "r", encoding="utf-8") as f:
        parcels_data = json.load(f)

    # Calculate center from parcel bounds
    feats = parcels_data.get("features", [])
    all_lats, all_lons = [], []
    for feat in feats:
        geom = feat["geometry"]
        coords = geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]
        for c in coords:
            all_lons.append(c[0])
            all_lats.append(c[1])

    center_lat = sum(all_lats) / len(all_lats) if all_lats else 8.695
    center_lon = sum(all_lons) / len(all_lons) if all_lons else 77.502

    # Initialize Folium Map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        control_scale=True,
        prefer_canvas=False
    )

    # 1. Add Basemaps
    # Satellite Imagery (Esri)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ Esri Satellite (Hybrid)",
        max_zoom=19,
        overlay=False,
        control=True
    ).add_to(m)

    # OpenStreetMap
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ OpenStreetMap",
        overlay=False,
        control=True
    ).add_to(m)

    # CartoDB Voyager
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="CartoDB Voyager",
        name="🚗 CartoDB Voyager (Street)",
        overlay=False,
        control=True
    ).add_to(m)

    # CartoDB Dark Matter
    folium.TileLayer(
        tiles="CartoDB dark_matter",
        name="🌙 CartoDB Dark Matter",
        overlay=False,
        control=True
    ).add_to(m)

    # 2. Add AOI Taluk Boundaries (if present)
    if os.path.exists(aoi_path):
        with open(aoi_path, "r", encoding="utf-8") as f:
            aoi_data = json.load(f)

        def aoi_style(feature):
            return {
                "fillColor": "#38bdf8",
                "fillOpacity": 0.05,
                "color": "#0284c7",
                "weight": 2.5,
                "dashArray": "6, 6"
            }

        aoi_layer = folium.GeoJson(
            aoi_data,
            name="📍 Taluk Boundaries (AOI)",
            style_function=aoi_style,
            tooltip=folium.GeoJsonTooltip(
                fields=["taluk_name", "area_km2"] if "taluk_name" in aoi_data["features"][0]["properties"] else list(aoi_data["features"][0]["properties"].keys()),
                aliases=["Taluk:", "Area (km²):"] if "taluk_name" in aoi_data["features"][0]["properties"] else None
            )
        )
        aoi_layer.add_to(m)

    # 3. Create Feature Groups for each crop
    paddy_group = folium.FeatureGroup(name="🌾 Paddy Parcels (123 fields • 77.03 ha)", show=True)
    banana_group = folium.FeatureGroup(name="🍌 Banana Parcels (109 fields • 54.41 ha)", show=True)
    other_group = folium.FeatureGroup(name="🌿 Other / Fallow (61 fields • 40.21 ha)", show=True)

    crop_colors = {
        "paddy": {"fill": "#22c55e", "stroke": "#15803d", "label": "Paddy (Rice)"},
        "banana": {"fill": "#eab308", "stroke": "#a16207", "label": "Banana (Plantation)"},
        "other": {"fill": "#a855f7", "stroke": "#6b21a8", "label": "Other / Fallow"}
    }

    for feat in feats:
        props = feat.get("properties", {})
        crop = str(props.get("predicted_crop", "Other")).lower()
        cfg = crop_colors.get(crop, crop_colors["other"])

        conf_pct = round(float(props.get("confidence", 0.0)) * 100, 1)
        area_ha = round(float(props.get("area_ha", 0.0)), 2)
        area_acres = round(area_ha * 2.47105, 2)
        parcel_id = props.get("parcel_id", "N/A")
        taluk = props.get("taluk", "Ambasamudram / Cheranmahadevi")

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px; padding: 4px;">
            <div style="font-size: 14px; font-weight: bold; color: {cfg['stroke']}; border-bottom: 2px solid {cfg['fill']}; padding-bottom: 4px; margin-bottom: 6px;">
                {cfg['label']}
            </div>
            <table style="width: 100%; font-size: 12px; line-height: 1.5;">
                <tr><td><b>Parcel ID:</b></td><td>{parcel_id}</td></tr>
                <tr><td><b>Taluk:</b></td><td>{taluk}</td></tr>
                <tr><td><b>Confidence:</b></td><td><span style="color: {cfg['stroke']}; font-weight: bold;">{conf_pct}%</span></td></tr>
                <tr><td><b>Area (ha):</b></td><td>{area_ha} ha</td></tr>
                <tr><td><b>Area (acres):</b></td><td>{area_acres} acres</td></tr>
                <tr><td><b>Paddy Prob:</b></td><td>{round(float(props.get('prob_paddy', 0.0))*100, 1)}%</td></tr>
                <tr><td><b>Banana Prob:</b></td><td>{round(float(props.get('prob_banana', 0.0))*100, 1)}%</td></tr>
                <tr><td><b>Other Prob:</b></td><td>{round(float(props.get('prob_other', 0.0))*100, 1)}%</td></tr>
            </table>
        </div>
        """

        tooltip_text = f"<b>{parcel_id}</b> ({taluk})<br>{cfg['label']}<br>Confidence: {conf_pct}% • Area: {area_ha} ha"

        geojson_elem = folium.GeoJson(
            feat,
            style_function=lambda x, fill=cfg["fill"], stroke=cfg["stroke"]: {
                "fillColor": fill,
                "color": stroke,
                "weight": 2.2,
                "fillOpacity": 0.70,
                "opacity": 0.95
            },
            highlight_function=lambda x: {
                "fillColor": "#ffffff",
                "color": "#ffffff",
                "weight": 3.5,
                "fillOpacity": 0.90
            },
            tooltip=folium.Tooltip(tooltip_text, sticky=True),
            popup=folium.Popup(popup_html, max_width=300)
        )

        if "paddy" in crop:
            geojson_elem.add_to(paddy_group)
        elif "banana" in crop:
            geojson_elem.add_to(banana_group)
        else:
            geojson_elem.add_to(other_group)

    paddy_group.add_to(m)
    banana_group.add_to(m)
    other_group.add_to(m)

    # 4. Add Town markers
    towns = [
        {"name": "Ambasamudram", "lat": 8.7082, "lon": 77.4383, "color": "blue"},
        {"name": "Cheranmahadevi", "lat": 8.6793, "lon": 77.5617, "color": "blue"},
        {"name": "Kallidaikurichi", "lat": 8.6809, "lon": 77.4651, "color": "darkblue"},
        {"name": "Veeravanallur", "lat": 8.6895, "lon": 77.5222, "color": "darkblue"},
        {"name": "Pattamadai", "lat": 8.6674, "lon": 77.5844, "color": "darkblue"}
    ]
    towns_group = folium.FeatureGroup(name="📍 Towns & Villages", show=True)
    for town in towns:
        folium.Marker(
            [town["lat"], town["lon"]],
            popup=f"<b>{town['name']}</b>",
            tooltip=town["name"],
            icon=folium.Icon(color=town["color"], icon="info-sign")
        ).add_to(towns_group)
    towns_group.add_to(m)

    # 5. Add Interactive Controls
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MeasureControl(position="bottomleft", primary_length_unit="meters", primary_area_unit="hectares").add_to(m)

    # Fit bounds to all parcels
    min_lat, max_lat = min(all_lats), max(all_lats)
    min_lon, max_lon = min(all_lons), max(all_lons)
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(20, 20))

    # Save HTML
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    m.save(output_html)
    print(f"[SUCCESS] Standalone interactive map generated at: {output_html}")
    return output_html

if __name__ == "__main__":
    generate_interactive_map()
