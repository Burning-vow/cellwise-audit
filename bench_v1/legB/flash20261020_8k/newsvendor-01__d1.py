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
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu = mu * 1.1
    elif a.pert == "mu_up":
        sd = sd * 1.1
    elif a.pert == "c_up":
        cost = cost * 1.1

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q = mu + sd * norm_ppf(crit)
    q = max(0.0, q)

    horizon = float(a.horizon)
    nseeds = max(1, int(a.seeds))
    seed_list = [a.seed_start + i for i in range(nseeds)]
    warm = 0.25 * horizon

    per_profit = []
    per_q = []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        profit_sum = 0.0
        q_sum = 0.0
        q_cnt = 0
        while t < horizon:
            demand = rng.gauss(mu, sd)
            sold = min(q, demand)
            leftover = max(0.0, q - demand)
            day_profit = price * sold + salvage * leftover - cost * q
            if t >= warm:
                profit_sum += day_profit
                q_sum += q
                q_cnt += 1
            t += 1.0
        if q_cnt > 0:
            per_profit.append(profit_sum / q_cnt)
            per_q.append(q_sum / q_cnt)
        else:
            per_profit.append(0.0)
            per_q.append(q)

    exp_profit = sum(per_profit) / len(per_profit) if per_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
