import argparse, json, math, random
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    args = p.parse_args()
    mu_d, sigma_d = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 7.0
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    q_opt = int(round(mu_d + sigma_d * math.sqrt(2) * erfinv(2 * crit_ratio - 1))) if hasattr(math, 'erfinv') else int(round(mu_d + sigma_d * 0.674))
    if not hasattr(math, 'erfinv'):
        z = 0.674
        for _ in range(10):
            z = z - (0.5 * (1 + math.erf(z / math.sqrt(2))) - crit_ratio) / (math.exp(-z*z/2)/math.sqrt(2*math.pi))
        q_opt = int(round(mu_d + sigma_d * z))
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    per_seed_exp_profit = []
    per_seed_q = []
    horizon_days = int(args.horizon)
    if horizon_days <= 0: horizon_days = 1
    warmup_days = int(horizon_days * 0.25)
    if warmup_days < 0: warmup_days = 0
    total_profit_window = 0.0
    days_in_window = max(1, horizon_days - warmup_days)
    rng = random.Random(args.seed_start)
    for s_idx in range(seeds_used):
        current_seed = seed_list[s_idx]
        rng = random.Random(current_seed)
        day_profits = []
        for d in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            day_profits.append(profit)
        window_profits = day_profits[warmup_days:]
        avg_p = sum(window_profits) / len(window_profits) if window_profits else 0.0
        per_seed_exp_profit.append(avg_p)
        per_seed_q.append(q_opt)
        total_profit_window += sum(window_profits)
    exp_profit = total_profit_window / (seeds_used * days_in_window) if seeds_used > 0 else 0.0
    out = {
        "exp_profit": round(exp_profit, 4),
        "q": q_opt,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))
if __name__ == "__main__":
    main()
