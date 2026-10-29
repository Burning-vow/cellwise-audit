import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 15.0
    p, c, s = 30.0, 12.0, 7.0
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

    def norm_ppf(q):
        return math.sqrt(2) * erfinv(2*q - 1)

    def erfinv(x):
        a = 0.147
        ln_term = math.log(1 - x*x)
        t1 = 2/(math.pi*a) + ln_term/2
        return math.copysign(math.sqrt(max(0.0, math.sqrt(t1*t1 - ln_term/a) - t1)), x)

    z_star = norm_ppf(crit_ratio)
    q_opt = max(0, int(round(mu_d + z_star * sigma_d)))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    seeds_used = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        warmup_days = int(args.horizon * 0.25)
        total_profit = 0.0
        count = 0
        for day in range(int(args.horizon)):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0.0, demand)
            sold = min(demand, q_opt)
            leftover = max(0.0, q_opt - demand)
            profit = p * sold + s * leftover - c * q_opt
            if day >= warmup_days:
                total_profit += profit
                count += 1
        exp_profit = total_profit / count if count > 0 else 0.0
        per_seed_exp_profit.append(exp_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)
        seeds_used += 1

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": q_opt,
        "runtime_units": int(args.horizon),
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(v, 4) for v in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
