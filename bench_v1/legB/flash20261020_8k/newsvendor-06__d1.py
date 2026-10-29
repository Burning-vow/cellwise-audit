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
    n_seeds = int(args.seeds)
    seed_list = [args.seed_start + i for i in range(n_seeds)]
    per_seed_profit = []
    per_seed_q = []
    warm = 0.25 * horizon

    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        profit_sum = 0.0
        q_sum = 0.0
        q_cnt = 0
        while t < horizon:
            # daily order cycle: one day = 1 time unit
            day_len = 1.0
            # demand for the day drawn at day start
            d = rng.gauss(mu_d, sd_d)
            if d < 0:
                d = 0.0
            sold = min(q_opt, d)
            leftover = q_opt - sold
            day_profit = price * sold + salvage * leftover - cost * q_opt
            # integrate only after warmup window
            if t >= warm:
                profit_sum += day_profit
                q_sum += q_opt
                q_cnt += 1
            t += day_len
        if q_cnt > 0:
            per_seed_profit.append(profit_sum / q_cnt)
            per_seed_q.append(q_sum / q_cnt)
        else:
            per_seed_profit.append(0.0)
            per_seed_q.append(q_opt)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    q_est = sum(per_seed_q) / len(per_seed_q) if per_seed_q else q_opt

    out = {
        "exp_profit": exp_profit,
        "q": q_est,
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
