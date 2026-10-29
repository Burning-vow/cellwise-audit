import json, random, math, argparse

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--horizon", type=float, default=365.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if args.pert == "lam_up":
        mu_d = 60.0 * 1.2
    elif args.pert == "mu_up":
        sd_d = 25.0 * 1.2
    elif args.pert == "c_up":
        cost = 12.0 * 1.2

    cu = price - cost
    co = cost - salvage
    z = (cu) / (cu + co)
    # invert normal cdf via bisection
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < z:
            lo = mid
        else:
            hi = mid
    zstar = 0.5 * (lo + hi)
    q_opt = mu_d + zstar * sd_d

    horizon = float(args.horizon)
    nseeds = args.seeds
    seed_list = [args.seed_start + i for i in range(nseeds)]
    warm = 0.25 * horizon

    per_seed_profit = []
    per_seed_q = []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        profit_sum = 0.0
        q_sum = 0.0
        q_cnt = 0
        while t < horizon:
            # daily order at start of day
            q = q_opt
            # demand drawn for the day
            d = rng.gauss(mu_d, sd_d)
            if d < 0:
                d = 0.0
            sold = min(q, d)
            leftover = q - sold
            day_profit = price * sold + salvage * leftover - cost * q
            if t >= warm:
                profit_sum += day_profit
                q_sum += q
                q_cnt += 1
            t += 1.0
        if q_cnt > 0:
            per_seed_profit.append(profit_sum / q_cnt)
            per_seed_q.append(q_sum / q_cnt)
        else:
            per_seed_profit.append(0.0)
            per_seed_q.append(0.0)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    q_report = sum(per_seed_q) / len(per_seed_q) if per_seed_q else q_opt

    out = {
        "exp_profit": exp_profit,
        "q": q_report,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
