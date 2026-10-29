import json, random, math, argparse

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_ppf(p):
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 7.0
    if args.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif args.pert == "mu_up":
        sd_d = sd_d * 1.2
    elif args.pert == "c_up":
        cost = cost * 1.2

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_opt = mu_d + sd_d * norm_ppf(crit)

    horizon = float(args.horizon)
    n_seeds = args.seeds
    seed_list = [args.seed_start + i for i in range(n_seeds)]
    per_seed_profit = []
    per_seed_q = []

    for s in seed_list:
        rng = random.Random(s)
        warm = 0.25 * horizon
        t = 0.0
        total_profit = 0.0
        total_time = 0.0
        while t < horizon:
            demand = rng.gauss(mu_d, sd_d)
            sold = min(q_opt, demand)
            leftover = max(0.0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            if t >= warm:
                total_profit += profit
                total_time += 1.0
            t += 1.0
        if total_time > 0:
            per_seed_profit.append(total_profit / total_time)
        else:
            per_seed_profit.append(0.0)
        per_seed_q.append(q_opt)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
