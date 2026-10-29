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

    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        sigma_d *= 1.1
    elif args.pert == 'c_up':
        cost *= 1.1

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        # Approximation for inverse normal CDF using rational approximation
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
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

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + sigma_d * z_opt
    q_opt = max(0, q_opt)

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    seeds_used = 0

    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1

    warmup_days = int(horizon_days * 0.25)
    if warmup_days >= horizon_days:
        warmup_days = max(0, horizon_days - 1)

    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        
        profits = []
        for _ in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(q_opt, demand)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            profits.append(profit)
        
        valid_profits = profits[warmup_days:]
        if not valid_profits:
            exp_p = sum(profits)/len(profits) if profits else 0.0
        else:
            exp_p = sum(valid_profits)/len(valid_profits)
        
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        seeds_used += 1

    total_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": round(total_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
