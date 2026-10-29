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

    mu, sd = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 7.0
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
    q = max(0.0, q)

    horizon = float(a.horizon)
    nseeds = int(a.seeds)
    seed_list = [a.seed_start + i for i in range(nseeds)]
    warm = 0.25 * horizon

    per_seed_profit = []
    per_seed_q = []
    for s in seed_list:
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
            d = max(0.0, d)
            sold = min(q, d)
            leftover = q - sold
            profit = price * sold + salvage * leftover - cost * q
            if t > warm:
                acc += profit
                cnt += 1
        per_seed_profit.append(acc / cnt if cnt > 0 else 0.0)
        per_seed_q.append(q)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q,
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
