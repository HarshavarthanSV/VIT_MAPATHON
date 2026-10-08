import requests
import json
import os

headers = {'User-Agent': 'VIT_Mapathon_Research_Project/1.0'}

# 1. Fetch real settlements (towns, villages)
query_places = """
[out:json][timeout:35];
(
  node["place"~"town|village|suburb|hamlet"](8.60,77.38,8.78,77.62);
);
out body;
"""

# 2. Fetch real roads and river waterways
query_infra = """
[out:json][timeout:35];
(
  way["waterway"~"river|canal|stream"](8.60,77.38,8.78,77.62);
  way["highway"~"primary|secondary|tertiary|trunk"](8.60,77.38,8.78,77.62);
);
out geom;
"""

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Fetching settlements from Overpass API...")
r1 = requests.post("https://overpass-api.de/api/interpreter", data={"data": query_places}, headers=headers, timeout=40)
places = []
if r1.status_code == 200:
    for el in r1.json().get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if name:
            places.append({
                "name": name,
                "place_type": tags.get("place", "village"),
                "lat": el.get("lat"),
                "lon": el.get("lon"),
                "taluk": "Ambasamudram" if el.get("lon") < 77.51 else "Cheranmahadevi",
                "district": "Tirunelveli",
                "state": "Tamil Nadu"
            })
    print(f"Retrieved {len(places)} real settlements.")
    with open(os.path.join(base_dir, "real_places.json"), "w", encoding="utf-8") as f:
        json.dump(places, f, indent=2)

print("Fetching rivers and roads from Overpass API...")
r2 = requests.post("https://overpass-api.de/api/interpreter", data={"data": query_infra}, headers=headers, timeout=40)
infra_features = []
if r2.status_code == 200:
    for el in r2.json().get("elements", []):
        geom = el.get("geometry", [])
        if len(geom) >= 2:
            tags = el.get("tags", {})
            coords = [[pt["lon"], pt["lat"]] for pt in geom]
            is_water = "waterway" in tags
            name = tags.get("name") or tags.get("name:en") or ("Thamirabarani River" if is_water else "State Highway / District Road")
            infra_features.append({
                "type": "Feature",
                "properties": {
                    "id": el.get("id"),
                    "name": name,
                    "category": "waterway" if is_water else "highway",
                    "type": tags.get("waterway") if is_water else tags.get("highway")
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })
    print(f"Retrieved {len(infra_features)} infrastructure line features.")
    infra_geojson = {
        "type": "FeatureCollection",
        "name": "ambasamudram_cheranmahadevi_infrastructure",
        "features": infra_features
    }
    with open(os.path.join(base_dir, "real_infrastructure.geojson"), "w", encoding="utf-8") as f:
        json.dump(infra_geojson, f)

print("Finished fetching real geospatial data.")
