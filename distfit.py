import numpy as np
import scipy.stats as stats

def fit_distributions(ams_data):
    data = np.sort(ams_data)
    n = len(data)
    results = []
    
    mean_val = np.mean(data)
    std_val = np.std(data, ddof=1)
    
    # 1. Gumbel MOM
    alpha_g = (np.sqrt(6) * std_val) / np.pi
    u_g = mean_val - 0.5772 * alpha_g
    results.append({'Dist': 'Gumbel', 'Method': 'MOM', 'Params': f'u={u_g:.2f}, alpha={alpha_g:.2f}', 'obj': stats.gumbel_r(loc=u_g, scale=alpha_g)})
    
    # 2. Gumbel MLE
    p_g_mle = stats.gumbel_r.fit(data)
    results.append({'Dist': 'Gumbel', 'Method': 'MLE', 'Params': f'u={p_g_mle[0]:.2f}, alpha={p_g_mle[1]:.2f}', 'obj': stats.gumbel_r(loc=p_g_mle[0], scale=p_g_mle[1])})
    
    # 3. Normal MOM
    results.append({'Dist': 'Normal', 'Method': 'MOM', 'Params': f'mu={mean_val:.2f}, sigma={std_val:.2f}', 'obj': stats.norm(loc=mean_val, scale=std_val)})
    
    # 4. Lognormal MOM
    if np.all(data > 0):
        log_data = np.log(data)
        mu_log = np.mean(log_data)
        sigma_log = np.std(log_data, ddof=1)
        results.append({'Dist': 'Log-Normal', 'Method': 'MOM', 'Params': f'mu_log={mu_log:.2f}, sigma_log={sigma_log:.2f}', 'obj': stats.lognorm(s=sigma_log, scale=np.exp(mu_log))})
    
    # 5. GEV MLE
    try:
        p_gev = stats.genextreme.fit(data)
        results.append({'Dist': 'GEV', 'Method': 'MLE', 'Params': f'c={p_gev[0]:.2f}, loc={p_gev[1]:.2f}, scale={p_gev[2]:.2f}', 'obj': stats.genextreme(c=p_gev[0], loc=p_gev[1], scale=p_gev[2])})
    except: pass

    # Compute goodness criteria and rank by RMSE
    m = np.arange(1, n + 1)
    p_emp = m / (n + 1)
    
    evaluated = []
    for item in results:
        dist_obj = item['obj']
        p_theo = dist_obj.cdf(data)
        rmse = np.sqrt(np.mean((p_theo - p_emp)**2))
        ks_stat, _ = stats.kstest(data, dist_obj.cdf)
        
        item['RMSE'] = rmse
        item['KS'] = ks_stat
        evaluated.append(item)
        
    evaluated.sort(key=lambda x: x['RMSE'])
    return evaluated[:5]

def estimate_quantiles(dist_dict, return_periods):
    dist_obj = dist_dict['obj']
    quantiles = {}
    for T in return_periods:
        p = 1.0 - (1.0 / T)
        quantiles[T] = dist_obj.ppf(p)
    return quantiles