import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    p = 20.0
    c = 12.0
    s = 7.0
    
    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)
    
    # Inverse normal approximation for optimal q
    # Using standard library only, no scipy. 
    # We can use a simple approximation or just simulate to find best q if needed, 
    # but Newsvendor has closed form: q* = mu + sigma * z_alpha
    # z_alpha is inverse CDF of standard normal at critical_ratio.
    # Approximation for inverse normal CDF (Abramowitz and Stegun):
    def inv_norm(p_val):
        if p_val <= 0: return -math.inf
        if p_val >= 1: return math.inf
        if p_val < 0.5:
            return -inv_norm(1 - p_val)
        
        t = math.sqrt(-2 * math.log(1 - p_val))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)

    z_alpha = inv_norm(critical_ratio)
    q_opt = mu_d + sigma_d * z_alpha
    
    # Simulation to verify expected profit
    seeds_used = []
    per_seed_exp_profit = []
    per_seed_q = []
    
    horizon_days = int(args.horizon)
    if horizon_days <= 0: horizon_days = 1
    
    warmup_fraction = 0.25
    warmup_days = int(horizon_days * warmup_fraction)
    
    total_profit_sum = 0.0
    count_valid = 0
    
    all_profits = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        day_profits = []
        for _ in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            revenue = sold * p
            cost = q_opt * c
            salvage = leftover * s
            
            profit = revenue - cost + salvage
            day_profits.append(profit)
        
        # Discard warmup
        valid_profits = day_profits[warmup_days:]
        if not valid_profits:
            avg_p = sum(day_profits)/len(day_profits)
        else:
            avg_p = sum(valid_profits)/len(valid_profits)
            
        per_seed_exp_profit.append(avg_p)
        per_seed_q.append(q_opt)
        
        total_profit_sum += avg_p
        count_valid += 1
        
    overall_exp_profit = total_profit_sum / count_valid if count_valid > 0 else 0.0
    
    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": horizon_days,
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
