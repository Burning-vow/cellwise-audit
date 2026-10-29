import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    price = 30.0
    cost = 12.0
    salvage = 4.0

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        sigma_d *= 1.1
    elif args.pert == "c_up":
        cost *= 1.1

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        # Approximation for inverse normal CDF using rational approximation
        if p <= 0: return -1e9
        if p >= 1: return 1e9
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

    z_star = norm_ppf(critical_ratio)
    q_opt = mu_d + z_star * sigma_d
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    total_profit_sum = 0.0
    days_simulated_total = 0

    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1

    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        daily_profits = []
        warmup_count = int(horizon_days * 0.25)
        
        for day in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            profit = price * sold + salvage * leftover - cost * q_opt
            daily_profits.append(profit)
        
        if len(daily_profits) > warmup_count:
            valid_profits = daily_profits[warmup_count:]
        else:
            valid_profits = daily_profits
            
        avg_profit = sum(valid_profits) / len(valid_profits) if valid_profits else 0.0
        
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(s)
        
        total_profit_sum += avg_profit
        days_simulated_total += len(valid_profits)

    exp_profit = total_profit_sum / args.seeds if args.seeds > 0 else 0.0
    
    result = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": days_simulated_total,
        "seed_list": seed_list,
        "seeds_used": args.seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
