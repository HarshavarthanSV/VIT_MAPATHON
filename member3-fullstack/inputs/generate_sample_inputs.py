"""
Generator for Member 3 Offline Development & Demonstration Dataset
Adheres strictly to the data contract in member1-ml/docs/member3_handoff.md.
Generates realistic agricultural parcel geometries in Ambasamudram and Cheranmahadevi Taluks (>= 20 sq. km)
using exact metric area calculations in EPSG:32643 and exporting standard EPSG:4326 GeoJSON.
"""

import os
import json
import numpy as np
import pyproj
from shapely.geometry import shape, box, Polygon, mapping
from shapely.ops import transform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_inputs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    aoi_path = os.path.abspath(os.path.join(base_dir, "../../member2-gis/inputs/aoi_ambasamudram_cheranmahadevi.geojson"))
    
    if not os.path.exists(aoi_path):
        raise FileNotFoundError(f"AOI file not found at: {aoi_path}")
        
    with open(aoi_path, "r", encoding="utf-8") as f:
        aoi_data = json.load(f)
        
    aoi_geom_wgs = shape(aoi_data["features"][0]["geometry"])
    
    # Coordinate transformers
    wgs_to_utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True).transform
    utm_to_wgs = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True).transform
    
    aoi_geom_utm = transform(wgs_to_utm, aoi_geom_wgs)
    minx, miny, maxx, maxy = aoi_geom_utm.bounds
    
    np.random.seed(42)
    
    # Create realistic parcels in UTM (size ~ 150m to 250m)
    step_x = 220.0
    step_y = 190.0
    
    features = []
    parcel_count = 0
    
    # Target distribution: ~58% Paddy, ~27% Banana, ~15% Other
    crops = ["Paddy", "Banana", "Other"]
    crop_weights = [0.58, 0.27, 0.15]
    
    x_coords = np.arange(minx + 500, maxx - 500, step_x)
    y_coords = np.arange(miny + 500, maxy - 500, step_y)
    
    for x in x_coords:
        for y in y_coords:
            # Add slight jitter to parcel vertices for organic field appearance
            dx = np.random.uniform(-25, 25)
            dy = np.random.uniform(-20, 20)
            w = step_x - 30 + np.random.uniform(-20, 20)
            h = step_y - 25 + np.random.uniform(-15, 15)
            
            p_box = box(x + dx, y + dy, x + dx + w, y + dy + h)
            if aoi_geom_utm.contains(p_box.centroid):
                parcel_count += 1
                area_sq_m = p_box.area
                area_sq_km = area_sq_m / 1e6
                area_ha = area_sq_m / 10000.0
                
                # Assign crop based on position (Thamirabarani river corridor favors Paddy, south/slopes favor Banana/Other)
                norm_y = (y - miny) / (maxy - miny)
                if 0.35 <= norm_y <= 0.70:
                    prob_p = 0.70
                    prob_b = 0.22
                    prob_o = 0.08
                elif norm_y < 0.35:
                    prob_p = 0.40
                    prob_b = 0.42
                    prob_o = 0.18
                else:
                    prob_p = 0.45
                    prob_b = 0.25
                    prob_o = 0.30
                
                crop = np.random.choice(crops, p=[prob_p, prob_b, prob_o])
                
                # Confidence and class probabilities
                if crop == "Paddy":
                    conf = np.random.uniform(0.85, 0.98)
                    rem = 1.0 - conf
                    p_b = rem * np.random.uniform(0.4, 0.8)
                    p_o = rem - p_b
                    prob_paddy = conf
                    prob_banana = p_b
                    prob_other = p_o
                elif crop == "Banana":
                    conf = np.random.uniform(0.80, 0.96)
                    rem = 1.0 - conf
                    p_p = rem * np.random.uniform(0.3, 0.7)
                    p_o = rem - p_p
                    prob_paddy = p_p
                    prob_banana = conf
                    prob_other = p_o
                else:
                    conf = np.random.uniform(0.72, 0.92)
                    rem = 1.0 - conf
                    p_p = rem * np.random.uniform(0.4, 0.6)
                    p_b = rem - p_p
                    prob_paddy = p_p
                    prob_banana = p_b
                    prob_other = conf
                
                # Reproject geometry back to EPSG:4326 for Leaflet compatibility
                geom_wgs = transform(utm_to_wgs, p_box)
                
                # Reduce precision to 6 decimal places for web performance
                coords_wgs = [
                    [[round(coord[0], 6), round(coord[1], 6)] for coord in geom_wgs.exterior.coords]
                ]
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": coords_wgs
                    },
                    "properties": {
                        "parcel_id": f"parcel_{parcel_count:05d}",
                        "predicted_crop": crop,
                        "confidence": round(float(conf), 4),
                        "area_sq_km": round(float(area_sq_km), 4),
                        "area_ha": round(float(area_ha), 2),
                        "prob_paddy": round(float(prob_paddy), 4),
                        "prob_banana": round(float(prob_banana), 4),
                        "prob_other": round(float(prob_other), 4)
                    }
                }
                features.append(feature)
                
                if parcel_count >= 850:
                    # Sufficient density covering ~30 sq km
                    break
        if parcel_count >= 850:
            break
            
    geojson_data = {
        "type": "FeatureCollection",
        "name": "classified_parcels_ambasamudram_cheranmahadevi",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }
    
    geojson_out = os.path.join(base_dir, "classified_parcels.geojson")
    with open(geojson_out, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)
        
    print(f"Generated {len(features)} parcel features saved to {geojson_out}")
    
    # Compute dynamic crop statistics strictly from features
    total_parcels = len(features)
    total_area_sq_km = sum(f["properties"]["area_sq_km"] for f in features)
    total_area_ha = sum(f["properties"]["area_ha"] for f in features)
    overall_mean_conf = float(np.mean([f["properties"]["confidence"] for f in features]))
    
    crop_stats = {}
    for crop in ["Paddy", "Banana", "Other"]:
        c_feats = [f for f in features if f["properties"]["predicted_crop"] == crop]
        c_count = len(c_feats)
        c_area_sq_km = sum(f["properties"]["area_sq_km"] for f in c_feats)
        c_area_ha = sum(f["properties"]["area_ha"] for f in c_feats)
        c_mean_conf = float(np.mean([f["properties"]["confidence"] for f in c_feats])) if c_count > 0 else 0.0
        
        crop_stats[crop] = {
            "parcel_count": c_count,
            "percentage_of_parcels": round((c_count / total_parcels * 100.0), 2) if total_parcels > 0 else 0.0,
            "area_sq_km": round(c_area_sq_km, 4),
            "area_hectares": round(c_area_ha, 2),
            "percentage_of_total_area": round((c_area_sq_km / total_area_sq_km * 100.0), 2) if total_area_sq_km > 0 else 0.0,
            "mean_confidence": round(c_mean_conf, 4)
        }
        
    statistics_data = {
        "study_area_summary": {
            "total_parcels": total_parcels,
            "total_study_area_sq_km": round(total_area_sq_km, 4),
            "total_study_area_hectares": round(total_area_ha, 2),
            "overall_mean_confidence": round(overall_mean_conf, 4),
            "meets_min_area_requirement": total_area_sq_km >= 20.0
        },
        "crop_distribution": crop_stats
    }
    
    stats_out = os.path.join(base_dir, "crop_statistics.json")
    with open(stats_out, "w", encoding="utf-8") as f:
        json.dump(statistics_data, f, indent=2)
    print(f"Generated crop statistics saved to {stats_out}")
    
    # Model evaluation metrics adhering strictly to Section 5 of handoff specification
    metrics_data = {
        "overall": {
            "accuracy": 0.9184,
            "precision_macro": 0.9102,
            "precision_weighted": 0.9188,
            "recall_macro": 0.9065,
            "recall_weighted": 0.9184,
            "f1_score_macro": 0.9082,
            "f1_score_weighted": 0.9185,
            "total_test_samples": 512
        },
        "per_class": {
            "Paddy": {
                "precision": 0.9360,
                "recall": 0.9450,
                "f1_score": 0.9405,
                "support": 302
            },
            "Banana": {
                "precision": 0.8980,
                "recall": 0.8820,
                "f1_score": 0.8899,
                "support": 141
            },
            "Other": {
                "precision": 0.8965,
                "recall": 0.8925,
                "f1_score": 0.8945,
                "support": 69
            }
        }
    }
    metrics_out = os.path.join(base_dir, "model_metrics.json")
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Generated model metrics saved to {metrics_out}")
    
    # Feature importance
    feature_importance_data = {
        "NDVI_mean": 0.2450,
        "NDWI_min": 0.1820,
        "EVI_mean": 0.1540,
        "B08_NIR": 0.1180,
        "SAVI_mean": 0.0890,
        "B04_Red": 0.0760,
        "B11_SWIR1": 0.0520,
        "B12_SWIR2": 0.0410,
        "B03_Green": 0.0240,
        "B02_Blue": 0.0190
    }
    fi_out = os.path.join(base_dir, "feature_importance.json")
    with open(fi_out, "w", encoding="utf-8") as f:
        json.dump(feature_importance_data, f, indent=2)
    print(f"Generated feature importance saved to {fi_out}")
    
    # Generate Confusion Matrix Chart
    cm_matrix = np.array([
        [285, 10, 7],
        [11, 124, 6],
        [4, 3, 62]
    ])
    labels = ["Paddy", "Banana", "Other"]
    
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_matrix, cmap="Blues", interpolation="nearest")
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm_matrix.shape[1]),
        yticks=np.arange(cm_matrix.shape[0]),
        xticklabels=labels,
        yticklabels=labels,
        title="Random Forest Confusion Matrix\nAmbasamudram & Cheranmahadevi",
        ylabel="True Ground Truth",
        xlabel="Predicted Crop Class"
    )
    for i in range(cm_matrix.shape[0]):
        for j in range(cm_matrix.shape[1]):
            val = cm_matrix[i, j]
            color = "white" if val > cm_matrix.max() / 2 else "black"
            ax.text(j, i, format(val, 'd'), ha="center", va="center", color=color, fontweight="bold")
    plt.tight_layout()
    cm_plot_path = os.path.join(base_dir, "confusion_matrix.png")
    plt.savefig(cm_plot_path, dpi=180)
    plt.close()
    print(f"Generated confusion matrix plot: {cm_plot_path}")
    
    # Generate Feature Importance Chart
    fig, ax = plt.subplots(figsize=(8, 5))
    sorted_feats = sorted(feature_importance_data.items(), key=lambda x: x[1])
    feat_names = [x[0] for x in sorted_feats]
    feat_vals = [x[1] for x in sorted_feats]
    
    colors = ['#10b981' if 'NDVI' in n or 'EVI' in n or 'SAVI' in n else '#3b82f6' if 'NDWI' in n else '#f59e0b' for n in feat_names]
    ax.barh(feat_names, feat_vals, color=colors)
    ax.set_xlabel("Relative Importance (MDI / Gini)")
    ax.set_title("Random Forest Spectral & Temporal Feature Importance")
    plt.tight_layout()
    fi_plot_path = os.path.join(base_dir, "feature_importance.png")
    plt.savefig(fi_plot_path, dpi=180)
    plt.close()
    print(f"Generated feature importance plot: {fi_plot_path}")

if __name__ == "__main__":
    generate_inputs()
