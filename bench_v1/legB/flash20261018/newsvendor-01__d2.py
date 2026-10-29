import json, random, math, argparse

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_ppf(p):
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--horizon", type=float, default=365.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu_d, sd_d = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if args.pert == "lam_up":
        mu_d = 60.0 * 1.1
    elif args.pert == "mu_up":
        sd_d = 15.0 * 1.1
    elif args.pert == "c_up":
        cost = 12.0 * 1.1

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_star = mu_d + sd_d * norm_ppf(crit)

    n_seeds = args.seeds
    horizon = float(args.horizon)
    seed_list = [args.seed_start + i for i in range(n_seeds)]
    per_seed_profit = []
    per_seed_q = []

    for s in seed_list:
        rng = random.Random(s)
        warm = int(horizon * 0.25)
        total_profit = 0.0
        count = 0
        for day in range(int(horizon)):
            demand = rng.gauss(mu_d, sd_d)
            sold = min(q_star, demand)
            leftover = max(0.0, q_star - demand)
            profit = price * sold + salvage * leftover - cost * q_star
            if day >= warm:
                total_profit += profit
                count += 1
        avg = total_profit / count if count > 0 else 0.0
        per_seed_profit.append(avg)
        per_seed_q.append(q_star)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q_star,
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
