import numpy as np
import scipy.stats as stats

def mann_kendall_test(years, ams_data):
    n = len(ams_data)
    if n < 4: return "Insuff. Data", 0, 1.0, 0.0
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += np.sign(ams_data[j] - ams_data[i])
            
    unique_x, counts = np.unique(ams_data, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5)) / 18.0
    if len(unique_x) != n:
        for count in counts:
            if count > 1:
                var_s -= (count * (count - 1) * (2 * count + 5)) / 18.0
                
    if s > 0: z = (s - 1) / np.sqrt(var_s)
    elif s < 0: z = (s + 1) / np.sqrt(var_s)
    else: z = 0.0
        
    p_val = 2 * (1 - stats.norm.cdf(np.abs(z)))
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            if (years[j] - years[i]) != 0:
                slopes.append((ams_data[j] - ams_data[i]) / (years[j] - years[i]))
    sens_slope = np.median(slopes) if slopes else 0.0
    
    trend_result = "No Trend"
    if p_val < 0.05:
        trend_result = "Increasing" if s > 0 else "Decreasing"
        
    return trend_result, s, p_val, sens_slope