"""
Member 2 — Agricultural Parcel & Ground Truth Digitization Helper
Generates agricultural parcel grids or digitizes field polygons across the AOI
for Ambasamudram and Cheranmahadevi Taluks.
"""

import os
import argparse
import logging
import geopandas as gpd
from shapely.geometry import box, Polygon
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Member2_Parcel_Generator")


def generate_study_parcels(
    aoi_path: str,
    output_parcels_path: str,
    parcel_size_meters: float = 200.0,
    target_crs: str = "EPSG:32643"
) -> str:
    """
    Subdivides the agricultural AOI in Ambasamudram & Cheranmahadevi into candidate farm parcels
    totaling >= 20 sq. km.
    """
    os.makedirs(os.path.dirname(output_parcels_path), exist_ok=True)
    
    aoi_gdf = gpd.read_file(aoi_path)
    if aoi_gdf.crs != target_crs:
        aoi_gdf = aoi_gdf.to_crs(target_crs)

    total_bounds = aoi_gdf.total_bounds  # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = total_bounds

    x_coords = np.arange(minx, maxx, parcel_size_meters)
    y_coords = np.arange(miny, maxy, parcel_size_meters)

    aoi_geom = aoi_gdf.geometry.iloc[0]
    parcels = []
    parcel_ids = []

    count = 1
    for x in x_coords:
        for y in y_coords:
            p_box = box(x, y, x + parcel_size_meters, y + parcel_size_meters)
            if p_box.intersects(aoi_geom):
                intersection = p_box.intersection(aoi_geom)
                if not intersection.is_empty and intersection.area > 5000:  # >= 0.5 hectare
                    parcels.append(intersection)
                    parcel_ids.append(f"parcel_{count:05d}")
                    count += 1

    gdf_parcels = gpd.GeoDataFrame({
        "parcel_id": parcel_ids,
        "geometry": parcels
    }, crs=target_crs)

    total_area_sq_km = gdf_parcels.geometry.area.sum() / 1e6
    logger.info(f"Generated {len(gdf_parcels)} parcels covering {total_area_sq_km:.2f} sq. km.")

    # Export
    gdf_parcels.to_file(output_parcels_path, driver="GeoJSON")
    logger.info(f"Saved agricultural parcel boundaries to: {output_parcels_path}")
    return output_parcels_path


def main():
    parser = argparse.ArgumentParser(description="Member 2 Parcel & Label Digitizer")
    parser.add_argument("--aoi", type=str, default="member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson")
    parser.add_argument("--output-parcels", type=str, default="member2-gis/outputs/parcels/parcel_boundaries.geojson")
    args = parser.parse_args()

    generate_study_parcels(args.aoi, args.output_parcels)


if __name__ == "__main__":
    main()
