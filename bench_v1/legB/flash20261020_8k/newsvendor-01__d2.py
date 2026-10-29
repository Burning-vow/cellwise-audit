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
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    mu_d, sd_d = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu_d = 66.0
    elif a.pert == "mu_up":
        price = 22.0
    elif a.pert == "c_up":
        cost = 13.2
    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_opt = mu_d + sd_d * norm_ppf(crit)
    q_int = int(round(q_opt))
    horizon = float(a.horizon)
    nseeds = max(1, int(a.seeds))
    seed_list = [a.seed_start + i for i in range(nseeds)]
    per_profit = []
    per_q = []
    t0 = time.time()
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        warm = 0.25 * horizon
        total_profit = 0.0
        days = 0
        while t < horizon:
            demand = rng.gauss(mu_d, sd_d)
            sold = min(q_int, demand)
            leftover = q_int - sold
            profit = price * sold + salvage * leftover - cost * q_int
            if t >= warm:
                total_profit += profit
                days += 1
            t += 1.0
        est = total_profit / days if days > 0 else 0.0
        per_profit.append(est)
        per_q.append(q_int)
    exp_profit = sum(per_profit) / len(per_profit) if per_profit else 0.0
    runtime_units = time.time() - t0
    out = {
        "exp_profit": exp_profit,
        "q": q_int,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "second",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
