import json, math, random, argparse

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
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if a.pert == "lam_up":
        mu = mu * 1.2
    elif a.pert == "mu_up":
        sd = sd * 1.2
    elif a.pert == "c_up":
        cost = cost * 1.2

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q = mu + sd * norm_ppf(crit)

    n = max(1, a.seeds)
    horizon = a.horizon
    warm = 0.25 * horizon
    per_profit = []
    per_q = []
    seeds = []
    for i in range(n):
        s = a.seed_start + i
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        acc = 0.0
        cnt = 0
        while t < horizon:
            dt = rng.expovariate(1.0)
            t += dt
            if t >= horizon:
                break
            d = rng.gauss(mu, sd)
            sold = min(q, d)
            leftover = max(0.0, q - d)
            profit = price * sold + salvage * leftover - cost * q
            if t > warm:
                acc += profit
                cnt += 1
        per_profit.append(acc / cnt if cnt > 0 else 0.0)
        per_q.append(q)

    exp_profit = sum(per_profit) / len(per_profit) if per_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q,
        "runtime_units": horizon,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
