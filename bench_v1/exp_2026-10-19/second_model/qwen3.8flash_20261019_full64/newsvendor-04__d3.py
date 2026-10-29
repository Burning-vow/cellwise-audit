import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    price = 30.0
    cost = 12.0
    salvage = 4.0

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        if p <= 0: return float('-inf')
        if p >= 1: return float('inf')
        # Approximation for inverse normal CDF using rational approximation
        # Abramowitz and Stegun formula 26.2.23
        t = math.sqrt(-2 * math.log(1 - p)) if p < 0.5 else math.sqrt(-2 * math.log(p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
        if p < 0.5:
            return -z
        else:
            return z

    q_opt = mu_d + sigma_d * norm_ppf(critical_ratio)
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seeds_used = 0
    seed_list = []

    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1

    warmup_fraction = 0.25
    warmup_days = int(horizon_days * warmup_fraction)
    effective_days = horizon_days - warmup_days
    if effective_days <= 0:
        effective_days = 1

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        profits = []
        
        for day in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            
            ordered = q_opt
            sold = min(demand, ordered)
            leftover = ordered - sold
            
            revenue = sold * price
            cost_total = ordered * cost
            salvage_val = leftover * salvage
            
            profit = revenue - cost_total + salvage_val
            profits.append(profit)
        
        avg_profit = sum(profits[warmup_days:]) / effective_days
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seeds_used += 1
        seed_list.append(seed)

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": overall_exp_profit,
        "q": q_opt,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
