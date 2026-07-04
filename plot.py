import matplotlib.pyplot as plt
import numpy as np

def plot_mean_monthly(df_flow):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    monthly_mean = df_flow.groupby('month')['flow'].mean()
    ax.bar(monthly_mean.index, monthly_mean.values, color='#1f77b4', edgecolor='black')
    ax.set_title("Mean Monthly Hydrograph")
    ax.set_xlabel("Month")
    ax.set_ylabel("Discharge (m3/s)")
    plt.tight_layout()
    plt.savefig("temp_monthly.png", dpi=200)
    plt.close()

def plot_mean_annual(df_flow):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    annual_mean = df_flow.groupby('year')['flow'].mean()
    ax.plot(annual_mean.index, annual_mean.values, marker='o', color='#003366')
    ax.set_title("Mean Annual Streamflow")
    ax.set_xlabel("Year")
    ax.set_ylabel("Discharge (m3/s)")
    plt.tight_layout()
    plt.savefig("temp_annual.png", dpi=200)
    plt.close()

def plot_fdc(df_flow):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    sorted_flow = np.sort(df_flow['flow'].dropna())[::-1]
    n = len(sorted_flow)
    exceedance_p = (np.arange(1, n + 1) / (n + 1)) * 100
    ax.plot(exceedance_p, sorted_flow, color='purple', lw=2)
    ax.set_yscale('log')
    ax.set_title("Flow Duration Curve (FDC)")
    ax.set_xlabel("% Time Exceeded")
    ax.set_ylabel("Discharge (m3/s) [Log Scale]")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("temp_fdc.png", dpi=200)
    plt.close()

def plot_ams_trends(years, ams_data, trend_line=None):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(years, ams_data, color='#aec7e8', alpha=0.7, edgecolor='grey', label='Observed AMS')
    if trend_line is not None:
        ax.plot(years, trend_line, color='red', linestyle='--', lw=2, label="Sen's Slope Trend")
    ax.set_title("Annual Maximum Series & Trends")
    ax.set_xlabel("Year")
    ax.set_ylabel("Peak Flow (m3/s)")
    ax.legend()
    plt.tight_layout()
    plt.savefig("temp_ams.png", dpi=200)
    plt.close()

def plot_top_distributions(ams_data, top_dist_list):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    sorted_data = np.sort(ams_data)
    n = len(sorted_data)
    p_emp = np.arange(1, n + 1) / (n + 1)
    ax.scatter(sorted_data, p_emp, color='black', zorder=5, label='Empirical (Weibull)')
    
    for item in top_dist_list:
        dist_obj = item['obj']
        lbl = f"{item['Dist']} ({item['Method']})"
        x_vals = np.linspace(min(sorted_data)*0.5, max(sorted_data)*1.5, 200)
        ax.plot(x_vals, dist_obj.cdf(x_vals), label=lbl, lw=1.5)
        
    ax.set_title("Theoretical Distributions vs Empirical Data")
    ax.set_xlabel("Peak Discharge (m3/s)")
    ax.set_ylabel("Probability")
    ax.legend()
    plt.tight_layout()
    plt.savefig("temp_distfits.png", dpi=200)
    plt.close()

def plot_quantile_curves(top_dist_list, return_periods):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    from distfit import estimate_quantiles
    for item in top_dist_list:
        q_dict = estimate_quantiles(item, return_periods)
        mags = [q_dict[T] for T in return_periods]
        lbl = f"{item['Dist']} ({item['Method']})"
        ax.plot(return_periods, mags, marker='v', lw=1.5, label=lbl)
    ax.set_xscale('log')
    ax.set_title("Design Flood Quantiles vs Return Period")
    ax.set_xlabel("Return Period T (Years)")
    ax.set_ylabel("Design Discharge (m3/s)")
    ax.legend()
    ax.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig("temp_quantiles.png", dpi=200)
    plt.close()