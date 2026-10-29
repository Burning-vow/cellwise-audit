import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    price = 20.0
    cost = 12.0
    salvage = 7.0

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        pass # Not applicable directly to newsvendor params in same way, but keep structure
    elif args.pert == "c_up":
        cost *= 1.1
    
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)
    
    q_optimal = int(round(mu_d + sigma_d * _norm_ppf(critical_ratio)))
    
    exp_profit_total = 0.0
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1
        
    for i in range(args.seeds):
        current_seed = args.seed_start + i
        rng = random.Random(current_seed)
        
        daily_profits = []
        warmup_count = int(horizon_days * 0.25)
        
        for day in range(horizon_days):
            demand = max(0.0, rng.gauss(mu_d, sigma_d))
            sales = min(demand, q_optimal)
            leftover = q_optimal - sales
            
            revenue = sales * price
            cogs = q_optimal * cost
            salvage_val = leftover * salvage
            profit = revenue - cogs + salvage_val
            
            if day >= warmup_count:
                daily_profits.append(profit)
                
        if daily_profits:
            avg_p = sum(daily_profits) / len(daily_profits)
        else:
            avg_p = 0.0
            
        per_seed_exp_profit.append(avg_p)
        per_seed_q.append(q_optimal)
        seed_list.append(current_seed)
        exp_profit_total += avg_p
        
    final_exp_profit = exp_profit_total / args.seeds if args.seeds > 0 else 0.0
    
    result = {
        "exp_profit": round(final_exp_profit, 4),
        "q": q_optimal,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": args.seeds,
        "time_unit": "day",
        "per_seed_exp_profit": [round(p, 4) for p in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

def _norm_ppf(p):
    if p <= 0: return -float('inf')
    if p >= 1: return float('inf')
    if p < 0.5:
        return -_norm_ppf(1-p)
    t = math.sqrt(-2 * math.log(1-p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)

if __name__ == "__main__":
    main()
