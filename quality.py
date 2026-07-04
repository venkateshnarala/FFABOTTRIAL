import numpy as np
import scipy.stats as stats

def iqr_outlier_test(data):
    if len(data) < 4: return []
    q25, q75 = np.percentile(data, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    return [x for x in data if x < lower_bound or x > upper_bound]

def grubbs_beck_test(data):
    n = len(data)
    if n < 3: return None
    log_data = np.log10([x for x in data if x > 0])
    mean_log = np.mean(log_data)
    std_log = np.std(log_data, ddof=1)
    
    # Accurate critical value approximation
    t_val = stats.t.ppf(1 - 0.05 / (2 * n), n - 2)
    g_crit = ((n - 1) / np.sqrt(n)) * np.sqrt((t_val**2) / (n - 2 + t_val**2))
    
    low_threshold = 10**(mean_log - g_crit * std_log)
    high_threshold = 10**(mean_log + g_crit * std_log)
    return low_threshold, high_threshold

def pettitt_test(data):
    n = len(data)
    if n < 4: return None, None
    k = np.zeros(n)
    for t in range(n):
        k[t] = np.sum(np.sign(data[t] - np.array(data)))
    u = np.zeros(n)
    for t in range(1, n):
        u[t] = u[t-1] + np.sum(np.sign(data[t-1] - np.array(data)))
    abs_u = np.abs(u[1:])
    K_max = np.max(abs_u)
    change_point_idx = np.argmax(abs_u) + 1
    p_val = 2.0 * np.exp((-6.0 * (K_max**2)) / (n**3 + n**2))
    return change_point_idx, p_val

def cusum_test(data):
    if len(data) == 0: return np.array([]), 0
    mean_val = np.mean(data)
    cusum_series = np.cumsum(data - mean_val)
    max_idx = np.argmax(np.abs(cusum_series))
    return cusum_series, max_idx