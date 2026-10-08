"""
AOI Boundary Builder and Validator for Ambasamudram & Cheranmahadevi Taluks.
Creates and validates data/aoi/study_area.geojson in EPSG:32643.
"""

from pathlib import Path
import json
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid
import pyproj

def build_and_validate_aoi(output_path: Path = Path("data/aoi/study_area.geojson")):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ambasamudram Taluk agricultural boundary (covering Ambasamudram, Kallidaikurichi, Manimuthar canal basin)
    # Coordinates in WGS84 (Lon, Lat)
    ambasamudram_coords_wgs84 = [
        (77.380, 8.730),
        (77.440, 8.750),
        (77.490, 8.740),
        (77.510, 8.710),
        (77.495, 8.670),
        (77.450, 8.650),
        (77.400, 8.660),
        (77.375, 8.690),
        (77.380, 8.730)
    ]
    
    # Cheranmahadevi Taluk agricultural boundary (covering Veeravanallur, Cheranmahadevi, Pathamadai, Melaseval)
    cheranmahadevi_coords_wgs84 = [
        (77.490, 8.740),
        (77.550, 8.735),
        (77.620, 8.720),
        (77.640, 8.680),
        (77.600, 8.650),
        (77.540, 8.650),
        (77.495, 8.670),
        (77.510, 8.710),
        (77.490, 8.740)
    ]
    
    # Reproject coordinates to EPSG:32643
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    
    poly_amba_utm = Polygon([transformer.transform(x, y) for x, y in ambasamudram_coords_wgs84])
    poly_chera_utm = Polygon([transformer.transform(x, y) for x, y in cheranmahadevi_coords_wgs84])
    
    poly_amba_utm = make_valid(poly_amba_utm)
    poly_chera_utm = make_valid(poly_chera_utm)
    
    area_amba_km2 = poly_amba_utm.area / 1e6
    area_chera_km2 = poly_chera_utm.area / 1e6
    total_area_km2 = area_amba_km2 + area_chera_km2
    
    gdf = gpd.GeoDataFrame([
        {
            "taluk_id": "TAL_01",
            "taluk_name": "Ambasamudram",
            "district": "Tirunelveli",
            "state": "Tamil Nadu",
            "area_km2": round(area_amba_km2, 2),
            "geometry": poly_amba_utm
        },
        {
            "taluk_id": "TAL_02",
            "taluk_name": "Cheranmahadevi",
            "district": "Tirunelveli",
            "state": "Tamil Nadu",
            "area_km2": round(area_chera_km2, 2),
            "geometry": poly_chera_utm
        }
    ], crs="EPSG:32643")
    
    # Save to GeoJSON
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"[AOI GENERATED] File: {output_path.resolve()}")
    print(f"  - Features: {len(gdf)} taluks")
    print(f"  - Ambasamudram Taluk Area : {area_amba_km2:.2f} km²")
    print(f"  - Cheranmahadevi Taluk Area: {area_chera_km2:.2f} km²")
    print(f"  - Total Study Area         : {total_area_km2:.2f} km² (Requirement >= 20 km²: {'PASSED' if total_area_km2 >= 20.0 else 'FAILED'})")
    print(f"  - CRS                      : {gdf.crs}")
    print(f"  - Bounds (UTM 43N)         : {gdf.total_bounds}")
    print(f"  - Validity Check           : {all(gdf.is_valid)}")
    
    return output_path

if __name__ == "__main__":
    build_and_validate_aoi()
