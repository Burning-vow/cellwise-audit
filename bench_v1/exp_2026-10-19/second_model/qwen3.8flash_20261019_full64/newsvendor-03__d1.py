import json, math, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    mu_d, sigma_d = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 4.0
    
    # Critical fractile for newsvendor
    cu = price - cost
    co = cost - salvage
    cf = cu / (cu + co)
    
    # Optimal q using inverse normal approximation (since no scipy)
    # Using standard normal quantile approximation
    def norm_ppf(p):
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        # Rational approximation for central range
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            return -(t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t))
        else:
            t = math.sqrt(-2 * math.log(1-p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            return t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)
            
    z_opt = norm_ppf(cf)
    q_opt = mu_d + z_opt * sigma_d
    
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    horizon_days = int(a.horizon)
    if horizon_days <= 0: horizon_days = 1
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        
        total_profit = 0.0
        warmup_cutoff = int(horizon_days * 0.25)
        
        for day in range(horizon_days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            sold = min(demand, q_opt)
            unsold = max(0, q_opt - demand)
            profit = price * sold + salvage * unsold - cost * q_opt
            
            if day >= warmup_cutoff:
                total_profit += profit
                
        exp_p = total_profit / max(1, horizon_days - warmup_cutoff)
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        
    avg_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": round(avg_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
