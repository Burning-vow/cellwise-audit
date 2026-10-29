import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu = 60.0
    sigma = 25.0
    p = 20.0
    c = 12.0
    s = 7.0
    
    if args.pert == 'c_up':
        c += 1.0
    elif args.pert == 'lam_up':
        mu += 5.0
    elif args.pert == 'mu_up':
        sigma += 5.0
        
    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)
    
    # Inverse normal CDF approximation for standard normal
    def inv_norm_cdf(p_val):
        # Rational approximation for central range
        if p_val <= 0: return -float('inf')
        if p_val >= 1: return float('inf')
        
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479430692340e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.618866141483772e+02, -1.324992083988872e+02, 5.938520729796010e+01, -4.968811331704886e+00]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.421187894709552e+00, 2.970400693520003e+00]
        
        plow = 0.02425
        phigh = 1 - plow
        
        if p_val < plow:
            q = math.sqrt(-2 * math.log(p_val))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p_val > phigh:
            q = math.sqrt(-2 * math.log(1 - p_val))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        else:
            q = p_val - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

    z_opt = inv_norm_cdf(critical_ratio)
    q_opt = mu + sigma * z_opt
    q_opt_int = int(round(q_opt))
    
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    total_horizon_days = max(1, int(args.horizon))
    
    for i in range(args.seeds):
        current_seed = args.seed_start + i
        rng = random.Random(current_seed)
        seed_list.append(current_seed)
        
        daily_profits = []
        for _ in range(total_horizon_days):
            demand = rng.gauss(mu, sigma)
            demand = max(0, demand) # Demand cannot be negative
            
            sold = min(demand, q_opt_int)
            leftover = max(0, q_opt_int - demand)
            
            revenue = sold * p
            cost = q_opt_int * c
            salvage = leftover * s
            
            profit = revenue - cost + salvage
            daily_profits.append(profit)
            
        exp_profit = sum(daily_profits) / len(daily_profits)
        per_seed_exp_profit.append(exp_profit)
        per_seed_q.append(q_opt_int)

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": q_opt_int,
        "runtime_units": total_horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
