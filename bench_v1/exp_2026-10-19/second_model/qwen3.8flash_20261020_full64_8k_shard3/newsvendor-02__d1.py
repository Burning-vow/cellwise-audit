import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 25.0
    price, cost, salvage = 20.0, 12.0, 7.0
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

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
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        # Rational approximation for inverse normal CDF
        a = [-3.96918e+01, 2.20946e+02, -2.75929e+02, 1.38358e+02, -3.06648e+01, 2.50663e-01]
        b = [-5.44760e+01, 1.61585e+02, -1.55698e+02, 6.68013e+01, -1.32806e+01]
        c = [-7.78489e-03, -3.22396e-01, -2.40075e+00, -2.54973e+00, 4.37466e+00, 2.93816e+00]
        d = [7.78469e-03, 3.22467e-01, 2.44513e+00, 3.75440e+00]
        plow = 0.02425
        phigh = 1 - plow
        if p < plow:
            q = math.sqrt(-2 * math.log(p))
            x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p > phigh:
            q = math.sqrt(-2 * math.log(1-p))
            x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        else:
            q = p - 0.5
            r = q*q
            x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        return x

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + sigma_d * z_opt
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
        seed = args.seed_start + i
        rng = random.Random(seed)
        seed_list.append(seed)
        
        daily_profits = []
        for _ in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            daily_profits.append(profit)
        
        exp_profit_seed = sum(daily_profits) / len(daily_profits)
        per_seed_exp_profit.append(exp_profit_seed)
        per_seed_q.append(q_opt)
        total_profit_sum += exp_profit_seed
        days_simulated_total += horizon_days

    overall_exp_profit = total_profit_sum / args.seeds if args.seeds > 0 else 0.0
    
    result = {
        "exp_profit": overall_exp_profit,
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
