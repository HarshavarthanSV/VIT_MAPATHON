"""
AOI Clipping Module for Sentinel-2 Rasters.
Clips raster files to a specified Area of Interest (GeoJSON/Shapefile/GeoPackage)
with automatic CRS reprojection, alignment, and metadata preservation.
"""

from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import json
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape, mapping
from shapely.ops import transform
import pyproj


def load_aoi_geometry(aoi_path: Union[str, Path], target_crs: Optional[str] = "EPSG:32643") -> List[Dict[str, Any]]:
    """
    Load vector AOI boundary and reproject to target CRS (default EPSG:32643).
    Returns list of GeoJSON geometry dictionaries.
    """
    aoi_path = Path(aoi_path)
    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI boundary file not found at: {aoi_path}")

    # Load using geopandas
    gdf = gpd.read_file(aoi_path)
    if gdf.empty:
        raise ValueError(f"AOI file {aoi_path} contains no valid geometry.")

    # Ensure CRS is defined
    if gdf.crs is None:
        # Default assumption if missing is WGS84 EPSG:4326
        gdf.set_crs(epsg=4326, inplace=True)

    if target_crs and gdf.crs.to_string().upper() != target_crs.upper():
        gdf = gdf.to_crs(target_crs)

    # Extract geometries
    geometries = [mapping(geom) for geom in gdf.geometry if geom is not None and not geom.is_empty]
    if not geometries:
        raise ValueError("No valid non-empty geometries found in AOI file.")

    return geometries


def clip_raster_to_aoi(
    input_raster_path: Union[str, Path],
    aoi_path: Union[str, Path],
    output_raster_path: Union[str, Path],
    nodata_val: Optional[float] = None,
    all_touched: bool = False,
) -> Path:
    """
    Clip input raster with vector AOI geometry.
    Automatically handles CRS mismatch between raster and vector, and dtype-aware NoData values.
    """
    input_path = Path(input_raster_path)
    output_path = Path(output_raster_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input raster not found: {input_path}")

    with rasterio.open(input_path) as src:
        raster_crs = src.crs
        if raster_crs is None:
            raster_crs = "EPSG:32643"

        # Determine safe nodata value matching dtype
        dtype_str = src.dtypes[0]
        if nodata_val is not None:
            effective_nodata = nodata_val
        elif src.nodata is not None:
            effective_nodata = src.nodata
        elif "uint" in dtype_str:
            effective_nodata = 0
        elif "int" in dtype_str:
            effective_nodata = -9999
        else:
            effective_nodata = np.nan

        # Load AOI in the matching raster CRS
        shapes = load_aoi_geometry(aoi_path, target_crs=raster_crs.to_string())

        # Perform clipping / masking
        out_image, out_transform = mask(
            src,
            shapes,
            crop=True,
            nodata=effective_nodata,
            all_touched=all_touched,
            filled=True,
        )

        out_profile = src.profile.copy()
        out_profile.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": effective_nodata,
            "compress": "lzw",
        })

        if out_image.shape[2] >= 256 and out_image.shape[1] >= 256:
            out_profile.update({
                "tiled": True,
                "blockxsize": 256,
                "blockysize": 256,
            })
        else:
            out_profile.pop("tiled", None)
            out_profile.pop("blockxsize", None)
            out_profile.pop("blockysize", None)

        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(out_image)
            dst.update_tags(
                AOI_SOURCE=str(aoi_path),
                CLIPPED_BY="Member2_GIS_Pipeline",
            )

    return output_path
