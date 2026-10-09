"""
VIT MAPATHON — Member 1 (AI / ML & Backend Systems)
FastAPI Backend Application Entrypoint
Provides REST endpoints for Agricultural Land Parcel & Crop Identification in Tirunelveli District.
"""

import os
import sys
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from fastapi import HTTPException

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db_connection, is_db_connected, resolve_artifact_path
from routers import parcels, statistics, layers, analysis, production_monitoring

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes PostGIS connection pool with graceful fallback check."""
    connected = init_db_connection()
    if connected:
        print("[DATABASE] PostGIS spatial database connected and verified.")
    else:
        print("[DATABASE] Running with high-performance local GeoJSON/JSON artifacts fallback.")
    yield

app = FastAPI(
    title="VIT MAPATHON — Agricultural GIS Dashboard API",
    description="Spatial API for Ambasamudram & Cheranmahadevi Taluks Agricultural Land Parcel & Crop Classification.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local and production web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(parcels.router)
app.include_router(statistics.router)
app.include_router(layers.router)
app.include_router(analysis.router)
app.include_router(production_monitoring.router)


@app.get("/", include_in_schema=False)
def root():
    """Redirects to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/map", include_in_schema=True, tags=["map"])
def get_interactive_map():
    """
    Returns standalone full-screen interactive open-source Folium/Leaflet map
    displaying all 293 classified agricultural parcels with layer controls and tooltips.
    """
    repo_root = os.path.dirname(os.path.dirname(backend_dir))
    map_path = os.path.join(repo_root, "results", "interactive_crop_map.html")
    if os.path.exists(map_path):
        return FileResponse(map_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Interactive map file not found.")


@app.get("/api/health")
def health_check():
    """Returns system status, active database backend, and dynamic study area metadata."""
    geojson_path = resolve_artifact_path("classified_parcels.geojson")
    stats_path = resolve_artifact_path("crop_statistics.json")
    
    study_name = "Ambasamudram & Cheranmahadevi Taluks"
    center = [8.70, 77.49]
    target_crops = ["Paddy", "Banana", "Other"]

    if stats_path:
        try:
            with open(stats_path, "r", encoding="utf-8") as f:
                s = json.load(f)
            study_name = s.get("study_area_summary", {}).get("study_area_taluks", study_name)
            if "crop_distribution" in s:
                target_crops = list(s["crop_distribution"].keys())
        except Exception:
            pass

    if geojson_path:
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                fc = json.load(f)
            coords = []
            for feat in fc.get("features", []):
                geom = feat.get("geometry", {})
                if geom.get("type") == "Polygon":
                    for ring in geom.get("coordinates", []):
                        coords.extend(ring)
            if coords:
                center = [round(sum(c[1] for c in coords) / len(coords), 4),
                          round(sum(c[0] for c in coords) / len(coords), 4)]
        except Exception:
            pass

    return {
        "status": "healthy",
        "module": "Member 1 — AI, ML & Backend API",
        "study_area": {
            "name": study_name,
            "district": "Tirunelveli",
            "state": "Tamil Nadu",
            "target_crops": target_crops,
            "center": center
        },
        "database": {
            "postgis_connected": is_db_connected(),
            "mode": "PostGIS" if is_db_connected() else "GeoJSON_Fallback",
        },
        "artifacts_available": {
            "classified_parcels": geojson_path is not None,
            "crop_statistics": stats_path is not None
        }
    }


# Mount static assets for plots (confusion matrix & feature importance)
outputs_dir = os.path.join(os.path.dirname(backend_dir), "outputs")
if os.path.exists(outputs_dir):
    app.mount("/static", StaticFiles(directory=outputs_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
