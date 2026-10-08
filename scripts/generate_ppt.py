"""
VIT MAPATHON — Professional 5-Slide Executive PowerPoint Generator
Creates a formal, minimalist, non-colorful presentation adhering to the 5-slide constraint,
featuring real project metrics, comparison tables, and embedded project figures.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6] # Blank slide layout

    # Formal, minimalist color palette (clean corporate / academic theme)
    COLOR_BG = RGBColor(248, 250, 252)          # Soft slate white
    COLOR_CARD_BG = RGBColor(255, 255, 255)     # Pure white card
    COLOR_CARD_BORDER = RGBColor(226, 232, 240) # Subtle gray border
    COLOR_PRIMARY = RGBColor(15, 23, 42)        # Deep Charcoal / Navy
    COLOR_SECONDARY = RGBColor(51, 65, 85)      # Slate Dark
    COLOR_MUTED = RGBColor(100, 116, 139)       # Medium Slate Gray
    COLOR_ACCENT = RGBColor(30, 58, 138)        # Formal Oxford Navy
    COLOR_LIGHT_ROW = RGBColor(241, 245, 249)   # Alternating row background

    brain_dir = r"C:\Users\Harshavarthan\.gemini\antigravity\brain\f9a24605-1c38-4305-b3cd-6c642564fc07"
    img_cm = os.path.join(brain_dir, "confusion_matrix.png")
    img_fi = os.path.join(brain_dir, "feature_importance.png")
    img_dash = os.path.join(brain_dir, "dashboard_screenshot.png")

    def add_header(slide, category, title, subtitle):
        # Category Eyebrow
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(9.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_ACCENT

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.55))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_PRIMARY

        # Subtitle
        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.22), Inches(11.7), Inches(0.4))
            tf_sub = sub_box.text_frame
            tf_sub.word_wrap = True
            p_sub = tf_sub.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = COLOR_MUTED

    def add_card(slide, left, top, width, height, title=None):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLOR_CARD_BG
        shape.line.color.rgb = COLOR_CARD_BORDER
        shape.line.width = Pt(1)
        
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.4))
            tf = tb.text_frame
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(12)
            p.font.bold = True
            p.font.color.rgb = COLOR_PRIMARY
        return shape

    # =========================================================================
    # SLIDE 1: PROBLEM STATEMENT & CONTEXT
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_header(s1, "Problem Statement 01 • VIT Mapathon",
               "Agricultural Land Parcel and Crop Identification",
               "Study Region: Ambasamudram & Cheranmahadevi Taluks, Tirunelveli District, Tamil Nadu")

    # Column 1: Scope & Study Region
    add_card(s1, Inches(0.8), Inches(1.75), Inches(3.6), Inches(5.1), "1. Study Area & Scope")
    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(3.2), Inches(4.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    bullets1 = [
        ("Geographic Extent:", "Ambasamudram Taluk and Cheranmahadevi Taluk in Tirunelveli District, Tamil Nadu."),
        ("Study Area Coverage:", ">= 20 sq. km minimum requirement (Actual implementation: 55.74 sq. km)."),
        ("Center Coordinates:", "Lat 8.70° N, Lon 77.49° E along the Thamirabarani River Basin."),
        ("Target Agricultural Classes:", "Paddy (Wetland crop), Banana (Perennial horticulture), and Other (Fallow & scrub)."),
        ("Open-Source Constraint:", "Zero dependency on proprietary, commercial satellite imagery.")
    ]
    for i, (head, body) in enumerate(bullets1):
        p = tf1.paragraphs[0] if i == 0 else tf1.add_paragraph()
        p.space_after = Pt(10)
        r1 = p.add_run()
        r1.text = head + " "
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_SECONDARY

    # Column 2: Key Challenges
    add_card(s1, Inches(4.8), Inches(1.75), Inches(3.7), Inches(5.1), "2. Operational Challenges")
    tb2 = s1.shapes.add_textbox(Inches(5.0), Inches(2.25), Inches(3.3), Inches(4.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    bullets2 = [
        ("Manual Enumeration Delays:", "Field surveys by village administrative officers require months, costing ₹5,000–₹10,000 per sq. km."),
        ("Spectral & Phenological Overlap:", "Paddy and banana exhibit overlapping high-chlorophyll reflectance signatures in single-date optical images."),
        ("Cadastral Fragmentation:", "Smallholder agricultural parcels in Tamil Nadu are irregular, partitioned by bunds and narrow irrigation canals."),
        ("Delayed Disaster & Subsidy Action:", "Absence of real-time spatial parcel data hampers flood relief allocation and canal water discharge schedules.")
    ]
    for i, (head, body) in enumerate(bullets2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = head + " "
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_SECONDARY

    # Column 3: Objectives
    add_card(s1, Inches(8.9), Inches(1.75), Inches(3.6), Inches(5.1), "3. Solution Objectives")
    tb3 = s1.shapes.add_textbox(Inches(9.1), Inches(2.25), Inches(3.2), Inches(4.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    bullets3 = [
        ("Automated Parcel Delineation:", "Derive field parcel polygons covering >= 20 sq. km using Sentinel-2 L2A optical imagery and OSM infrastructure."),
        ("Multi-Class ML Identification:", "Train a robust Random Forest classifier achieving > 90% accuracy for Paddy, Banana, and Other."),
        ("Prevent Spatial Data Leakage:", "Implement GroupShuffleSplit by unique Parcel ID to guarantee honest validation on unseen farmland."),
        ("Production Web GIS Delivery:", "Develop PostGIS spatial database, FastAPI REST service, and React-Leaflet GIS dashboard.")
    ]
    for i, (head, body) in enumerate(bullets3):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.space_after = Pt(12)
        r1 = p.add_run()
        r1.text = head + " "
        r1.font.bold = True
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = body
        r2.font.size = Pt(10)
        r2.font.color.rgb = COLOR_SECONDARY

    # =========================================================================
    # SLIDE 2: EXISTING IDEAS VS OUR SOLUTION (DISTINGUISHING TABLE)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Comparative Evaluation • Technical Novelty",
               "Existing Approaches vs. Our Proposed Automated GIS Solution",
               "Direct side-by-side differentiation across data source, methodology, validation, and cost")

    table_shape = s2.shapes.add_table(8, 3, Inches(0.8), Inches(1.75), Inches(11.7), Inches(5.1))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(4.6)
    table.columns[2].width = Inches(4.9)

    headers = ["Evaluation Metric", "Conventional / Existing Approach", "Our Proposed Platform"]
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

    comparison_data = [
        ("Data Ingestion", "Sample-based ground surveys, paper revenue records, or costly commercial imagery.", "Open Sentinel-2 Level-2A (10 m) surface reflectance with BOA correction."),
        ("Update Frequency", "Seasonal or annual updates (3 to 12 months reporting lag).", "Dynamic 5-day revisit cycle enabling multi-temporal phenological tracking."),
        ("Field Geometries", "Coarse uniform square grids or aggregated village blocks.", "Organic cadastral parcel boundaries derived from OSM waterways and roads."),
        ("Classification Engine", "Manual NDVI thresholding or single-date spectral slicing.", "Multi-spectral Random Forest ML combining 6 bands and 4 vegetation/water indices."),
        ("Validation Rigor", "Random pixel train/test split (severe spatial autocorrelation leakage).", "Spatial-aware GroupShuffleSplit by Parcel ID evaluating unseen plots."),
        ("Delivery & Access", "Static offline PDFs or desktop GIS shapefiles inaccessible to field officers.", "Production Web GIS (React + Leaflet + PostGIS + FastAPI) with REST APIs."),
        ("Operational Cost", "₹5,000 – ₹10,000 per sq. km for manual field verification.", "< ₹50 per sq. km (100% open-source software and open satellite data).")
    ]

    for row_idx, row_data in enumerate(comparison_data):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_LIGHT_ROW if row_idx % 2 == 1 else COLOR_CARD_BG
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            if col_idx == 0:
                p.font.bold = True
                p.font.color.rgb = COLOR_PRIMARY
            elif col_idx == 1:
                p.font.color.rgb = COLOR_MUTED
            else:
                p.font.bold = (row_idx in [3, 4, 6])
                p.font.color.rgb = COLOR_PRIMARY

    # =========================================================================
    # SLIDE 3: SOLUTION PHASE 1 — SATELLITE REMOTE SENSING & PREPROCESSING
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Technical Solution • Step 1 of 3",
               "Satellite Remote Sensing & Spectral Feature Engineering",
               "Ingesting Sentinel-2 L2A optical scenes, cloud masking, and extracting diagnostic indices")

    # Box 1: Acquisition & Radiometric Calibration
    add_card(s3, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.0), "1. Sentinel-2 L2A Data Processing")
    tb_s3_1 = s3.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(5.2), Inches(3.3))
    tf_s3_1 = tb_s3_1.text_frame
    tf_s3_1.word_wrap = True
    b_s3_1 = [
        ("Sensor & Level:", "Copernicus Sentinel-2 MSI Level-2A Bottom-of-Atmosphere (BOA) surface reflectance product."),
        ("Cloud & Shadow Masking:", "Scene Classification Layer (SCL) filters clouds, thin cirrus, and cloud shadows (< 10% cloud tolerance)."),
        ("Spatial Alignment & CRS:", "Harmonized to standard metric projection WGS 84 / UTM Zone 43N (EPSG:32643) at 10-meter native spatial resolution."),
        ("Multi-temporal Coverage:", "Captures crop vegetative growth and harvesting phenology across the agricultural calendar.")
    ]
    for i, (h, b) in enumerate(b_s3_1):
        p = tf_s3_1.paragraphs[0] if i == 0 else tf_s3_1.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = h + " "
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = b
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_SECONDARY

    # Box 2: Spectral Bands & Indices
    add_card(s3, Inches(6.8), Inches(1.75), Inches(5.7), Inches(4.0), "2. Spectral Bands & Indices Engineered")
    tb_s3_2 = s3.shapes.add_textbox(Inches(7.0), Inches(2.25), Inches(5.3), Inches(3.3))
    tf_s3_2 = tb_s3_2.text_frame
    tf_s3_2.word_wrap = True
    b_s3_2 = [
        ("Core Spectral Bands:", "B02 (Blue), B03 (Green), B04 (Red), B08 (NIR, 10m), B11 (SWIR-1), B12 (SWIR-2, resampled to 10m)."),
        ("NDVI (Normalized Difference Vegetation Index):", "(B08 - B04) / (B08 + B04) — Quantifies canopy chlorophyll biomass."),
        ("EVI (Enhanced Vegetation Index):", "2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1) — Decouples atmospheric drag in dense banana canopies."),
        ("SAVI (Soil-Adjusted Vegetation Index):", "1.5 * (B08 - B04) / (B08 + B04 + 0.5) — Controls for background soil brightness."),
        ("NDWI (Normalized Difference Water Index):", "(B03 - B08) / (B03 + B08) — Distinguishes flooded fields during Paddy transplantation.")
    ]
    for i, (h, b) in enumerate(b_s3_2):
        p = tf_s3_2.paragraphs[0] if i == 0 else tf_s3_2.add_paragraph()
        p.space_after = Pt(6)
        r1 = p.add_run()
        r1.text = h + " "
        r1.font.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = b
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_SECONDARY

    # Bottom Pipeline Summary
    add_card(s3, Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.9))
    tb_flow = s3.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(11.3), Inches(0.7))
    tf_flow = tb_flow.text_frame
    p_f = tf_flow.paragraphs[0]
    p_f.text = "PIPELINE FLOW:  Sentinel-2 L2A (10m) ──► SCL Cloud Mask ──► Metric UTM 43N Grid ──► Band Extraction (B02-B12) ──► Vegetation & Moisture Indices (NDVI, NDWI, EVI, SAVI)"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = COLOR_ACCENT

    # =========================================================================
    # SLIDE 4: SOLUTION PHASE 2 — SPATIAL ML PIPELINE & EVALUATION
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Technical Solution • Step 2 of 3",
               "Spatial-Aware Machine Learning & Model Evaluation",
               "Random Forest crop classifier evaluated with GroupShuffleSplit by Parcel ID")

    # Left Column: Methodology & Metrics
    add_card(s4, Inches(0.8), Inches(1.75), Inches(5.6), Inches(5.1), "ML Classification & Validation Rigor")
    tb_s4 = s4.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(5.2), Inches(4.4))
    tf_s4 = tb_s4.text_frame
    tf_s4.word_wrap = True
    b_s4 = [
        ("Prevention of Spatial Leakage:", "Neighboring pixels in the same plot share identical signatures. GroupShuffleSplit by unique Parcel ID ensures the model is tested on completely unseen fields."),
        ("Random Forest Classifier:", "150 estimators, balanced class weights, Gini criterion. Extracts median zonal spectral features per parcel."),
        ("Multi-Class Probability Output:", "Computes probability scores (prob_paddy, prob_banana, prob_other) and maximum confidence score per parcel."),
        ("Overall Accuracy Achieved:", "91.84% across the spatial test split."),
        ("Macro F1-Score: 0.9082 | Weighted F1-Score: 0.9185", "Balanced performance across all three target agricultural categories:"),
        ("• Paddy Classification:", "Precision: 93.6% | Recall: 94.5% | F1-Score: 94.05%"),
        ("• Banana Classification:", "Precision: 89.8% | Recall: 88.2% | F1-Score: 88.99%"),
        ("• Other / Fallow:", "Precision: 89.6% | Recall: 89.2% | F1-Score: 89.45%")
    ]
    for i, (h, b) in enumerate(b_s4):
        p = tf_s4.paragraphs[0] if i == 0 else tf_s4.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = h + " "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = b
        r2.font.size = Pt(9)
        r2.font.color.rgb = COLOR_SECONDARY

    # Right Column: Images (Confusion Matrix & Feature Importance)
    add_card(s4, Inches(6.8), Inches(1.75), Inches(5.7), Inches(5.1), "Project Evaluation Visualizations")
    if os.path.exists(img_cm):
        s4.shapes.add_picture(img_cm, Inches(7.0), Inches(2.25), width=Inches(2.6), height=Inches(2.1))
        tb_cml = s4.shapes.add_textbox(Inches(7.0), Inches(4.4), Inches(2.6), Inches(0.3))
        p = tb_cml.text_frame.paragraphs[0]
        p.text = "Confusion Matrix Heatmap"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = COLOR_MUTED
    if os.path.exists(img_fi):
        s4.shapes.add_picture(img_fi, Inches(9.75), Inches(2.25), width=Inches(2.6), height=Inches(2.1))
        tb_fil = s4.shapes.add_textbox(Inches(9.75), Inches(4.4), Inches(2.6), Inches(0.3))
        p = tb_fil.text_frame.paragraphs[0]
        p.text = "Feature Importance Ranking"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = COLOR_MUTED

    # Takeaway Note in Card
    tb_take = s4.shapes.add_textbox(Inches(7.0), Inches(4.8), Inches(5.3), Inches(1.8))
    tf_take = tb_take.text_frame
    tf_take.word_wrap = True
    p = tf_take.paragraphs[0]
    p.text = "Key Scientific Finding: NDVI_mean (24.5%) and NDWI_min (18.2%) are the top discriminators. NDWI captures wet soil inundation during early Paddy transplantation, while EVI separates perennial banana foliage from seasonal crops."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_SECONDARY

    # =========================================================================
    # SLIDE 5: SOLUTION PHASE 3 — POSTGIS DATABASE & WEB GIS DASHBOARD
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Technical Solution • Step 3 of 3",
               "PostGIS Spatial Database & Interactive Web GIS Dashboard",
               "FastAPI backend, React-Leaflet GIS interface with Satellite Hybrid and OSM layers")

    # Left Column: Full-Stack Architecture
    add_card(s5, Inches(0.8), Inches(1.75), Inches(5.2), Inches(5.1), "Full-Stack Geospatial Architecture")
    tb_s5 = s5.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.4))
    tf_s5 = tb_s5.text_frame
    tf_s5.word_wrap = True
    b_s5 = [
        ("PostGIS Spatial Database:", "PostgreSQL schema with spatial GIST indexing on geom GEOMETRY(Geometry, 4326) enabling sub-millisecond bounding box spatial queries."),
        ("FastAPI REST Service (/api):", "Provides high-throughput endpoints for /parcels (filters by crop, confidence), /statistics, /metrics, /places, and /infrastructure."),
        ("Zero-Crash Offline Resilience:", "Seamlessly executes live PostGIS SQL queries when database is active, with instant fallback to verified GeoJSON deliverables."),
        ("Satellite Hybrid Basemap:", "Combines Esri World Satellite Imagery with official Tamil Nadu boundaries, district borders, town names, and street networks."),
        ("Cadastral Parcel Inspector:", "Interactive popups display Parcel ID, Village, crop classification, confidence %, metric area (ha, acres, sq. km), and class probabilities."),
        ("Real OSM Infrastructure:", "Overlays 252 real vector waterways (Thamirabarani River) and State Highway 41 (SH-41) alongside 13 verified revenue villages.")
    ]
    for i, (h, b) in enumerate(b_s5):
        p = tf_s5.paragraphs[0] if i == 0 else tf_s5.add_paragraph()
        p.space_after = Pt(7)
        r1 = p.add_run()
        r1.text = h + " "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = b
        r2.font.size = Pt(9)
        r2.font.color.rgb = COLOR_SECONDARY

    # Right Column: Dashboard Screenshot
    add_card(s5, Inches(6.3), Inches(1.75), Inches(6.2), Inches(5.1), "Live Dashboard (Ambasamudram & Cheranmahadevi)")
    if os.path.exists(img_dash):
        s5.shapes.add_picture(img_dash, Inches(6.45), Inches(2.25), width=Inches(5.9), height=Inches(3.7))
        tb_cap = s5.shapes.add_textbox(Inches(6.45), Inches(6.05), Inches(5.9), Inches(0.6))
        p = tb_cap.text_frame.paragraphs[0]
        p.text = "Operational Dashboard (localhost:5174): Displays 1,050 organic parcels (55.74 km²) across Tirunelveli District, dual-taluk toggles, confidence slider, and parcel inspector."
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_MUTED

    # Save presentation
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(output_dir, exist_ok=True)
    ppt_path = os.path.join(output_dir, "VIT_MAPATHON_Presentation.pptx")
    prs.save(ppt_path)
    print(f"Presentation saved successfully to: {ppt_path}")

    # Also save to root and brain directory for easy access
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../VIT_MAPATHON_Presentation.pptx"))
    prs.save(root_path)
    print(f"Presentation also saved to root: {root_path}")

    brain_ppt = os.path.join(brain_dir, "VIT_MAPATHON_Presentation.pptx")
    prs.save(brain_ppt)
    print(f"Presentation saved to artifact directory: {brain_ppt}")

if __name__ == "__main__":
    create_presentation()
