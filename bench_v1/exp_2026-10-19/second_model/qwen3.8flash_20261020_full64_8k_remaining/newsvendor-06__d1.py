import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 25.0
    p, c, s = 30.0, 12.0, 7.0
    cu = p - c
    co = c - s
    crit_ratio = cu / (cu + co)

    if args.pert == "lam_up":
        mu_d *= 1.2
    elif args.pert == "mu_up":
        sigma_d *= 1.2
    elif args.pert == "c_up":
        c *= 1.2
        cu = p - c
        co = c - s
        crit_ratio = cu / (cu + co)

    z = _inv_std_normal(crit_ratio)
    q_opt = max(0, int(round(mu_d + z * sigma_d)))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    seeds_used = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        n_days = int(args.horizon)
        if n_days <= 0:
            n_days = 1
        warmup = int(n_days * 0.25)
        total_profit = 0.0
        count = 0
        for d in range(n_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0.0, demand)
            sold = min(q_opt, demand)
            leftover = max(0, q_opt - demand)
            profit = p * sold + s * leftover - c * q_opt
            if d >= warmup:
                total_profit += profit
                count += 1
        exp_p = total_profit / count if count > 0 else 0.0
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        seed_list.append(seed)
        seeds_used += 1

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": q_opt,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))


def _inv_std_normal(p):
    if p <= 0 or p >= 1:
        return 0.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479406966539e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615821328582478e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.400952008976518e+00,
         2.549732534343734e+00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


if __name__ == "__main__":
    main()
