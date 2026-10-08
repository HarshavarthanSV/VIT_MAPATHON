"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
FastAPI Backend Application Entrypoint
Provides REST endpoints for Agricultural Land Parcel & Crop Identification in Tirunelveli District.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import init_db_connection, is_db_connected, resolve_artifact_path
from routers import parcels, statistics

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


@app.get("/", include_in_schema=False)
def root():
    """Redirects to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api/health")
def health_check():
    """Returns system status, active database backend, and study area metadata."""
    geojson_available = resolve_artifact_path("classified_parcels.geojson") is not None
    stats_available = resolve_artifact_path("crop_statistics.json") is not None

    return {
        "status": "healthy",
        "module": "Member 3 — Full Stack & Web GIS",
        "study_area": {
            "name": "Ambasamudram & Cheranmahadevi Taluks",
            "district": "Tirunelveli",
            "state": "Tamil Nadu",
            "target_crops": ["Paddy", "Banana", "Other"],
            "center": [8.70, 77.49]
        },
        "database": {
            "postgis_connected": is_db_connected(),
            "mode": "PostGIS" if is_db_connected() else "GeoJSON_Fallback",
        },
        "artifacts_available": {
            "classified_parcels": geojson_available,
            "crop_statistics": stats_available
        }
    }


# Mount static assets for plots (confusion matrix & feature importance)
inputs_dir = os.path.join(os.path.dirname(backend_dir), "inputs")
if os.path.exists(inputs_dir):
    app.mount("/static", StaticFiles(directory=inputs_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
