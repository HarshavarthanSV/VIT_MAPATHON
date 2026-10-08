"""
GIS Postprocessing and Vectorization Module.
Converts classified crop rasters / parcel masks into clean vector polygons (GeoJSON/Shapefile/GeoPackage)
for QGIS visual validation, parcel boundary analysis, and handoff to Backend & Web GIS Dashboard.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import geopandas as gpd
from shapely.geometry import shape, Polygon
import rasterio
from rasterio.features import shapes


def vectorize_classified_raster(
    classified_raster_path: Union[str, Path],
    output_vector_path: Union[str, Path],
    class_labels: Optional[Dict[int, str]] = None,
    min_area_sqm: float = 500.0,
    simplify_tolerance: Optional[float] = 2.0,
) -> Path:
    """
    Vectorize a categorical crop classification raster into polygon features.
    Filters out noise polygons smaller than min_area_sqm (default 500 m² = 0.05 ha).
    Adds attributes: class_id, crop_name, area_ha, perimeter_m.
    """
    raster_path = Path(classified_raster_path)
    out_vector = Path(output_vector_path)
    out_vector.parent.mkdir(parents=True, exist_ok=True)

    if class_labels is None:
        class_labels = {
            1: "Paddy",
            2: "Banana",
            3: "Water",
            4: "Other_Vegetation",
            5: "Bare_Soil_Builtup",
        }

    with rasterio.open(raster_path) as src:
        image = src.read(1)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    mask = image != nodata if nodata is not None else np.ones(image.shape, dtype=bool)

    # Extract polygon shapes from raster
    polygon_generator = shapes(image, mask=mask, transform=transform)

    records = []
    for geom_dict, val in polygon_generator:
        class_val = int(val)
        if class_val == nodata or class_val <= 0:
            continue

        poly = shape(geom_dict)
        if simplify_tolerance and simplify_tolerance > 0:
            poly = poly.simplify(simplify_tolerance, preserve_topology=True)

        area_sqm = poly.area
        if area_sqm < min_area_sqm:
            continue

        area_ha = area_sqm / 10000.0
        crop_name = class_labels.get(class_val, f"Class_{class_val}")

        records.append({
            "geometry": poly,
            "class_id": class_val,
            "crop_name": crop_name,
            "area_sqm": round(area_sqm, 2),
            "area_ha": round(area_ha, 4),
        })

    if not records:
        gdf = gpd.GeoDataFrame(columns=["geometry", "class_id", "crop_name", "area_sqm", "area_ha"], crs=crs)
    else:
        gdf = gpd.GeoDataFrame(records, crs=crs)

    # Export to GeoJSON or GeoPackage
    if out_vector.suffix.lower() == ".geojson":
        # WGS84 for GeoJSON web compatibility if needed, or maintain native CRS
        gdf.to_file(out_vector, driver="GeoJSON")
    elif out_vector.suffix.lower() == ".gpkg":
        gdf.to_file(out_vector, driver="GPKG")
    elif out_vector.suffix.lower() == ".shp":
        gdf.to_file(out_vector, driver="ESRI Shapefile")
    else:
        gdf.to_file(out_vector, driver="GeoJSON")

    return out_vector
