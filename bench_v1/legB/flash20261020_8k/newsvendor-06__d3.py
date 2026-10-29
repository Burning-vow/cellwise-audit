import argparse, json, math, random, time

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
    ap.add_argument("--horizon", type=float, default=365.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif a.pert == "mu_up":
        price = price * 1.1
    elif a.pert == "c_up":
        cost = cost * 1.15
    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q = mu_d + sd_d * norm_ppf(crit)
    q = max(0.0, q)
    horizon = float(a.horizon)
    nseeds = max(1, int(a.seeds))
    seed_list = [a.seed_start + i for i in range(nseeds)]
    per_profit = []
    per_q = []
    warm = 0.25
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        total_profit = 0.0
        total_days = 0.0
        while t < horizon:
            dt = 1.0
            if t + dt > horizon:
                dt = horizon - t
            if dt <= 0:
                break
            demand = rng.gauss(mu_d, sd_d)
            sold = min(q, demand)
            leftover = max(0.0, q - demand)
            profit = price * sold + salvage * leftover - cost * q
            if t >= warm * horizon:
                total_profit += profit * dt
                total_days += dt
            t += dt
        if total_days > 0:
            per_profit.append(total_profit / total_days)
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
