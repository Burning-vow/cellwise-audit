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
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--horizon", type=float, default=365.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu_d, sd_d = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif a.pert == "mu_up":
        sd_d = sd_d * 1.2
    elif a.pert == "c_up":
        cost = cost * 1.2

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_star = mu_d + sd_d * norm_ppf(crit)

    def day_profit(q, d):
        sold = min(q, d)
        return price * sold + salvage * (q - sold) - cost * q

    n = max(1, a.seeds)
    H = a.horizon
    warm = 0.25
    per_profit = []
    per_q = []
    seeds = []
    for i in range(n):
        s = a.seed_start + i
        seeds.append(s)
        rng = random.Random(s)
        total = 0.0
        cnt = 0
        t = 0.0
        while t < H:
            d = rng.gauss(mu_d, sd_d)
            if d < 0:
                d = 0.0
            if t >= warm * H:
                total += day_profit(q_star, d)
                cnt += 1
            t += 1.0
        per_profit.append(total / cnt if cnt > 0 else 0.0)
        per_q.append(q_star)

    exp_profit = sum(per_profit) / len(per_profit) if per_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q_star,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
