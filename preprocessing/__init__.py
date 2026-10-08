"""
VIT_MAPATHON - Member 2 (GIS / Remote Sensing Engineering) Preprocessing Package
Agricultural Land Parcel and Crop Identification in Tirunelveli District.
"""

from pathlib import Path

# Default Coordinate Reference System for Tirunelveli / UTM Zone 43N
DEFAULT_CRS = "EPSG:32643"

# Native Sentinel-2 band spatial resolutions
BAND_RESOLUTIONS = {
    "B02": 10.0,  # Blue (10m)
    "B03": 10.0,  # Green (10m)
    "B04": 10.0,  # Red (10m)
    "B08": 10.0,  # NIR (10m)
    "B11": 20.0,  # SWIR-1 (20m)
    "B12": 20.0,  # SWIR-2 (20m)
    "SCL": 20.0,  # Scene Classification Layer (20m)
}
