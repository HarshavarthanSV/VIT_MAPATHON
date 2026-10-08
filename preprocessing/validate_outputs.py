"""
Visual Validation and Map Rendering Module.
Generates quick-inspection visual PNG maps under results/validation_maps/ for:
1. AOI boundary
2. True-Color RGB composite (B04/B03/B02)
3. False-Color composite (B08/B04/B03)
4. NDVI map
5. EVI map
6. SAVI map
7. NDWI map
8. Parcel boundaries
9. Training labels
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.plot import show


def normalize_rgb(arr: np.ndarray, lower_p: float = 2.0, upper_p: float = 98.0) -> np.ndarray:
    """Normalize array for RGB display with percentile stretching."""
    valid_mask = (arr > 0) & (~np.isnan(arr)) & (arr != -9999.0)
    if not np.any(valid_mask):
        return np.zeros_like(arr, dtype=np.float32)
    p_low = np.percentile(arr[valid_mask], lower_p)
    p_high = np.percentile(arr[valid_mask], upper_p)
    if p_high - p_low < 1e-5:
        p_high = p_low + 1.0
    stretched = np.clip((arr - p_low) / (p_high - p_low), 0.0, 1.0)
    return stretched


def generate_validation_maps(
    aoi_path: Path = Path("data/aoi/study_area.geojson"),
    cloud_masked_scenes: Optional[Dict[str, Dict[str, Path]]] = None,
    indices_scenes: Optional[Dict[str, Dict[str, Path]]] = None,
    cleaned_parcels_path: Path = Path("data/parcels/cleaned/parcels.geojson"),
    training_labels_path: Path = Path("data/parcels/training/training_labels.geojson"),
    output_dir: Path = Path("results/validation_maps"),
    target_date: Optional[str] = None,
) -> Dict[str, Path]:
    """
    Generate and save all 9 visual validation maps as high-resolution PNGs.
    """
    print("\n[VISUAL VALIDATION] Rendering inspection maps in results/validation_maps/...")
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_maps = {}

    aoi_gdf = gpd.read_file(aoi_path)

    # 1. AOI Map
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    aoi_gdf.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=2.0, label="Study Area AOI")
    aoi_gdf.boundary.plot(ax=ax, color="darkred")
    for idx, row in aoi_gdf.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            text=f"{row.get('taluk_name', 'Taluk')} ({row.get('area_km2', '')} km²)",
            xy=(centroid.x, centroid.y),
            ha="center", fontsize=11, fontweight="bold", color="darkblue",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="darkblue", alpha=0.8)
        )
    ax.set_title("Study Area AOI: Ambasamudram & Cheranmahadevi Taluks (EPSG:32643)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.grid(True, linestyle="--", alpha=0.5)
    aoi_png = output_dir / "01_aoi_map.png"
    plt.tight_layout()
    plt.savefig(aoi_png)
    plt.close()
    generated_maps["aoi_map"] = aoi_png

    if cloud_masked_scenes and indices_scenes:
        if target_date is None or target_date not in cloud_masked_scenes:
            target_date = sorted(list(cloud_masked_scenes.keys()))[0]

        date_bands = cloud_masked_scenes[target_date]
        date_indices = indices_scenes[target_date]

        # Read RGB bands
        with rasterio.open(date_bands["B04"]) as s_r:
            red = s_r.read(1).astype(np.float32)
        with rasterio.open(date_bands["B03"]) as s_g:
            green = s_g.read(1).astype(np.float32)
        with rasterio.open(date_bands["B02"]) as s_b:
            blue = s_b.read(1).astype(np.float32)
        with rasterio.open(date_bands["B08"]) as s_nir:
            nir = s_nir.read(1).astype(np.float32)

        # 2. True-Color RGB Composite (B04, B03, B02)
        rgb_img = np.dstack([normalize_rgb(red), normalize_rgb(green), normalize_rgb(blue)])
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.imshow(rgb_img)
        ax.set_title(f"True-Color RGB Composite (B04/B03/B02) - {target_date}", fontsize=13, fontweight="bold")
        ax.axis("off")
        rgb_png = output_dir / "02_rgb_composite.png"
        plt.tight_layout()
        plt.savefig(rgb_png)
        plt.close()
        generated_maps["rgb_composite"] = rgb_png

        # 3. False-Color Composite (B08, B04, B03)
        nrg_img = np.dstack([normalize_rgb(nir), normalize_rgb(red), normalize_rgb(green)])
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        ax.imshow(nrg_img)
        ax.set_title(f"False-Color Composite (B08/B04/B03) - {target_date}\n(Red = Dense Banana/Paddy Canopy)", fontsize=12, fontweight="bold")
        ax.axis("off")
        fc_png = output_dir / "03_false_color_composite.png"
        plt.tight_layout()
        plt.savefig(fc_png)
        plt.close()
        generated_maps["false_color_composite"] = fc_png

        # 4. NDVI Map
        with rasterio.open(date_indices["NDVI"]) as src:
            ndvi = src.read(1)
            ndvi_masked = np.where((ndvi != -9999.0) & (~np.isnan(ndvi)), ndvi, np.nan)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        im = ax.imshow(ndvi_masked, cmap="RdYlGn", vmin=-0.1, vmax=0.85)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04, label="NDVI Index Value")
        ax.set_title(f"Normalized Difference Vegetation Index (NDVI) - {target_date}", fontsize=13, fontweight="bold")
        ax.axis("off")
        ndvi_png = output_dir / "04_ndvi_map.png"
        plt.tight_layout()
        plt.savefig(ndvi_png)
        plt.close()
        generated_maps["ndvi_map"] = ndvi_png

        # 5. EVI Map
        with rasterio.open(date_indices["EVI"]) as src:
            evi = src.read(1)
            evi_masked = np.where((evi != -9999.0) & (~np.isnan(evi)), evi, np.nan)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        im = ax.imshow(evi_masked, cmap="YlGn", vmin=0.0, vmax=0.9)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04, label="EVI Index Value")
        ax.set_title(f"Enhanced Vegetation Index (EVI) - {target_date}", fontsize=13, fontweight="bold")
        ax.axis("off")
        evi_png = output_dir / "05_evi_map.png"
        plt.tight_layout()
        plt.savefig(evi_png)
        plt.close()
        generated_maps["evi_map"] = evi_png

        # 6. SAVI Map
        with rasterio.open(date_indices["SAVI"]) as src:
            savi = src.read(1)
            savi_masked = np.where((savi != -9999.0) & (~np.isnan(savi)), savi, np.nan)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        im = ax.imshow(savi_masked, cmap="Greens", vmin=0.0, vmax=0.75)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04, label="SAVI Index Value")
        ax.set_title(f"Soil Adjusted Vegetation Index (SAVI) - {target_date}", fontsize=13, fontweight="bold")
        ax.axis("off")
        savi_png = output_dir / "06_savi_map.png"
        plt.tight_layout()
        plt.savefig(savi_png)
        plt.close()
        generated_maps["savi_map"] = savi_png

        # 7. NDWI Map
        with rasterio.open(date_indices["NDWI"]) as src:
            ndwi = src.read(1)
            ndwi_masked = np.where((ndwi != -9999.0) & (~np.isnan(ndwi)), ndwi, np.nan)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        im = ax.imshow(ndwi_masked, cmap="BrBG", vmin=-0.8, vmax=0.4)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04, label="NDWI Index Value")
        ax.set_title(f"Normalized Difference Water Index (NDWI) - {target_date}", fontsize=13, fontweight="bold")
        ax.axis("off")
        ndwi_png = output_dir / "07_ndwi_map.png"
        plt.tight_layout()
        plt.savefig(ndwi_png)
        plt.close()
        generated_maps["ndwi_map"] = ndwi_png

    # 8. Cleaned Parcels Boundaries Map
    if cleaned_parcels_path.exists():
        parcels_gdf = gpd.read_file(cleaned_parcels_path)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        aoi_gdf.plot(ax=ax, facecolor="#f5f5f5", edgecolor="gray", linestyle="--", linewidth=1.2)
        parcels_gdf.plot(ax=ax, facecolor="#90EE90", edgecolor="#2E8B57", linewidth=0.8, alpha=0.8)
        ax.set_title(f"Delineated Agricultural Land Parcels (N = {len(parcels_gdf)})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")
        ax.grid(True, linestyle=":", alpha=0.5)
        parcels_png = output_dir / "08_parcels_map.png"
        plt.tight_layout()
        plt.savefig(parcels_png)
        plt.close()
        generated_maps["parcels_map"] = parcels_png

    # 9. Training Labels Map
    if training_labels_path.exists():
        labels_gdf = gpd.read_file(training_labels_path)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
        aoi_gdf.plot(ax=ax, facecolor="#fafafa", edgecolor="black", linewidth=1.5)

        color_map = {0: "#808080", 1: "#32CD32", 2: "#FF8C00"}
        labels_map = {0: "Other / Non-crop", 1: "Paddy (Rice)", 2: "Banana (Orchard)"}

        for class_id, color in color_map.items():
            sub = labels_gdf[labels_gdf["crop_class"] == class_id]
            if not sub.empty:
                sub.plot(ax=ax, facecolor=color, edgecolor="black", linewidth=0.6, label=f"{labels_map[class_id]} (n={len(sub)})")

        ax.set_title("Ground Truth / Reference Training Parcels (Paddy, Banana, Other)", fontsize=13, fontweight="bold")
        ax.legend(loc="upper right", frameon=True)
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")
        ax.grid(True, linestyle=":", alpha=0.5)
        train_png = output_dir / "09_training_labels_map.png"
        plt.tight_layout()
        plt.savefig(train_png)
        plt.close()
        generated_maps["training_labels_map"] = train_png

    print(f"  [OK] Generated {len(generated_maps)} visual validation maps in {output_dir.resolve()}")
    return generated_maps
