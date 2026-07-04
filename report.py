import os
import datetime
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#003366"))
        
        stn_name = getattr(self, "cwc_site_name", "NADI AI Hydro Analysis")
        self.drawString(54, 750, f"STATION REPORT: {str(stn_name).upper()}")
        self.drawRightString(letter[0] - 54, 750, "NADI AI HYDROLOGIC SUITE")
        
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 742, letter[0] - 54, 742)
        
        self.line(54, 48, letter[0] - 54, 48)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(54, 34, "Confidential - Academic & Research Engineering Analysis Artifact")
        self.drawRightString(letter[0] - 54, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def safe_extract(obj, key, default="N/A", idx=None):
    """Safely extracts data whether the backend returned a dictionary, Series, list, or tuple."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    if hasattr(obj, 'get') and not isinstance(obj, (list, tuple)):
        try: return obj.get(key, default)
        except: pass
    if isinstance(obj, (list, tuple, np.ndarray)):
        if idx is not None and idx < len(obj):
            return obj[idx]
    return default

def build_pdf_report(filename, meta, df_stats, df_ams, outliers_iqr, 
                     gb_bounds, pettitt_res, cusum_res, mk_res, 
                     top_fitted, return_periods, design_matrix):
    
    cwc_site_name = safe_extract(meta, 'cwc_site_name', 'N/A')
    
    doc = SimpleDocTemplate(
        filename, pagesize=letter,
        leftMargin=54, rightMargin=54, topMargin=72, bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=34, leading=40,
        textColor=colors.HexColor("#003366"), alignment=1, spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'CoverSub', parent=styles['Normal'], fontName='Helvetica', fontSize=14, leading=18,
        textColor=colors.HexColor("#444444"), alignment=1, spaceAfter=40
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20,
        textColor=colors.HexColor("#003366"), spaceBefore=18, spaceAfter=10, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14,
        textColor=colors.HexColor("#222222"), spaceAfter=8
    )
    table_text = ParagraphStyle('TableText', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
    table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    story = []
    
    # TITLE PAGE
    story.append(Spacer(1, 100))
    story.append(Paragraph("NADI AI", title_style))
    story.append(Paragraph("💧 Advanced Hydrologic Data Analysis Suite", subtitle_style))
    story.append(Spacer(1, 20))
    
    author_text = """
    <b>Developed by:</b> Narala Venkatesh<br/>
    MTech Water Resources Engineering<br/>
    National Institute of Technology, Warangal (NITW)<br/>
    <b>Contact/Suggestions:</b> venkateshnarala387@gmail.com
    """
    story.append(Paragraph(author_text, ParagraphStyle('Auth', parent=body_style, alignment=1, fontSize=11, leading=16)))
    story.append(Spacer(1, 50))
    
    warning_box = """
    <i><b>Disclaimer Note:</b> This engineering diagnostic profile report is automatically compiled by AI 
    analytical frameworks. It may contain mathematical anomalies or processing mismatches. 
    Please exercise strict engineering caution and cross-verify parameters before field deployment.</i>
    """
    story.append(Paragraph(warning_box, ParagraphStyle('Warn', parent=body_style, alignment=1, textColor=colors.HexColor("#990000"), fontSize=9.5)))
    story.append(Spacer(1, 40))
    
    run_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Report Generation Artifact Timestamp:</b> {run_date}", ParagraphStyle('MetaStr', parent=body_style, alignment=1, fontSize=9, textColor=colors.HexColor("#666666"))))
    story.append(PageBreak())
    
    # SECTION 1: STATION INFORMATION
    story.append(Paragraph("1. Station Information & Catchment Attributes", h1_style))
    
    attr_list = [
        ("cwc_site_name", "Name of the gauging site (CWC)", 0),
        ("river_basin", "Name of the primary river basin network", 0),
        ("cwc_river", "Specific river channel or major tributary system", 0),
        ("flow_availability", "Percentage data duration availability (%)", 0),
        ("cwc_lat", "Gauging station Latitude coordinate (°)", 0),
        ("cwc_lon", "Gauging station Longitude coordinate (°)", 0),
        ("elev_mean", "Catchment mean elevation (m)", 0),
        ("elev_min", "Catchment minimum elevation (m)", 0),
        ("elev_max", "Catchment maximum elevation (m)", 0),
        ("slope_mean", "Catchment average basin slope (%)", 0),
        ("cwc_area", "Catchment drainage drainage area (km²)", 0),
        ("water_frac", "Water cover fraction (2017-2022)", 0),
        ("trees_frac", "Tree canopy spatial fraction", 0),
        ("crops_frac", "Cropland agricultural spatial fraction", 0),
        ("built_area_frac", "Urban built-up area layer fraction", 0),
        ("dom_land_cover", "Dominant catchment classification type", 0),
        ("lai_mean", "Catchment mean Leaf Area Index (MODIS)", 0),
    ]
    
    attr_data = [[Paragraph("Parameter Token", table_header), Paragraph("Description", table_header), Paragraph("Observed Value", table_header)]]
    for key, desc, idx in attr_list:
        val = safe_extract(meta, key, "N/A", idx)
        if isinstance(val, float): val = f"{val:.4f}"
        attr_data.append([Paragraph(key, table_text), Paragraph(desc, table_text), Paragraph(str(val), table_text)])
        
    t1 = Table(attr_data, colWidths=[1.5*inch, 3.2*inch, 2.3*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    
    # SECTION 2: OPERATION DATA OVERVIEW
    story.append(Spacer(1, 15))
    story.append(Paragraph("2. Operational Hydrologic Data Overview", h1_style))
    if isinstance(df_ams, pd.DataFrame) and 'Year' in df_ams.columns:
        years_str = ", ".join([str(y) for y in df_ams['Year'].tolist()])
        story.append(Paragraph(f"<b>Years Matching Strict Quality Filter Trigger (&ge; 50% Annual Data Completeness):</b> {years_str}", body_style))
    
    if os.path.exists("temp_monthly.png"):
        story.append(KeepTogether([Spacer(1, 5), Image("temp_monthly.png", width=6.5*inch, height=2.5*inch)]))
    if os.path.exists("temp_fdc.png"):
        story.append(KeepTogether([Spacer(1, 5), Image("temp_fdc.png", width=6.5*inch, height=2.5*inch)]))
        
    # SECTION 3: OUTLIERS
    story.append(PageBreak())
    story.append(Paragraph("3. Outlier Detection Tests (AMS Inconsistency Checks)", h1_style))
    iqr_outliers = safe_extract(outliers_iqr, 'outliers', [], 0)
    iqr_status = "Outliers Detected" if iqr_outliers else "No Outliers Located"
    
    outlier_intro = f"""
    <b>Interquartile Range (IQR) Outlier Test:</b><br/>
    • Lower Bound = Q1 - 1.5 * IQR; Upper Bound = Q3 + 1.5 * IQR.<br/>
    • Operational Results: <b>{iqr_status}</b>. Identified points: {iqr_outliers}<br/><br/>
    <b>Grubbs-Beck Test (USGS Bulletin 17B Framework):</b><br/>
    • Threshold parametric verification tool to extract localized anomalies.<br/>
    • Low Threshold: {safe_extract(gb_bounds, 'low_threshold', 'N/A', 0)} | High Threshold: {safe_extract(gb_bounds, 'high_threshold', 'N/A', 1)}
    """
    story.append(Paragraph(outlier_intro, body_style))
    if iqr_outliers:
        story.append(Paragraph("⚠️ <b>CRITICAL NOTE:</b> Outliers tracked inside the dataset. Cross-verify readings manually.", ParagraphStyle('W', parent=body_style, textColor=colors.HexColor("#990000"), fontName='Helvetica-Bold')))

    # SECTION 4: CHANGE POINT
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Change-Point Detection (Stationarity Diagnostics)", h1_style))
    p_sig = safe_extract(pettitt_res, 0, "N/A", 0)
    cp_text = f"""
    <b>Pettitt Test Status:</b> Shift Significant = {p_sig} (Statistic K: {safe_extract(pettitt_res, 2, 'N/A', 2)})<br/>
    <b>CUSUM Test:</b> Maximum shift structural location tracked near array entry index {safe_extract(cusum_res, 1, 'N/A', 1)}.
    """
    story.append(Paragraph(cp_text, body_style))

    # SECTION 5: TREND TEST
    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Non-Parametric Trend Diagnostics", h1_style))
    mk_text = f"""
    <b>Mann-Kendall Trend:</b> {safe_extract(mk_res, 0, 'N/A', 0).upper()}<br/>
    • Calculated P-Value structural vector: {safe_extract(mk_res, 2, 0.0, 2):.4f}<br/>
    • Calculated Sen's Slope parameters: {safe_extract(mk_res, 3, 0.0, 3):.4f} units/annum.
    """
    story.append(Paragraph(mk_text, body_style))
    if os.path.exists("temp_ams.png"):
        story.append(KeepTogether([Spacer(1, 5), Image("temp_ams.png", width=6.5*inch, height=2.5*inch)]))

    # SECTION 6 & 7: DISTRIBUTION FITTING & ranks
    story.append(PageBreak())
    story.append(Paragraph("6. Parametric Distribution Model Optimizations", h1_style))
    dist_data = [[Paragraph("Distribution Model Type", table_header), Paragraph("Estimation Technique", table_header), Paragraph("Fitted Parameter Structure Values", table_header)]]
    
    for item in top_fitted:
        name = safe_extract(item, 'name', 'N/A', 0)
        method = safe_extract(item, 'method', 'N/A', 1)
        params = safe_extract(item, 'params', {}, 2)
        p_str = ", ".join([f"{k}={v:.2f}" for k,v in params.items()]) if isinstance(params, dict) else str(params)
        dist_data.append([Paragraph(str(name), table_text), Paragraph(str(method), table_text), Paragraph(p_str, table_text)])
        
    t_d = Table(dist_data, colWidths=[2.2*inch, 1.8*inch, 3.0*inch])
    t_d.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_d)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Goodness-of-Fit (GoF) Assessment Ranks", h1_style))
    gof_data = [[Paragraph("Distribution Model", table_header), Paragraph("Method Type", table_header), Paragraph("Calculated RMSE Metric", table_header)]]
    for item in top_fitted:
        gof_data.append([
            Paragraph(str(safe_extract(item, 'name', 'N/A', 0)), table_text),
            Paragraph(str(safe_extract(item, 'method', 'N/A', 1)), table_text),
            Paragraph(f"{safe_extract(item, 'rmse', 0.0, 3):.4f}", table_text)
        ])
    t_g = Table(gof_data, colWidths=[2.5*inch, 2.2*inch, 2.3*inch])
    t_g.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD"))]))
    story.append(t_g)
    
    if os.path.exists("temp_distfits.png"):
        story.append(KeepTogether([Spacer(1, 5), Image("temp_distfits.png", width=6.5*inch, height=2.5*inch)]))

    # SECTION 8: DESIGN MAGNITUDES
    story.append(PageBreak())
    story.append(Paragraph("8. Design Flood Magnitude Quantile Matrix Projections", h1_style))
    header_row = [Paragraph("Return Period (T)", table_header)]
    for item in top_fitted:
        header_row.append(Paragraph(str(safe_extract(item, 'name', 'N/A', 0)), table_header))
    
    mat_data = [header_row]
    for row in design_matrix:
        cells = [Paragraph(f"<b>{row[0]} Years</b>", table_text)]
        for val in row[1:]:
            cells.append(Paragraph(f"{val:.2f}" if isinstance(val, (int, float)) else str(val), table_text))
        mat_data.append(cells)
        
    c_w = 7.0 / len(mat_data[0])
    t_m = Table(mat_data, colWidths=[c_w*inch]*len(mat_data[0]))
    t_m.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD"))]))
    story.append(t_m)
    
    if os.path.exists("temp_quantiles.png"):
        story.append(KeepTogether([Spacer(1, 5), Image("temp_quantiles.png", width=6.5*inch, height=2.5*inch)]))

    # SECTION 9 & 10: REFERENCES & THANK YOU
    story.append(Spacer(1, 10))
    story.append(Paragraph("9. Academic Reference Page & Data Citations", h1_style))
    ref_txt = "<b>Dataset Reference Citation:</b><br/>Mangukiya, N. K., Kumar, K. B., Dey, P., Sharma, S., Bejagam, V., Mujumdar, P. P., and Sharma, A.: <i>CAMELS-IND: hydrometeorological time series and catchment attributes for 228 catchments in Peninsular India</i>, Earth Syst. Sci. Data, 17, 461–491, https://doi.org/10.5194/essd-17-461-2025, 2025."
    story.append(Paragraph(ref_txt, body_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("10. Thank You Note", h1_style))
    story.append(Paragraph("Thank you for utilizing the <b>NADI AI Suite</b> for your water resources engineering computations. For any issues or suggested updates, contact Narala Venkatesh at venkateshnarala387@gmail.com.", body_style))
    
    def bind_canvas_vars(canvas_obj, doc_obj):
        canvas_obj.cwc_site_name = cwc_site_name

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=lambda c, d: None, onLaterPages=bind_canvas_vars)