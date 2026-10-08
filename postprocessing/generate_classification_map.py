"""
Final Publication-Quality Crop Classification Map Generator.
Member 2 - Agricultural Land Parcel & Crop Identification (Tirunelveli District).

Renders high-resolution cartographic map with:
- Delineated parcels colored by crop class:
  * Paddy  -> Vivid Green (#27ae60)
  * Banana -> Golden Orange (#e67e22)
  * Other  -> Neutral Slate Gray (#7f8c8d)
- Study area boundary & taluk divisions (Ambasamudram & Cheranmahadevi)
- Comprehensive legend with parcel counts and acreages
- Scale bar, north arrow, coordinate grid
Saves results/validation_maps/final_crop_classification_map.png (300 DPI).
"""

from pathlib import Path
from typing import Optional, Dict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, FancyArrowPatch, Rectangle
import numpy as np
import geopandas as gpd


def generate_final_crop_map(
    classified_parcels_path: Path = Path("data/parcels/cleaned/classified_parcels.geojson"),
    aoi_path: Path = Path("data/aoi/study_area.geojson"),
    output_png_path: Path = Path("results/validation_maps/final_crop_classification_map.png"),
    target_crs: str = "EPSG:32643",
    dpi: int = 300,
) -> Path:
    """
    Render and export the final publication-quality crop classification map.
    """
    output_png_path.parent.mkdir(parents=True, exist_ok=True)

    if not classified_parcels_path.exists():
        raise FileNotFoundError(f"Classified parcels file not found at: {classified_parcels_path}")

    # 1. Load Data & Reproject to EPSG:32643
    parcels_gdf = gpd.read_file(classified_parcels_path)
    if parcels_gdf.crs is None or parcels_gdf.crs.to_string().upper() != target_crs.upper():
        parcels_gdf = parcels_gdf.to_crs(target_crs)

    aoi_gdf = None
    if aoi_path.exists():
        aoi_gdf = gpd.read_file(aoi_path)
        if aoi_gdf.crs is None or aoi_gdf.crs.to_string().upper() != target_crs.upper():
            aoi_gdf = aoi_gdf.to_crs(target_crs)

    # Calculate exact acreage
    parcels_gdf["area_ha_val"] = parcels_gdf.geometry.area / 10000.0

    # 2. Setup Figure Canvas
    fig, ax = plt.subplots(figsize=(14, 10), dpi=dpi)
    fig.patch.set_facecolor("#fcfdfd")
    ax.set_facecolor("#f7f9fa")

    # 3. Plot AOI Background & Boundaries
    if aoi_gdf is not None:
        aoi_gdf.plot(ax=ax, facecolor="#edf2f7", edgecolor="#2d3748", linewidth=1.5, linestyle="-", zorder=1)
        aoi_gdf.boundary.plot(ax=ax, color="#1a202c", linewidth=1.8, zorder=2)

        # Annotate Taluks
        for idx, row in aoi_gdf.iterrows():
            centroid = row.geometry.centroid
            t_name = row.get("taluk_name", row.get("taluk", f"Taluk {idx+1}"))
            t_area = row.get("area_km2", round(row.geometry.area / 1e6, 1))
            ax.text(
                centroid.x, centroid.y + 1200,
                f"{t_name} Taluk\n({t_area} km²)",
                fontsize=12, fontweight="bold", color="#2b6cb0",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.4", fc="#ffffff", ec="#3182ce", lw=1.2, alpha=0.9),
                zorder=6
            )

    # 4. Color Palette & Parcel Rendering
    color_scheme = {
        "Paddy": {"color": "#27ae60", "edge": "#1e824c", "label": "Paddy (Rice)"},
        "Banana": {"color": "#e67e22", "edge": "#d35400", "label": "Banana (Plantation)"},
        "Other": {"color": "#7f8c8d", "edge": "#34495e", "label": "Other / Non-crop"},
    }

    crop_col = "predicted_crop" if "predicted_crop" in parcels_gdf.columns else "crop_name"

    legend_handles = []
    total_ha_all = parcels_gdf["area_ha_val"].sum()

    for crop_name, style in color_scheme.items():
        sub_gdf = parcels_gdf[parcels_gdf[crop_col] == crop_name]
        count = len(sub_gdf)
        ha_sum = sub_gdf["area_ha_val"].sum()
        pct = (ha_sum / total_ha_all) * 100.0 if total_ha_all > 0 else 0.0

        if not sub_gdf.empty:
            sub_gdf.plot(
                ax=ax,
                facecolor=style["color"],
                edgecolor=style["edge"],
                linewidth=0.8,
                alpha=0.9,
                zorder=4,
            )

        legend_handles.append(
            Patch(
                facecolor=style["color"],
                edgecolor=style["edge"],
                label=f"{style['label']} — {count} parcels ({ha_sum:.1f} ha, {pct:.1f}%)"
            )
        )

    # 5. Cartographic Elements: Title & Metadata Header
    total_parcels = len(parcels_gdf)
    ax.set_title(
        "VIT MAPATHON — Agricultural Land Parcel & Crop Classification Map\n"
        "Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu",
        fontsize=15, fontweight="bold", pad=16, color="#1a202c"
    )

    # 6. North Arrow (Top Right)
    bounds = ax.get_xlim() + ax.get_ylim()
    minx, maxx, miny, maxy = bounds[0], bounds[1], bounds[2], bounds[3]
    arrow_x = maxx - (maxx - minx) * 0.06
    arrow_y = maxy - (maxy - miny) * 0.10
    arrow_len = (maxy - miny) * 0.06

    ax.annotate(
        "N",
        xy=(arrow_x, arrow_y),
        xytext=(arrow_x, arrow_y - arrow_len),
        arrowprops=dict(facecolor="#1a202c", edgecolor="#1a202c", width=3, headwidth=10),
        ha="center", va="center", fontsize=14, fontweight="bold", color="#1a202c",
        zorder=7
    )

    # 7. Scale Bar (Bottom Left)
    scale_bar_len_m = 5000.0  # 5 km
    sb_x = minx + (maxx - minx) * 0.06
    sb_y = miny + (maxy - miny) * 0.06
    ax.plot([sb_x, sb_x + scale_bar_len_m], [sb_y, sb_y], color="#1a202c", linewidth=4, zorder=7)
    ax.plot([sb_x, sb_x + scale_bar_len_m/2], [sb_y, sb_y], color="#ffffff", linewidth=2.5, zorder=8)
    ax.text(
        sb_x + scale_bar_len_m / 2, sb_y + (maxy - miny) * 0.015,
        "5 km", fontsize=10, fontweight="bold", ha="center", color="#1a202c", zorder=7
    )

    # 8. Legend
    legend = ax.legend(
        handles=legend_handles,
        title="Crop Classification (Random Forest Model)",
        title_fontsize=11,
        fontsize=10,
        loc="lower right",
        frameon=True,
        facecolor="#ffffff",
        edgecolor="#cbd5e0",
        framealpha=0.95,
        shadow=True,
        borderpad=0.8,
    )
    legend.get_title().set_weight("bold")

    # 9. Coordinate Grid & Labels
    ax.set_xlabel("UTM Easting (m) — Zone 43N", fontsize=10, color="#4a5568")
    ax.set_ylabel("UTM Northing (m) — Zone 43N", fontsize=10, color="#4a5568")
    ax.grid(True, linestyle=":", color="#a0aec0", alpha=0.6)
    ax.tick_params(colors="#4a5568", labelsize=9)

    plt.tight_layout()
    plt.savefig(output_png_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    print(f"[MAP GENERATED] Final classification map saved: {output_png_path.resolve()} (DPI: {dpi})")
    return output_png_path


if __name__ == "__main__":
    generate_final_crop_map()
