import os
import pandas as pd
import numpy as np

# 1. Define the relative base path using forward slashes for cross-platform compatibility
BASE_PATH = "DATA"

def load_stations():
    """
    Dynamically constructs the file path safely across all Operating Systems.
    Reads and returns the station lookup reference.
    """
    file_path = os.path.join(BASE_PATH, "camels_ind_name.csv")
    df = pd.read_csv(file_path)
    return df.sort_values(by="cwc_site_name")

def get_station_full_metadata(gauge_id):
    """
    Safely resolves path environments to parse structural metadata for name, land, and topo profiles.
    Combines fields into a single environment dictionary object.
    """
    # Dynamic path construction replacing hardcoded Windows separators
    path_name = os.path.join(BASE_PATH, "camels_ind_name.csv")
    path_land = os.path.join(BASE_PATH, "camels_ind_land.csv")
    path_topo = os.path.join(BASE_PATH, "camels_ind_topo.csv")
    
    # Read the datasets safely
    df_name = pd.read_csv(path_name)
    df_land = pd.read_csv(path_land)
    df_topo = pd.read_csv(path_topo)
    
    m_name = df_name[df_name['gauge_id'] == gauge_id].to_dict(orient='records')
    m_land = df_land[df_land['gauge_id'] == gauge_id].to_dict(orient='records')
    m_topo = df_topo[df_topo['gauge_id'] == gauge_id].to_dict(orient='records')
    
    meta = {}
    if m_name: meta.update(m_name[0])
    if m_land: meta.update(m_land[0])
    if m_topo: meta.update(m_topo[0])
    return meta

def extract_streamflow(gauge_id):
    """
    Loads raw observed streamflow vectors using dynamic platform paths.
    Processes threshold filters to isolate the Annual Maximum Series (AMS).
    """
    # FIXED: Replaced hardcoded backslash path with os.path.join for Linux cloud containers
    path_flow = os.path.join(BASE_PATH, "streamflow_observed.csv")
    df_flow = pd.read_csv(path_flow)
    
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
