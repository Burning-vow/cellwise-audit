import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 15.0
    p, c, s = 30.0, 12.0, 4.0
    cu = p - c
    co = c - s
    crit_ratio = cu / (cu + co)

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        sigma_d *= 1.1
    elif args.pert == "c_up":
        c *= 1.1
        cu = p - c
        co = c - s
        crit_ratio = cu / (cu + co)

    def norm_inv(p):
        a = [-3.969683028665376e+01, 2.209460928105471e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01]
        c_ = [7.784695709041462e-03, -3.223964580411365e-01, -2.400758277161838e+00,
              -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290748e-01, 2.400758277161838e+00,
             2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        plow = 0.02425
        phigh = 1 - plow
        if p < plow:
            q = math.sqrt(-2 * math.log(p))
            return (((((c_[0]*q+c_[1])*q+c_[2])*q+c_[3])*q+c_[4])*q+c_[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+d[4])*q+1)
        elif p <= phigh:
            q = p - 0.5
            r = q*q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1-p))
            return -(((((c_[0]*q+c_[1])*q+c_[2])*q+c_[3])*q+c_[4])*q+c_[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+d[4])*q+1)

    z_star = norm_inv(crit_ratio)
    q_opt = mu_d + z_star * sigma_d
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    total_profit_sum = 0.0
    total_days = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        warmup_frac = 0.25
        horizon_days = int(args.horizon)
        warmup_days = int(horizon_days * warmup_frac)
        profit_sum = 0.0
        days_counted = 0
        for day in range(horizon_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            daily_profit = p * sold + s * leftover - c * q_opt
            if day >= warmup_days:
                profit_sum += daily_profit
                days_counted += 1
        avg_profit = profit_sum / days_counted if days_counted > 0 else 0.0
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)
        total_profit_sum += profit_sum
        total_days += days_counted

    exp_profit = total_profit_sum / total_days if total_days > 0 else 0.0

    result = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
