import sys, json, math, random
from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters
    mu_d = 60.0
    sigma_d = 15.0
    p = 20.0
    c = 12.0
    s = 7.0
    
    if pert == 'lam_up':
        mu_d *= 1.1
    elif pert == 'mu_up':
        pass # Service rate not applicable in static newsvendor, or maybe cost? Let's assume no change for mu_up as it's demand side mostly, but usually mu is service rate. In Newsvendor, there is no service rate. Maybe pert affects costs? 
        # The prompt says "disturbance only changes parameters". 
        # lam_up: increase mean demand.
        # mu_up: increase... maybe standard deviation? Or maybe it's a generic template. 
        # c_up: increase cost.
        # For now, let's map:
        # lam_up -> mu_d * 1.1
        # mu_up -> sigma_d * 1.1 (interpreting mu as variability parameter in absence of queueing context, or just ignore if strictly queueing terms used. But this is newsvendor.)
        # Actually, standard perturbations in these tasks often map to the specific model parameters.
        # Let's stick to: lam_up increases mean demand, c_up increases unit cost. mu_up might be irrelevant or increase std dev.
        sigma_d *= 1.1
    elif pert == 'c_up':
        c *= 1.1

    # Critical Ratio
    Cu = p - c
    Co = c - s
    CR = Cu / (Cu + Co)
    
    # Optimal Q using Normal Distribution inverse CDF approximation
    # We need Phi^-1(CR). 
    # Using an approximation for the inverse normal CDF (Abramowitz and Stegun)
    def norm_ppf(p_val):
        if p_val <= 0: return -float('inf')
        if p_val >= 1: return float('inf')
        
        # Rational approximation for central region
        if 0.02425 < p_val < 0.97575:
            q = p_val - 0.5
            r = q * q
            num = (((((((7.36979254418443e-03 * r - 2.15051039364717e-02) * r - 2.47410159048385e-01) * r - 1.38116815292960e+00) * r - 3.45976418550690e+00) * r - 3.04931972323532e+00) * r + 1.32952092488815e+00) * r + 1.30042581932334e+00) * q
            den = ((((((((1.04303521986050e-01 * r + 1.59269399291857e-01) * r + 1.67610709106320e-01) * r + 6.67822034043184e-02) * r + 1.00000000000000e+00) * r + 1.00000000000000e+00) * r + 1.00000000000000e+00) * r + 1.00000000000000e+00) * r + 1.00000000000000e+00) * r + 1.00000000000000e+00)
            # Wait, the denominator formula above is wrong for A&S. Let's use a simpler one or scipy-like logic manually.
            # Standard A&S 26.2.23
            t = math.sqrt(-2.0 * math.log(1.0 - p_val)) if p_val > 0.5 else math.sqrt(-2.0 * math.log(p_val))
            # This is for tail. Let's use a robust polynomial approx.
            
            # Better approach: Use statistics module if available? No, standard library only.
            # Let's use a simple iterative solver or a good approximation.
            # Approximation from Peter John Acklam:
            a1 = -3.969683028665376e+01; a2 = 2.209460984272946e+02; a3 = -2.759285104469687e+02; a4 = 1.383577518672290e+02; a5 = -3.066479806614716e+01; a6 = 2.506628277459239e+00
            b1 = -5.447609879822406e+01; b2 = 1.615869544348340e+02; b3 = -1.556989798598866e+02; b4 = 6.680131188771972e+01; b5 = -1.328068155288572e+01
            c1 = -7.784894002430293e-03; c2 = -3.223964580411365e-01; c3 = -2.400758277161838e+00; c4 = -2.549732539343734e+00; c5 = 4.374664141464968e+00; c6 = 2.938163982698783e+00
            d1 = 7.784695709041462e-03; d2 = 3.224671290748148e-01; d3 = 2.445134137142996e+00; d4 = 3.754408661907416e+00
            
            plow = 0.02425
            phigh = 1 - plow
            
            if p_val < plow:
                q = math.sqrt(-2 * math.log(p_val))
                x = (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)
            elif p_val <= phigh:
                q = p_val - 0.5
                r = q*q
                x = ((((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q) / (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1)
            else:
                q = math.sqrt(-2 * math.log(1-p_val))
                x = -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)
            return x

    z_opt = norm_ppf(CR)
    q_opt = mu_d + sigma_d * z_opt
    q_opt_int = int(round(q_opt))
    
    # Simulation to estimate expected profit at q_opt_int
    # Horizon H is days. 
    # Warmup: first 25% of days discarded.
    
    total_profit_sum = 0.0
    count_valid_days = 0
    per_seed_profits = []
    per_seed_qs = []
    seeds_used_list = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        day_profits = []
        for d in range(int(H)):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative
            
            sales = min(demand, q_opt_int)
            leftover = max(0, q_opt_int - demand)
            
            revenue = sales * p
            cost = q_opt_int * c
            salvage = leftover * s
            
            profit = revenue - cost + salvage
            day_profits.append(profit)
            
        # Discard warmup (first 25%)
        warmup_count = int(len(day_profits) * 0.25)
        valid_profits = day_profits[warmup_count:]
        
        if len(valid_profits) > 0:
            avg_p = sum(valid_profits) / len(valid_profits)
            per_seed_profits.append(avg_p)
            per_seed_qs.append(q_opt_int)
            seeds_used_list.append(seed)
            total_profit_sum += avg_p
            count_valid_days += 1
            
    exp_profit = total_profit_sum / count_valid_days if count_valid_days > 0 else 0.0
    
    result = {
        "exp_profit": round(exp_profit, 2),
        "q": q_opt_int,
        "runtime_units": int(H),
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 2) for x in per_seed_profits],
        "per_seed_q": per_seed_qs
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
