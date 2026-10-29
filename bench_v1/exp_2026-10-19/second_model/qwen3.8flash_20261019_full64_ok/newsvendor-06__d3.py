import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    price = 30.0
    cost = 12.0
    salvage = 7.0

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        pass
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
            return -(t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t**3))
        else:
            t = math.sqrt(-2 * math.log(1-p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            return t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t**3)

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + sigma_d * z_opt
    q_opt_int = int(round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    total_profit_sum = 0.0
    days_simulated_total = 0

    horizon_days = int(args.horizon)
    warmup_fraction = 0.25
    warmup_days = int(horizon_days * warmup_fraction)
    effective_days = horizon_days - warmup_days

    for i in range(args.seeds):
        seed_val = args.seed_start + i
        rng = random.Random(seed_val)
        daily_profits = []
        for d in range(horizon_days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            ordered = q_opt_int
            sold = min(demand, ordered)
            leftover = ordered - sold
            profit = price * sold + salvage * leftover - cost * ordered
            daily_profits.append(profit)
        
        if effective_days > 0:
            window_profits = daily_profits[warmup_days:]
            avg_profit = sum(window_profits) / len(window_profits)
        else:
            avg_profit = sum(daily_profits) / len(daily_profits) if daily_profits else 0.0
        
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt_int)
        seed_list.append(seed_val)
        total_profit_sum += avg_profit
        days_simulated_total += 1

    exp_profit = total_profit_sum / days_simulated_total if days_simulated_total > 0 else 0.0

    result = {
        "exp_profit": round(exp_profit, 4),
        "q": q_opt_int,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(p, 4) for p in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
