import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 4.0
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    if args.pert == "lam_up":
        mu_d *= 1.2
    elif args.pert == "mu_up":
        sigma_d *= 1.2
    elif args.pert == "c_up":
        cost *= 1.2
        cu = price - cost
        co = cost - salvage
        critical_ratio = cu / (cu + co)

    q_opt = mu_d + sigma_d * _norm_ppf(critical_ratio)
    q_opt = max(0, round(q_opt))

    horizon_days = int(args.horizon)
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]

    per_seed_exp_profit = []
    per_seed_q = []

    for s in seed_list:
        rng = random.Random(s)
        total_profit = 0.0
        warmup_days = int(horizon_days * 0.25)
        counted_days = 0
        for d in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = q_opt - sold
            profit = price * sold + salvage * leftover - cost * q_opt
            if d >= warmup_days:
                total_profit += profit
                counted_days += 1
        exp_p = total_profit / counted_days if counted_days > 0 else 0.0
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(float(q_opt))

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

def _norm_ppf(p):
    # Rational approximation for inverse normal CDF (Abramowitz & Stegun 26.2.22)
    if p <= 0 or p >= 1:
        return 0.0
    if p < 0.5:
        return -_norm_ppf_upper(1 - p)
    else:
        return _norm_ppf_upper(p)

def _norm_ppf_upper(p):
    t = math.sqrt(-2 * math.log(1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)

if __name__ == "__main__":
    main()
