import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    price = 20.0
    cost = 12.0
    salvage = 7.0

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        # Approximation for inverse normal CDF using rational approximation
        # Abramowitz and Stegun formula 26.2.23
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432748, 0.189269, 0.001308
            return -(t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t))
        else:
            t = math.sqrt(-2 * math.log(1-p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432748, 0.189269, 0.001308
            return t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + z_opt * sigma_d
    q_opt = max(0, round(q_opt))

    days = int(args.horizon)
    if days <= 0:
        days = 1

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    total_profit_sum = 0.0
    total_days_count = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        daily_profits = []
        for _ in range(days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            daily_profits.append(profit)
        
        avg_profit = sum(daily_profits) / len(daily_profits) if daily_profits else 0.0
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)
        total_profit_sum += sum(daily_profits)
        total_days_count += len(daily_profits)

    exp_profit = total_profit_sum / total_days_count if total_days_count > 0 else 0.0
    
    result = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
