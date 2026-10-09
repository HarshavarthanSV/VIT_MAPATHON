"""
VIT MAPATHON — Member 1 (AI / ML & Backend Systems)
Professional Cadastral & Temporal PDF Report Generator using ReportLab.
Generates publication-ready agronomic and remote sensing reports for Ambasamudram & Cheranmahadevi.
"""

import io
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def build_agricultural_pdf_report(
    summary_data: dict,
    taluk_acreage_data: list,
    metrics_data: dict,
    temporal_data: dict
) -> bytes:
    """
    Builds a professional multi-page PDF report containing:
    1. Executive Summary & AOI Overview
    2. Cadastral Land Parcel Acreage Breakdown (Paddy, Banana, Other)
    3. Multi-Temporal Sentinel-2 Comparison (Period 1 vs Period 2)
    4. Machine Learning Model Performance Metrics
    5. AI Agronomic Recommendations to Improve Next Cultivation
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Color Tokens
    c_primary = colors.HexColor("#1e3a8a")      # Dark Navy
    c_secondary = colors.HexColor("#0284c7")    # Sky Blue
    c_paddy = colors.HexColor("#15803d")        # Forest Green
    c_banana = colors.HexColor("#b45309")       # Amber Brown
    c_other = colors.HexColor("#6b21a8")        # Deep Purple
    c_slate_dark = colors.HexColor("#0f172a")
    c_slate_muted = colors.HexColor("#475569")
    c_border = colors.HexColor("#cbd5e1")
    c_bg_light = colors.HexColor("#f8fafc")

    # Typography Styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        alignment=TA_LEFT
    )

    style_meta = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=c_slate_muted,
        alignment=TA_RIGHT
    )

    style_h1 = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=4
    )

    style_body = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_slate_dark,
        alignment=TA_JUSTIFY
    )

    style_cell = ParagraphStyle(
        'Cell_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=c_slate_dark
    )

    style_cell_bold = ParagraphStyle(
        'Cell_Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_slate_dark
    )

    style_cell_header = ParagraphStyle(
        'Cell_Header',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # --- HEADER BLOCK ---
    header_data = [
        [
            Paragraph("<b>VIT MAPATHON 2026</b><br/><font size='10' color='#1e3a8a'>Agricultural Land Parcel & Multi-Temporal Crop Assessment Report</font>", style_title),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}<br/><b>AOI:</b> Ambasamudram & Cheranmahadevi<br/><b>Sensor:</b> Sentinel-2 L2A (10m MSI)", style_meta)
        ]
    ]
    t_header = Table(header_data, colWidths=[360, 160])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceBefore=4, spaceAfter=8))

    # --- SECTION 1: STUDY AREA EXECUTIVE SUMMARY ---
    total_parcels = summary_data.get("total_parcels", 293)
    total_ha = summary_data.get("total_parcels_area_hectares", 171.65)
    study_area_km2 = summary_data.get("total_study_area_sq_km", 119.41)
    mean_conf = summary_data.get("overall_mean_confidence", 0.9767)

    overall_metrics = metrics_data.get("overall", {})
    model_name = metrics_data.get("model_name", "XGBoost_Advanced")
    model_acc = overall_metrics.get("test_accuracy", overall_metrics.get("accuracy", 0.9153))
    macro_f1 = overall_metrics.get("test_f1_macro", 0.9114)

    story.append(Paragraph("1. Geographic Study Area & Cadastral Overview", style_h1))
    story.append(Paragraph(
        "This evaluation report covers the agricultural extent of <b>Ambasamudram</b> and <b>Cheranmahadevi</b> Taluks "
        "in Tirunelveli District, Tamil Nadu. The region encompasses the fertile alluvial plains of the <b>Thamirabarani River Basin</b>, "
        "relying on surface canal irrigation networks and the Northeast Monsoon. A total of "
        f"<b>{total_parcels} cadastral land parcels</b> covering <b>{total_ha:.2f} hectares ({total_ha*2.47105:.2f} acres)</b> "
        "have been classified and monitored across multi-temporal Sentinel-2 satellite stacks.",
        style_body
    ))
    story.append(Spacer(1, 6))

    # Summary KPI Box
    kpi_table_data = [
        [
            Paragraph(f"<b>Study Area</b><br/>{study_area_km2:.2f} km² (AOI)", style_cell_bold),
            Paragraph(f"<b>Classified Parcels</b><br/>{total_parcels} Polygons", style_cell_bold),
            Paragraph(f"<b>Parcel Extent</b><br/>{total_ha:.1f} ha ({total_ha*2.47105:.1f} ac)", style_cell_bold),
            Paragraph(f"<b>{model_name} Accuracy</b><br/>{model_acc*100:.1f}% (F1: {macro_f1*100:.1f}%)", style_cell_bold),
            Paragraph(f"<b>Mean Confidence</b><br/>{mean_conf*100:.1f}%", style_cell_bold)
        ]
    ]
    t_kpi = Table(kpi_table_data, colWidths=[104, 104, 104, 104, 104])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # --- SECTION 2: TALUK-WISE CROP ACREAGE BREAKDOWN ---
    story.append(Paragraph("2. Taluk-Wise Cadastral Crop Distribution", style_h1))
    
    acreage_rows = [
        [
            Paragraph("Taluk Division", style_cell_header),
            Paragraph("Crop Classification", style_cell_header),
            Paragraph("Parcels", style_cell_header),
            Paragraph("Area (Hectares)", style_cell_header),
            Paragraph("Area (Acres)", style_cell_header),
            Paragraph("Taluk Share", style_cell_header)
        ]
    ]

    for item in taluk_acreage_data:
        crop_name = item.get("crop", "")
        if crop_name == "Paddy":
            crop_label = "<font color='#15803d'><b>Paddy (நெல்)</b></font>"
        elif crop_name == "Banana":
            crop_label = "<font color='#b45309'><b>Banana (வாழை)</b></font>"
        elif crop_name == "Other":
            crop_label = "<font color='#6b21a8'><b>Other / Fallow</b></font>"
        else:
            crop_label = f"<b>{crop_name}</b>"

        acreage_rows.append([
            Paragraph(item.get("taluk", ""), style_cell_bold),
            Paragraph(crop_label, style_cell),
            Paragraph(str(item.get("parcel_count", "")), style_cell),
            Paragraph(f"{item.get('area_hectares', 0.0):.2f} ha", style_cell),
            Paragraph(f"{item.get('area_acres', 0.0):.2f} ac", style_cell),
            Paragraph(f"{item.get('percentage_of_taluk', 0.0):.1f}%", style_cell)
        ])

    t_acreage = Table(acreage_rows, colWidths=[100, 120, 60, 80, 80, 80])
    t_acreage.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(t_acreage)
    story.append(Spacer(1, 10))

    # --- SECTION 3: MULTI-TEMPORAL SENTINEL-2 COMPARISON ---
    temp_p1 = temporal_data.get("period_1", {})
    temp_p2 = temporal_data.get("period_2", {})
    deltas = temporal_data.get("deltas", {})

    p1_paddy = temp_p1.get("paddy_area_ha", 59.47)
    p2_paddy = temp_p2.get("paddy_area_ha", 76.29)
    d_paddy = deltas.get("paddy_area_ha_delta", round(p2_paddy - p1_paddy, 2))
    p_paddy = deltas.get("paddy_pct_delta", round((d_paddy / p1_paddy * 100) if p1_paddy > 0 else 0, 1))

    p1_banana = temp_p1.get("banana_area_ha", 53.15)
    p2_banana = temp_p2.get("banana_area_ha", 53.15)
    d_banana = deltas.get("banana_area_ha_delta", round(p2_banana - p1_banana, 2))
    p_banana = deltas.get("banana_pct_delta", round((d_banana / p1_banana * 100) if p1_banana > 0 else 0, 1))

    p1_other = temp_p1.get("other_area_ha", 59.04)
    p2_other = temp_p2.get("other_area_ha", 42.22)
    d_other = deltas.get("other_area_ha_delta", round(p2_other - p1_other, 2))
    p_other = deltas.get("other_pct_delta", round((d_other / p1_other * 100) if p1_other > 0 else 0, 1))

    m1_ndvi = temp_p1.get("mean_ndvi", 0.213)
    m2_ndvi = temp_p2.get("mean_ndvi", 0.362)
    p_ndvi = deltas.get("ndvi_pct_delta", round((m2_ndvi - m1_ndvi) / m1_ndvi * 100 if m1_ndvi > 0 else 0, 1))

    m1_ndwi = temp_p1.get("mean_ndwi", -0.242)
    m2_ndwi = temp_p2.get("mean_ndwi", -0.361)
    p_ndwi = deltas.get("ndwi_pct_delta", round((m2_ndwi - m1_ndwi) / abs(m1_ndwi) * 100 if m1_ndwi != 0 else 0, 1))

    p1_name = temp_p1.get("short_name", "Period 1")
    p2_name = temp_p2.get("short_name", "Period 2")
    p1_tf = temp_p1.get("timeframe", "")
    p2_tf = temp_p2.get("timeframe", "")

    story.append(Paragraph("3. Multi-Temporal Remote Sensing Comparison (Period 1 vs Period 2)", style_h1))
    story.append(Paragraph(
        "A multi-temporal bi-seasonal analysis was performed using Sentinel-2 L2A stacks comparing "
        f"<b>{p1_name}</b> and <b>{p2_name}</b>. "
        "The comparison illustrates vegetative vigor (NDVI), canopy moisture (NDWI), and fallow land dynamics:",
        style_body
    ))
    story.append(Spacer(1, 6))

    temp_table_data = [
        [
            Paragraph("Agronomic & Spectral Metric", style_cell_header),
            Paragraph(f"{p1_name}<br/><font size='7'>{p1_tf}</font>", style_cell_header),
            Paragraph(f"{p2_name}<br/><font size='7'>{p2_tf}</font>", style_cell_header),
            Paragraph("Net Shift (Δ)", style_cell_header),
            Paragraph("Seasonal Dynamic", style_cell_header)
        ],
        [
            Paragraph("<b>Paddy Cultivated Area</b>", style_cell),
            Paragraph(f"{p1_paddy:.2f} ha", style_cell),
            Paragraph(f"{p2_paddy:.2f} ha", style_cell),
            Paragraph(f"<font color='#15803d'><b>{d_paddy:+.2f} ha ({p_paddy:+.1f}%)</b></font>", style_cell),
            Paragraph("Monsoon canal expansion", style_cell)
        ],
        [
            Paragraph("<b>Banana Plantation Area</b>", style_cell),
            Paragraph(f"{p1_banana:.2f} ha", style_cell),
            Paragraph(f"{p2_banana:.2f} ha", style_cell),
            Paragraph(f"<font color='#b45309'><b>{d_banana:+.2f} ha ({p_banana:+.1f}%)</b></font>", style_cell),
            Paragraph("Perennial stable crop canopy", style_cell)
        ],
        [
            Paragraph("<b>Fallow & Other Land</b>", style_cell),
            Paragraph(f"{p1_other:.2f} ha", style_cell),
            Paragraph(f"{p2_other:.2f} ha", style_cell),
            Paragraph(f"<font color='#15803d'><b>{d_other:+.2f} ha ({p_other:+.1f}%)</b></font>", style_cell),
            Paragraph("Converted to irrigated wetland", style_cell)
        ],
        [
            Paragraph("<b>Mean Vegetation Index (NDVI)</b>", style_cell),
            Paragraph(f"{m1_ndvi:.3f}", style_cell),
            Paragraph(f"{m2_ndvi:.3f}", style_cell),
            Paragraph(f"<font color='#15803d'><b>{p_ndvi:+.1f}%</b></font>", style_cell),
            Paragraph("Heading & canopy closure", style_cell)
        ],
        [
            Paragraph("<b>Water/Moisture Index (NDWI)</b>", style_cell),
            Paragraph(f"{m1_ndwi:.3f}", style_cell),
            Paragraph(f"{m2_ndwi:.3f}", style_cell),
            Paragraph(f"<font color='#0284c7'><b>{p_ndwi:+.1f}%</b></font>", style_cell),
            Paragraph("Soil moisture dynamics", style_cell)
        ]
    ]

    t_temp = Table(temp_table_data, colWidths=[130, 95, 95, 100, 100])
    t_temp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
    ]))
    story.append(t_temp)
    story.append(Spacer(1, 10))

    # --- SECTION 4: AI AGRONOMIC RECOMMENDATIONS FOR NEXT CULTIVATION ---
    story.append(Paragraph("4. AI Agronomic Suggestions for Cultivation Optimization", style_h1))
    
    suggestions = temporal_data.get("ai_suggestions", [])
    if not suggestions:
        suggestions = [
            {
                "title": "Post-Harvest Pulse Relay Cropping (பயறு வகை சுழற்சி முறை)",
                "action": "Broadcast certified Blackgram (VBN 8 / ADT 5) or Greengram (CO 8) seeds into standing Samba paddy 7-10 days before harvest.",
                "impact": f"Biological nitrogen fixation of 35-40 kg N/ha across {p2_paddy:.2f} ha of paddy."
            },
            {
                "title": "Precision Nitrogen Top-Dressing via Leaf Color Chart (LCC)",
                "action": "Shift from indiscriminate basal urea broadcasting to 3-split applications calibrated by LCC Score 4.",
                "impact": "Prevents 20% urea volatilization/runoff into the Thamirabarani river."
            },
            {
                "title": "Alternate Wetting & Drying (AWD) in Cheranmahadevi Tail-End",
                "action": "Install perforated field water tubes (Pani Pipe) in Cheranmahadevi tail-end distributaries.",
                "impact": "Conserves 25-30% irrigation water during dry spells and reduces soil root rot."
            },
            {
                "title": "Banana Sigatoka & Pseudostem Management along Riverbanks",
                "action": f"Maintain 2.1m x 2.1m plant spacing across the {p2_banana:.2f} ha banana parcels and apply foliar spray of Pseudomonas fluorescens (0.5%).",
                "impact": "Eliminates high-humidity fungal spread in riverbank clusters."
            },
            {
                "title": f"Drought-Resilient Millet & Sesame Diversification ({p2_other:.2f} ha)",
                "action": f"Mobilize remaining {p2_other:.2f} ha fallow parcels into climate-smart Barnyard Millet (Kudiraivali) or Sesame (TMV 7).",
                "impact": "Requires only 2 protective irrigations, utilizes dryland margins, and prevents weed seed bank propagation."
            }
        ]

    for idx, s in enumerate(suggestions, 1):
        s_title = s.get("title", f"Suggestion {idx}")
        s_action = s.get("action", "")
        s_impact = s.get("impact", "")
        story.append(Paragraph(f"<b>{idx}. {s_title}</b>", ParagraphStyle('RecTitle', parent=style_body, fontName='Helvetica-Bold', textColor=c_primary)))
        story.append(Paragraph(f"{s_action} <i>Impact:</i> {s_impact}", style_body))
        story.append(Spacer(1, 4))

    # --- SIGNATURE & AUDIT BLOCK ---
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=6))
    audit_data = [
        [
            Paragraph(f"<b>Analytical Method:</b> Sentinel-2 Multi-Spectral Stack ({model_name} v2.0)", style_meta),
            Paragraph("<b>Certified by:</b> VIT MAPATHON 2026 GIS & AI Analytics Engine", style_meta)
        ]
    ]
    t_audit = Table(audit_data, colWidths=[260, 260])
    t_audit.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_audit)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
