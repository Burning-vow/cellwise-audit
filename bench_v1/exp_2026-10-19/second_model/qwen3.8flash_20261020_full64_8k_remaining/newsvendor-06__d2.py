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
    p = 30.0
    c = 12.0
    s = 7.0

    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        pass
    elif args.pert == 'c_up':
        c *= 1.1

    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)

    def norm_ppf(p_val):
        if p_val <= 0: return -math.inf
        if p_val >= 1: return math.inf
        # Approximation for inverse normal CDF using rational approximation
        # Abramowitz and Stegun formula 26.2.23
        if p_val < 0.5:
            t = math.sqrt(-2 * math.log(p_val))
            x = -(t - (2.30753 + 0.278982*t)/(1+0.99229*t+0.04481*t*t))
        else:
            t = math.sqrt(-2 * math.log(1-p_val))
            x = t - (2.30753 + 0.278982*t)/(1+0.99229*t+0.04481*t*t)
        return x

    q_opt = mu_d + sigma_d * norm_ppf(critical_ratio)
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1
        
    total_profit_sum = 0.0
    count = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        daily_profits = []
        
        warmup_days = int(horizon_days * 0.25)
        
        for d in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            revenue = sold * p
            cost = q_opt * c
            salvage = leftover * s
            
            profit = revenue - cost + salvage
            daily_profits.append(profit)
            
        valid_profits = daily_profits[warmup_days:]
        if len(valid_profits) > 0:
            avg_profit = sum(valid_profits) / len(valid_profits)
        else:
            avg_profit = sum(daily_profits) / len(daily_profits) if daily_profits else 0.0
            
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)
        total_profit_sum += avg_profit
        count += 1
        
    exp_profit = total_profit_sum / count if count > 0 else 0.0
    
    result = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": count,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
