import requests
import json

def test_fetch():
    query_places = """
    [out:json][timeout:30];
    (
      node["place"~"town|village|suburb"](8.62,77.40,8.75,77.60);
      way["waterway"="river"](8.62,77.40,8.75,77.60);
      way["highway"~"primary|secondary|tertiary|trunk"](8.62,77.40,8.75,77.60);
      way["landuse"~"farmland|orchard|allotments|meadow"](8.62,77.40,8.75,77.60);
    );
    out body;
    >;
    out skel qt;
    """
    headers = {
        "User-Agent": "VIT_Mapathon_Research_Project/1.0 (contact: vit_mapathon@edu.in)",
        "Referer": "https://overpass-turbo.eu/"
    }
    mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    for url in mirrors:
        try:
            print(f"Trying mirror {url}...")
            r = requests.post(url, data={"data": query_places}, headers=headers, timeout=25)
            print("Status Code:", r.status_code)
            if r.status_code == 200:
                data = r.json()
                elements = data.get("elements", [])
                print("Total Elements returned from Overpass:", len(elements))
                places = []
                highways = []
                farmlands = []
                for el in elements:
                    tags = el.get("tags", {})
                    if "place" in tags:
                        places.append((tags.get("name"), tags.get("place"), el.get("lat"), el.get("lon")))
                    elif "highway" in tags:
                        highways.append((tags.get("name"), tags.get("highway")))
                    elif "landuse" in tags:
                        farmlands.append((tags.get("name"), tags.get("landuse"), el.get("id")))
                print(f"Places found ({len(places)}):", places[:10])
                print(f"Highways found ({len(highways)}):", [h for h in highways if h[0]][:10])
                print(f"Farmlands found ({len(farmlands)}):", farmlands[:10])
                return data
        except Exception as e:
            print(f"Mirror {url} error: {e}")
    return None

if __name__ == "__main__":
    test_fetch()
