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
    
    seeds_used = []
    per_seed_exp_profit = []
    per_seed_q = []
    
    days_per_unit_time = 1.0 # Assuming horizon is in days or we scale appropriately? 
    # The problem says "daily". Horizon H is simulation time length. 
    # Let's assume 1 unit of time = 1 day for simplicity unless specified otherwise.
    # But the prompt asks for time_unit. Let's use 'day' but options are hour/minute/second.
    # Wait, the prompt says: time_unit 填你程序内部时间轴的单位（hour/minute/second 之一）
    # This implies I must map my daily model to one of these. 
    # Let's say 1 day = 24 hours. So time_unit = 'hour'.
    # Then horizon H is in hours. Number of days = H / 24.
    
    time_unit = 'hour'
    hours_per_day = 24.0
    total_days = a.horizon / hours_per_day
    warmup_fraction = 0.25
    warmup_days = int(total_days * warmup_fraction)
    effective_days = max(1, int(total_days) - warmup_days)
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        profits = []
        
        # Simulate effective_days
        for _ in range(effective_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            revenue = sold * price
            cost_total = q_opt * cost
            salvage_val = leftover * salvage
            
            profit = revenue - cost_total + salvage_val
            profits.append(profit)
            
        exp_p = sum(profits) / len(profits) if profits else 0.0
        
        seeds_used.append(seed)
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        
    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": a.horizon,
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": time_unit,
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
