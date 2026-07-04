import os
import matplotlib.pyplot as plt
import numpy as np

# Ensure clean backend processing on remote servers without display heads
import matplotlib
matplotlib.use('Agg')

def plot_mean_monthly(df_flow):
    """
    Plots the Mean Monthly Hydrograph bar chart.
    Saves to root working folder as 'temp_monthly.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    monthly_mean = df_flow.groupby('month')['flow'].mean()
    
    ax.bar(monthly_mean.index, monthly_mean.values, color='#1f77b4', edgecolor='black')
    ax.set_title("Mean Monthly Hydrograph")
    ax.set_xlabel("Month")
    ax.set_ylabel("Discharge (m³/s)")
    ax.set_xticks(range(1, 13))
    
    plt.tight_layout()
    plt.savefig("temp_monthly.png", dpi=200, bbox_inches='tight')
    plt.close(fig)

def plot_mean_annual(df_flow):
    """
    Plots the Mean Annual Streamflow time series.
    Saves to root working folder as 'temp_annual.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    annual_mean = df_flow.groupby('year')['flow'].mean()
    
    ax.plot(annual_mean.index, annual_mean.values, marker='o', color='#003366', lw=1.5)
    ax.set_title("Mean Annual Streamflow")
    ax.set_xlabel("Year")
    ax.set_ylabel("Discharge (m³/s)")
    
    plt.tight_layout()
    plt.savefig("temp_annual.png", dpi=200, bbox_inches='tight')
    plt.close(fig)

def plot_fdc(df_flow):
    """
    Plots the Flow Duration Curve (FDC) on a semi-log scale.
    Saves to root working folder as 'temp_fdc.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    sorted_flow = np.sort(df_flow['flow'].dropna())[::-1]
    n = len(sorted_flow)
    
    if n > 0:
        exceedance_p = (np.arange(1, n + 1) / (n + 1)) * 100
        ax.plot(exceedance_p, sorted_flow, color='purple', lw=2)
        ax.set_yscale('log')
        ax.set_title("Flow Duration Curve (FDC)")
        ax.set_xlabel("% Time Exceeded")
        ax.set_ylabel("Discharge (m³/s) [Log Scale]")
        ax.grid(True, which="both", ls="--", alpha=0.5)
    else:
        ax.text(0.5, 0.5, "Insufficient Flow Data", transform=ax.transAxes, ha="center")

    plt.tight_layout()
    plt.savefig("temp_fdc.png", dpi=200, bbox_inches='tight')
    plt.close(fig)

def plot_ams_trends(years, ams_data, trend_line=None):
    """
    Plots the Annual Maximum Series (AMS) bar chart with a trend overlay.
    Saves to root working folder as 'temp_ams.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(years, ams_data, color='#aec7e8', alpha=0.7, edgecolor='grey', label='Observed AMS')
    
    if trend_line is not None and len(trend_line) == len(years):
        ax.plot(years, trend_line, color='red', linestyle='--', lw=2, label="Sen's Slope Trend")
        
    ax.set_title("Annual Maximum Series & Trends")
    ax.set_xlabel("Year")
    ax.set_ylabel("Peak Flow (m³/s)")
    ax.legend()
    
    plt.tight_layout()
    plt.savefig("temp_ams.png", dpi=200, bbox_inches='tight')
    plt.close(fig)

def plot_top_distributions(ams_data, top_dist_list):
    """
    Plots the CDF curves of top fitted distributions against empirical data.
    Saves to root working folder as 'temp_distfits.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    sorted_data = np.sort(ams_data)
    n = len(sorted_data)
    
    if n > 0:
        p_emp = np.arange(1, n + 1) / (n + 1)
        ax.scatter(sorted_data, p_emp, color='black', zorder=5, label='Empirical (Weibull)', s=15)
        
        x_vals = np.linspace(max(0.1, min(sorted_data) * 0.5), max(sorted_data) * 1.3, 300)
        
        for item in top_dist_list:
            # Handles both standard scipy object structures or dictionary definitions safely
            dist_obj = item.get('obj') if isinstance(item, dict) else getattr(item, 'obj', None)
            dist_name = item.get('Dist') if isinstance(item, dict) else getattr(item, 'Dist', 'Unknown')
            fit_method = item.get('Method') if isinstance(item, dict) else getattr(item, 'Method', 'MLE')
            
            if dist_obj is not None:
                try:
                    ax.plot(x_vals, dist_obj.cdf(x_vals), label=f"{dist_name} ({fit_method})", lw=1.5)
                except Exception:
                    continue
                    
        ax.set_title("Theoretical Distributions vs Empirical Data")
        ax.set_xlabel("Peak Discharge (m³/s)")
        ax.set_ylabel("Probability")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "No Data for Distribution Plotting", transform=ax.transAxes, ha="center")

    plt.tight_layout()
    plt.savefig("temp_distfits.png", dpi=200, bbox_inches='tight')
    plt.close(fig)

def plot_quantile_curves(top_dist_list, return_periods):
    """
    Plots design flood magnitudes across varying return periods on a log-scale.
    Saves to root working folder as 'temp_quantiles.png'.
    """
    fig, ax = plt.subplots(figsize=(6, 3.5))
    
    # Defensive execution import to decouple module evaluation circular dependencies
    try:
        from distfit import estimate_quantiles
    except ImportError:
        # Fallback if function cannot be localized directly
        def estimate_quantiles(item, periods):
            return {t: 0.0 for t in periods}

    has_plots = False
    for item in top_dist_list:
        try:
            q_dict = estimate_quantiles(item, return_periods)
            mags = [q_dict[T] for T in return_periods]
            
            dist_name = item.get('Dist') if isinstance(item, dict) else getattr(item, 'Dist', 'Unknown')
            fit_method = item.get('Method') if isinstance(item, dict) else getattr(item, 'Method', 'MLE')
            
            ax.plot(return_periods, mags, marker='v', lw=1.5, label=f"{dist_name} ({fit_method})", markersize=4)
            has_plots = True
        except Exception:
            continue
            
    if has_plots:
        ax.set_xscale('log')
        ax.set_title("Design Flood Quantiles vs Return Period")
        ax.set_xlabel("Return Period T (Years)")
        ax.set_ylabel("Design Discharge (m³/s)")
        ax.legend()
        ax.grid(True, which="both", ls="--", alpha=0.5)
    else:
        ax.text(0.5, 0.5, "Quantile Quantities Empty", transform=ax.transAxes, ha="center")

    plt.tight_layout()
    plt.savefig("temp_quantiles.png", dpi=200, bbox_inches='tight')
    plt.close(fig)
