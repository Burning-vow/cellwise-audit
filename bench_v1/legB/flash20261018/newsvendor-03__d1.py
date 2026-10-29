import json, random, math, argparse, time

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
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu_d, sd_d = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if args.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif args.pert == "mu_up":
        price = price * 1.1
    elif args.pert == "c_up":
        cost = cost * 1.1

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
            dt = rng.expovariate(1.0 / 1.0)
            t += dt
            if t >= horizon:
                break
            demand = rng.gauss(mu_d, sd_d)
            q = q_opt
            sold = min(q, demand)
            leftover = q - sold
            profit = price * sold + salvage * leftover - cost * q
            if t >= warm:
                profit_sum += profit
                q_sum += q
                q_cnt += 1
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
