import streamlit as st
import pandas as pd
import numpy as np
import os

import data_collec as dc
import quality as ql
import statisticaltests as stt
import distfit as dfi
import plot as plt_engine
import report as rpt_engine

st.set_page_config(page_title="NADI AI Panel", layout="wide")

# Enhanced Executive Header Block with Custom CSS Brand/Logo Representation
st.markdown("""
    <style>
    .header-container {
        display: flex;
        align-items: center;
        background: linear-gradient(135deg, #002B49 0%, #004B75 100%);
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 25px;
        color: white;
    }
    .logo-badge {
        font-size: 40px;
        background-color: rgba(255, 255, 255, 0.15);
        padding: 10px 18px;
        border-radius: 12px;
        margin-right: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .title-text {
        font-size: 46px;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
        letter-spacing: 0.5px;
    }
    .subtitle-text {
        font-size: 15px;
        margin: 5px 0 0 0;
        color: #E0E8F0;
    }
    </style>
    
    <div class="header-container">
        <div class="logo-badge">💧</div>
        <div>
            <div class="title-text">NADI AI</div>
            <div class="subtitle-text">Developed by: <b>Narala Venkatesh</b>, MTech Water Resources Engineering, NITW</div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.caption("ℹ️ Phase Note: Developing phase. Thanks for using, help us in developing.")
st.divider()

try:
    df_stations = dc.load_stations()
    stn_options = df_stations['cwc_site_name'].tolist()
    selected_stn = st.selectbox("Select station:", stn_options)
    
    stn_row = df_stations[df_stations['cwc_site_name'] == selected_stn].iloc[0]
    target_id = stn_row['gauge_id']
    meta = dc.get_station_full_metadata(target_id)
    
    st.subheader("Station Parameters Preview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Station Name", meta.get('cwc_site_name', 'N/A') if hasattr(meta, 'get') else stn_row.get('cwc_site_name', 'N/A'))
    col2.metric("River Basin", meta.get('river_basin', 'N/A') if hasattr(meta, 'get') else stn_row.get('river_basin', 'N/A'))
    col3.metric("River", meta.get('cwc_river', 'N/A') if hasattr(meta, 'get') else stn_row.get('cwc_river', 'N/A'))
    col4.metric("Flow Availability", f"{meta.get('flow_availability', 'N/A') if hasattr(meta, 'get') else stn_row.get('flow_availability', 'N/A')}%")
    
    st.markdown("---")
    
    df_flow, df_stats, df_ams = dc.extract_streamflow(target_id)
    
    if df_flow.empty:
        st.error("No streamflow record found matching this Gauge Identifier.")
    else:
        if st.button("🚀 Run Analysis & Compile Engineering Artifact", type="primary"):
            if len(df_ams) < 10:
                st.warning(f"Sufficient data is not available for station ({len(df_ams)} years matching >=50% filter). Displaying basic data overview only.")
                st.subheader("Data Cleanliness Summary Matrix")
                st.dataframe(df_stats)
            else:
                with st.spinner("Processing statistical engines and drawing figures..."):
                    ams_years = df_ams['Year'].to_numpy()
                    ams_values = df_ams['AMS'].to_numpy()
                    
                    outliers_iqr = ql.iqr_outlier_test(ams_values)
                    gb_bounds = ql.grubbs_beck_test(ams_values)
                    pettitt_res = ql.pettitt_test(ams_values)
                    cusum_series, cusum_max_idx = ql.cusum_test(ams_values)
                    
                    mk_res = stt.mann_kendall_test(ams_years, ams_values)
                    top_fitted = dfi.fit_distributions(ams_values)
                    
                    plt_engine.plot_mean_monthly(df_flow)
                    plt_engine.plot_mean_annual(df_flow)
                    plt_engine.plot_fdc(df_flow)
                    
                    t_line = ams_years * mk_res[3] + (np.mean(ams_values) - np.mean(ams_years) * mk_res[3])
                    plt_engine.plot_ams_trends(ams_years, ams_values, t_line)
                    plt_engine.plot_top_distributions(ams_values, top_fitted)
                    
                    return_periods = [2, 5, 10, 25, 50, 100, 200, 500, 1000]
                    plt_engine.plot_quantile_curves(top_fitted, return_periods)
                    
                    design_matrix = []
                    for T in return_periods:
                        row_vals = [T]
                        for item in top_fitted:
                            try:
                                q_dict = dfi.estimate_quantiles(item, [T])
                                val = q_dict[T] if isinstance(q_dict, dict) else q_dict[0]
                            except Exception:
                                val = np.nan
                            row_vals.append(val)
                        design_matrix.append(row_vals)
                    
                    pdf_filename = f"NADI_AI_Report_{target_id}.pdf"
                    rpt_engine.build_pdf_report(
                        pdf_filename, meta, df_stats, df_ams, outliers_iqr, 
                        gb_bounds, pettitt_res, (cusum_series, cusum_max_idx), 
                        mk_res, top_fitted, return_periods, design_matrix
                    )
                    
                st.success("✅ Analysis Complete! The comprehensive engineering document is compiled.")
                
                with open(pdf_filename, "rb") as f:
                    st.download_button(
                        label="📥 Download Complete PDF Report",
                        data=f,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
except Exception as e:
    st.error(f"System Pipeline Interrupt: {str(e)}")