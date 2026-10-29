import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_demand = 60.0
    sigma_demand = 25.0
    price = 30.0
    cost = 12.0
    salvage = 4.0

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        if p <= 0: return -float('inf')
        if p >= 1: return float('inf')
        # Approximation for inverse normal CDF using rational approximation
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
            return -z
        else:
            t = math.sqrt(-2 * math.log(1 - p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
            return z

    q_opt = mu_demand + sigma_demand * norm_ppf(critical_ratio)
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []

    horizon_days = int(args.horizon)
    warmup_days = int(horizon_days * 0.25)

    for i in range(args.seeds):
        seed_val = args.seed_start + i
        rng = random.Random(seed_val)
        profits = []
        for day in range(horizon_days):
            demand = rng.gauss(mu_demand, sigma_demand)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            if day >= warmup_days:
                profits.append(profit)
        exp_p = sum(profits) / len(profits) if profits else 0.0
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        seed_list.append(seed_val)

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": overall_exp_profit,
        "q": q_opt,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
