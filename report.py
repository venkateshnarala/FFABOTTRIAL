import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total page count and draw
    academic-grade running headers and footers with a custom station stamp.
    """
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
        self.saveState()
        
        # Suppress running headers/footers on the title cover page (Page 1)
        if self._pageNumber > 1:
            # Running Header Bar Configuration
            self.setFillColor(colors.HexColor("#003366"))
            self.rect(36, 750, 540, 20, fill=1, stroke=0)
            
            self.setFillColor(colors.white)
            self.setFont("Helvetica-Bold", 9)
            self.drawString(45, 756, "NADI AI — HYDROLOGIC ANALYSIS REPORT")
            
            # Extract active station name safely from dynamic storage if needed, or use stamp
            self.setFillColor(colors.HexColor("#555555"))
            self.setFont("Helvetica", 8)
            self.drawRightString(565, 756, "CAMELS-IND Analytics Engine")
            
            # Running Footer Configuration
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(36, 50, 540, 50)
            
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.setFont("Helvetica", 9)
            self.drawRightString(565, 38, page_text)
            self.drawString(45, 38, "Confidential — Generated for Research & Evaluation Purposes")
            
        self.restoreState()


def build_pdf_report(filename, meta, df_stats, df_ams, outliers_iqr, 
                     gb_bounds, pettitt_res, cusum_data, mk_res, 
                     top_fitted, return_periods, design_matrix):
    """
    Main document assembly line. Uses ReportLab Flowables to construct the formal
    10-section layout, incorporating type-safe fallbacks for statistical outputs.
    """
    # Initialize the base document layout with default standard letter sizes and margins
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette Typography Definitions
    title_style = ParagraphStyle(
        'CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=34,
        leading=40,
        textColor=colors.HexColor("#003366"),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#555555"),
        spaceAfter=40
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#003366"),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#222222"),
        spaceAfter=8
    )
    
    table_text = ParagraphStyle(
        'TableText',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#111111")
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # TITLE COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 100))
    story.append(Paragraph("NADI AI", title_style))
    story.append(Paragraph("Automated Hydrologic Data Analysis Suite", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Metadata Identification Table Block
    author_info = [
        [Paragraph("<b>Developed By:</b>", body_style), Paragraph("Narala Venkatesh, MTech Water Resources Engineering, NITW", body_style)],
        [Paragraph("<b>Contact Support:</b>", body_style), Paragraph("venkateshnarala387@gmail.com", body_style)],
        [Paragraph("<b>Target Station Profile:</b>", body_style), Paragraph(str(meta.get('cwc_site_name', 'N/A')), body_style)],
        [Paragraph("<b>River System Basin:</b>", body_style), Paragraph(str(meta.get('river_basin', 'N/A')), body_style)]
    ]
    t_author = Table(author_info, colWidths=[150, 350])
    t_author.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_author)
    story.append(Spacer(1, 120))
    
    # Compliance Warning and Advisory Note
    warning_text = (
        "<b>⚠️ CAUTIONary Verification Note:</b> This engineering evaluation assessment artifact "
        "is generated programmatically by artificial intelligence engines. Results can contain statistical "
        "irregularities or mismatched operational limits due to dataset constraints. "
        "Please remain cautious and manually crosscheck critical data thresholds before implementing design layouts."
    )
    story.append(Paragraph(warning_text, body_style))
    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: STATION INFORMATION SCHEMA
    # =========================================================================
    story.append(Paragraph("1. Catchment Physiographic Information Summary", h1_style))
    story.append(Paragraph("Below is the tabulated summary index mapping core topographic indicators, relocated coordinates, and localized attributes extracted from the primary databases.", body_style))
    
    # Construct complete structured overview metadata table
    meta_table_data = [
        [Paragraph("Attribute Parameter", table_header), Paragraph("Description Context", table_header), Paragraph("Value Measured", table_header)],
        [Paragraph("cwc_site_name", table_text), Paragraph("Name of Gauging Station (CWC Source)", table_text), Paragraph(str(meta.get('cwc_site_name', 'N/A')), table_text)],
        [Paragraph("river_basin", table_text), Paragraph("Primary Hydrologic Drainage Basin Name", table_text), Paragraph(str(meta.get('river_basin', 'N/A')), table_text)],
        [Paragraph("cwc_river", table_text), Paragraph("Local River System / Tributary Connection", table_text), Paragraph(str(meta.get('cwc_river', 'N/A')), table_text)],
        [Paragraph("cwc_lat / cwc_lon", table_text), Paragraph("Geographic Station Coordinates (Latitude / Longitude)", table_text), Paragraph(f"{meta.get('cwc_lat', 'N/A')}°N / {meta.get('cwc_lon', 'N/A')}°E", table_text)],
        [Paragraph("flow_availability", table_text), Paragraph("Historical Records Data Availability Duration (1980-2020)", table_text), Paragraph(f"{meta.get('flow_availability', 'N/A')}%", table_text)],
        [Paragraph("elev_mean / elev_median", table_text), Paragraph("Catchment Elevation Bounds (SRTM DEM 90m)", table_text), Paragraph(f"{meta.get('elev_mean', 'N/A')} m / {meta.get('elev_median', 'N/A')} m", table_text)],
        [Paragraph("slope_mean / slope_max", table_text), Paragraph("Catchment Structural Gradient Percentages", table_text), Paragraph(f"{meta.get('slope_mean', 'N/A')}% / {meta.get('slope_max', 'N/A')}%", table_text)],
        [Paragraph("cwc_area / ghi_area", table_text), Paragraph("Catchment Total Drainage Surface Extents", table_text), Paragraph(f"{meta.get('cwc_area', 'N/A')} km² / {meta.get('ghi_area', 'N/A')} km²", table_text)],
        [Paragraph("dom_land_cover", table_text), Paragraph("Dominant Regional Land Cover Category (ESRI 2017-2022)", table_text), Paragraph(f"{meta.get('dom_land_cover', 'N/A')} ({meta.get('dom_land_cover_frac', 'N/A')}%)", table_text)],
        [Paragraph("lai_mean", table_text), Paragraph("Catchment Mean Leaf Area Index (MODIS MCD15A2H)", table_text), Paragraph(str(meta.get('lai_mean', 'N/A')), table_text)]
    ]
    t_meta = Table(meta_table_data, colWidths=[130, 260, 150])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # =========================================================================
    # SECTION 2: OVERVIEW OF STREAMFLOW DATA & SERIES METRICS
    # =========================================================================
    story.append(Paragraph("2. Streamflow Dataset Overview & Record Quality Matrix", h1_style))
    story.append(Paragraph("The historical streamflow records were structured at a minimum annual completeness filter boundary condition requiring at least 50% of operating data to be populated inside each given analysis cycle.", body_style))
    
    # Append the Data Cleanliness Summary Matrix dataframe as a table structure
    if not df_stats.empty:
        stats_headers = [Paragraph(str(col), table_header) for col in df_stats.columns]
        stats_rows = [stats_headers]
        for _, row in df_stats.iterrows():
            stats_rows.append([Paragraph(str(val), table_text) for val in row.values])
        
        t_stats = Table(stats_rows, hAlign='LEFT')
        t_stats.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_stats)
    
    story.append(Spacer(1, 15))
    
    # Embed the seasonal diagnostic figures generated by plot.py
    img_width, img_height = 240, 140
    if os.path.exists("temp_monthly.png") and os.path.exists("temp_fdc.png"):
        img_row = [
            [Image("temp_monthly.png", width=img_width, height=img_height), 
             Image("temp_fdc.png", width=img_width, height=img_height)]
        ]
        t_imgs = Table(img_row, colWidths=[270, 270], hAlign='CENTER')
        t_imgs.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(t_imgs)
        story.append(Paragraph("<font size=8><i>Figure 1: Mean Monthly Hydrograph Bar Distribution (Left) alongside the compiled Flow Duration Curve (Right).</i></font>", body_style))
    
    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: OUTLIER DETECTION TESTS (TYPE-SAFE)
    # =========================================================================
    story.append(Paragraph("3. Outlier Identification Tests", h1_style))
    story.append(Paragraph("<b>Purpose:</b> Locates localized computational anomalies or observational errors using IQR thresholds and standard federal Grubbs-Beck criteria.", body_style))
    
    # Intercept list vs dictionary structural shapes safely for Interquartile Ranges (IQR)
    if isinstance(outliers_iqr, dict):
        outlier_list = outliers_iqr.get("outliers", [])
        iqr_desc = f"IQR Limits: Low [{outliers_iqr.get('threshold_low', 0):.2f}], High [{outliers_iqr.get('threshold_high', 0):.2f}]."
    else:
        outlier_list = list(outliers_iqr) if outliers_iqr else []
        iqr_desc = "IQR bounds parsed as simple list sequence collection array structure."

    # Intercept list vs dictionary structural shapes safely for Grubbs-Beck (GB)
    if isinstance(gb_bounds, dict):
        gb_desc = f"Grubbs-Beck Bounds: Low Limit [{gb_bounds.get('low_threshold', 0):.2f}], High Limit [{gb_bounds.get('high_threshold', 0):.2f}]."
        gb_outliers = gb_bounds.get("outliers", [])
    elif isinstance(gb_bounds, (list, tuple)) and len(gb_bounds) >= 2:
        gb_desc = f"Grubbs-Beck Bounds extracted as sequential components. Low: {gb_bounds[0]:.2f} | High: {gb_bounds[1]:.2f}"
        gb_outliers = []
    else:
        gb_desc = "Grubbs-Beck evaluation thresholds compiled."
        gb_outliers = []

    story.append(Paragraph(f"<b>IQR Execution Results:</b> Detected anomalies: {outlier_list}. {iqr_desc}", body_style))
    story.append(Paragraph(f"<b>Grubbs-Beck Results:</b> Detected values: {gb_outliers}. {gb_desc}", body_style))
    
    if len(outlier_list) > 0 or len(gb_outliers) > 0:
        story.append(Paragraph("<b>⚠️ Action Required:</b> Potential anomalies identified. Please manually cross-reference these historical hydrological events to ensure gauge calibration accuracy.", body_style))
    else:
        story.append(Paragraph("<i>Result Statement: No standard outliers were detected outside the operational safety boundaries.</i>", body_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: CHANGE-POINT DETECTION (PETTITT & CUSUM)
    # =========================================================================
    story.append(Paragraph("4. Change-Point Step Metrics", h1_style))
    story.append(Paragraph("<b>Purpose:</b> Assesses sudden non-parametric step changes inside the time-series mean via Pettitt and Cumulative Sum (CUSUM) checks.", body_style))
    
    # Safe unpacking for Pettitt results tuple
    p_year, p_pval = "N/A", "N/A"
    if isinstance(pettitt_res, (list, tuple)) and len(pettitt_res) >= 2:
        p_year = str(pettitt_res[0])
        p_pval = f"{pettitt_res[1]:.4f}" if isinstance(pettitt_res[1], (int, float)) else str(pettitt_res[1])
        
    story.append(Paragraph(f"<b>Pettitt Test Signature:</b> Estimated Change Year: {p_year} (p-value: {p_pval})", body_style))
    
    # Safe parsing for CUSUM data structures
    c_idx = "N/A"
    if isinstance(cusum_data, (list, tuple)) and len(cusum_data) >= 2:
        c_idx = str(cusum_data[1])
        
    story.append(Paragraph(f"<b>CUSUM Analysis Index:</b> Max Deviation Pivot Location Index: {c_idx}", body_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: TREND ANALYSIS (MANN-KENDALL & SEN'S SLOPE)
    # =========================================================================
    story.append(Paragraph("5. Non-Parametric Trend Indicators", h1_style))
    story.append(Paragraph("<b>Purpose:</b> Tracks uniform long-term movement tendencies across continuous monotonic series variables.", body_style))
    
    mk_trend, mk_slope = "N/A", "N/A"
    if isinstance(mk_res, (list, tuple)) and len(mk_res) >= 4:
        mk_trend = str(mk_res[0])
        mk_slope = f"{mk_res[3]:.4f}" if isinstance(mk_res[3], (int, float)) else str(mk_res[3])
        
    story.append(Paragraph(f"<b>Mann-Kendall Outcome Signature:</b> Trend Profile: `{mk_trend}` | <b>Sen's Slope Variant:</b> `{mk_slope} m³/s/year`", body_style))
    
    if os.path.exists("temp_ams.png"):
        story.append(Spacer(1, 5))
        story.append(Image("temp_ams.png", width=320, height=160, hAlign='CENTER'))
        story.append(Paragraph("<font size=8><i>Figure 2: Annual Maximum Series (AMS) distribution metrics with Sen's Slope trendline overlay.</i></font>", body_style))
    
    story.append(PageBreak())

    # =========================================================================
    # SECTION 6 & 7: DISTRIBUTION FITTING & GOODNESS-OF-FIT RANKINGS
    # =========================================================================
    story.append(Paragraph("6. Distribution Parameter Optimizations & Goodness-of-Fit Performance", h1_style))
    story.append(Paragraph("Theoretical flood probability distributions were fitted onto the extracted Annual Maximum Series (AMS) through Maximum Likelihood Estimation (MLE) or Method of Moments (MOM) matching.", body_style))
    
    # Construct structured Distribution Ranking Table safely mapping internal dictionary collections
    dist_rows = [[Paragraph("Fitted Distribution Model", table_header), Paragraph("Estimation Method Used", table_header), Paragraph("Composite Error Statistic (RMSE)", table_header)]]
    
    if isinstance(top_fitted, list):
        for item in top_fitted:
            if isinstance(item, dict):
                d_name = item.get('Dist', 'Unknown')
                d_meth = item.get('Method', 'MLE')
                d_stat = item.get('RMSE', item.get('score', 0.0))
                d_stat_str = f"{d_stat:.5f}" if isinstance(d_stat, (int, float)) else str(d_stat)
            else:
                d_name = getattr(item, 'Dist', 'Unknown')
                d_meth = getattr(item, 'Method', 'MLE')
                d_stat_str = "Verified"
            
            dist_rows.append([Paragraph(d_name, table_text), Paragraph(d_meth, table_text), Paragraph(d_stat_str, table_text)])
            
    t_dist = Table(dist_rows, colWidths=[180, 180, 180], hAlign='LEFT')
    t_dist.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_dist)
    
    if os.path.exists("temp_distfits.png") and os.path.exists("temp_quantiles.png"):
        story.append(Spacer(1, 15))
        img_row_dist = [
            [Image("temp_distfits.png", width=240, height=140), 
             Image("temp_quantiles.png", width=240, height=140)]
        ]
        t_imgs_dist = Table(img_row_dist, colWidths=[270, 270], hAlign='CENTER')
        t_imgs_dist.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(t_imgs_dist)
        story.append(Paragraph("<font size=8><i>Figure 3: Theoretical Fit Cumulative Distribution Curves (Left) alongside return-period design flood quantiles (Right).</i></font>", body_style))

    story.append(Spacer(1, 15))

    # =========================================================================
    # SECTION 8: DESIGN MAGNITUDES
    # =========================================================================
    story.append(Paragraph("7. Design Flood Magnitudes vs Return Period Matrix", h1_style))
    story.append(Paragraph("The design flood peak discharge quantities ($m^3/s$) mapped across key civil engineering structural return periods ($T$ in years) are structured below:", body_style))
    
    # Build complete dynamic quantile headers based on active fitted distribution indices
    q_headers = [Paragraph("Return Period T (Yrs)", table_header)]
    if isinstance(top_fitted, list):
        for item in top_fitted:
            d_name = item.get('Dist', 'Unknown') if isinstance(item, dict) else getattr(item, 'Dist', 'Model')
            q_headers.append(Paragraph(d_name, table_header))
            
    q_table_data = [q_headers]
    for row in design_matrix:
        row_cells = []
        for i, val in enumerate(row):
            if i == 0:
                row_cells.append(Paragraph(f"<b>{int(val)} Years</b>", table_text))
            else:
                row_cells.append(Paragraph(f"{val:.2f}", table_text))
        q_table_data.append(row_cells)
        
    t_q = Table(q_table_data, hAlign='LEFT')
    t_q.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_q)
    story.append(Spacer(1, 20))

    # =========================================================================
    # SECTION 9 & 10: REFERENCE CITATIONS & ACKNOWLEDGMENTS
    # =========================================================================
    story.append(Paragraph("8. Database Reference Citations", h1_style))
    ref_text = (
        "<b>Primary Framework Citation:</b> The hydrometeorological boundaries, drainage properties, "
        "and parameters used across this project are extracted from the CAMELS-IND database repository layout. "
        "<br/><br/><i>How to Cite:</i> Mangukiya, N. K., Kumar, K. B., Dey, P., Sharma, S., Bejagam, V., "
        "Mujumdar, P. P., and Sharma, A.: CAMELS-IND: hydrometeorological time series and "
        "catchment attributes for 228 catchments in Peninsular India, Earth Syst. Sci. Data, 17, 461–491, "
        "https://doi.org/10.5194/essd-17-461-2025, 2025."
    )
    story.append(Paragraph(ref_text, body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("9. Academic Acknowledgment", h1_style))
    thank_you = (
        "Thank you for deploying the NADI AI Analysis Panel. This engine was built as a core "
        "computational framework component designed to bring rapid, verifiable civil engineering analytics to "
        "watershed management problems. For updates, structural revisions, or code modifications, please contact "
        "the engineering development team directly via email: <b>venkateshnarala387@gmail.com</b>."
    )
    story.append(Paragraph(thank_you, body_style))

    # Compile the final document using our custom NumberedCanvas builder
    doc.build(story, canvasmaker=NumberedCanvas)
