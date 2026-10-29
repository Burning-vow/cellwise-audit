import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 25.0
    p, c, s = 20.0, 12.0, 7.0
    cu = p - c
    co = c - s
    crit_ratio = cu / (cu + co)
    
    # Optimal q via inverse normal CDF approximation for critical fractile
    # Using standard normal quantile approximation
    def norm_ppf(p):
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        # Rational approximation for central range
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
            x = -(t - (2.30753288627045 + 0.270610566351444*t)/(1+1.28298290832394*t+0.32196695604982*t**2))
        else:
            t = math.sqrt(-2 * math.log(1-p))
            x = t - (2.30753288627045 + 0.270610566351444*t)/(1+1.28298290832394*t+0.32196695604982*t**2)
        return x

    z_opt = norm_ppf(crit_ratio)
    q_opt = mu_d + sigma_d * z_opt
    
    # Simulation to estimate expected profit at optimal q and verify
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    per_seed_exp_profit = []
    per_seed_q = []
    
    horizon_days = int(args.horizon) # Assuming horizon is in days for this problem context or just number of iterations
    # The prompt says H is simulation time length in time_unit. 
    # For newsvendor, "time" is usually discrete days. Let's assume 1 unit = 1 day.
    # If H is large, we simulate H days.
    
    total_profit_sum = 0.0
    count = 0
    
    for seed in seed_list:
        rng = random.Random(seed)
        daily_profits = []
        
        # Warmup removal: first 25%
        warmup_count = int(horizon_days * 0.25)
        
        for _ in range(horizon_days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            revenue = sold * p + leftover * s
            cost = q_opt * c
            profit = revenue - cost
            daily_profits.append(profit)
            
        # Calculate average over non-warmup period
        valid_profits = daily_profits[warmup_count:]
        if not valid_profits:
            avg_p = sum(daily_profits)/len(daily_profits) if daily_profits else 0
        else:
            avg_p = sum(valid_profits)/len(valid_profits)
            
        per_seed_exp_profit.append(avg_p)
        per_seed_q.append(q_opt)
        total_profit_sum += avg_p
        count += 1
        
    exp_profit = total_profit_sum / count if count > 0 else 0.0
    
    result = {
        "exp_profit": round(exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
