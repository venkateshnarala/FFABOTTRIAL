import pandas as pd
import numpy as np

BASE_PATH = r"C:\Documents\NADIAI\DATA"

def load_stations():
    df = pd.read_csv(f"{BASE_PATH}\\camels_ind_name.csv")
    return df.sort_values(by="cwc_site_name")

def get_station_full_metadata(gauge_id):
    df_name = pd.read_csv(f"{BASE_PATH}\\camels_ind_name.csv")
    df_land = pd.read_csv(f"{BASE_PATH}\\camels_ind_land.csv")
    df_topo = pd.read_csv(f"{BASE_PATH}\\camels_ind_topo.csv")
    
    m_name = df_name[df_name['gauge_id'] == gauge_id].to_dict(orient='records')
    m_land = df_land[df_land['gauge_id'] == gauge_id].to_dict(orient='records')
    m_topo = df_topo[df_topo['gauge_id'] == gauge_id].to_dict(orient='records')
    
    meta = {}
    if m_name: meta.update(m_name[0])
    if m_land: meta.update(m_land[0])
    if m_topo: meta.update(m_topo[0])
    return meta

def extract_streamflow(gauge_id):
    df_flow = pd.read_csv(f"{BASE_PATH}\\streamflow_observed.csv")
    col_name = str(gauge_id)
    if col_name not in df_flow.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    df_stn = df_flow[['year', 'month', 'day', col_name]].copy()
    df_stn.rename(columns={col_name: 'flow'}, inplace=True)
    df_stn['flow'] = pd.to_numeric(df_stn['flow'], errors='coerce')
    
    yearly_stats = []
    valid_years_ams = []
    
    grouped = df_stn.groupby('year')
    for yr, group in grouped:
        total_days = len(group)
        valid_days = group['flow'].notna().sum()
        pct_yr = (valid_days / total_days) * 100 if total_days > 0 else 0
        
        monsoon = group[group['month'].isin([6, 7, 8, 9])]
        total_m = len(monsoon)
        valid_m = monsoon['flow'].notna().sum()
        pct_m = (valid_m / total_m) * 100 if total_m > 0 else 0
        
        yearly_stats.append({
            'Year': int(yr),
            'Annual_Availability_Pct': pct_yr,
            'Monsoon_Availability_Pct': pct_m
        })
        
        if pct_yr >= 50.0:
            valid_years_ams.append(yr)
            
    df_stats = pd.DataFrame(yearly_stats)
    
    ams_list = []
    for yr in valid_years_ams:
        yr_data = df_stn[df_stn['year'] == yr]
        max_val = yr_data['flow'].max()
        if not np.isnan(max_val):
            ams_list.append({'Year': int(yr), 'AMS': max_val})
            
    df_ams = pd.DataFrame(ams_list)
    return df_stn, df_stats, df_ams