import json, random, argparse, math

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

    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if a.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif a.pert == "mu_up":
        cost = cost * 1.1
    elif a.pert == "c_up":
        salvage = salvage * 0.5

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_star = mu_d + sd_d * norm_ppf(crit)

    n = max(1, a.seeds)
    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(n)]
    per_profit = []
    per_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        acc = 0.0
        cnt = 0
        while t < H:
            d = rng.gauss(mu_d, sd_d)
            if d < 0:
                d = 0.0
            sold = min(q_star, d)
            leftover = q_star - sold
            profit = price * sold + salvage * leftover - cost * q_star
            if t >= warm:
                acc += profit
                cnt += 1
            t += 1.0
        per_profit.append(acc / cnt if cnt > 0 else 0.0)
        per_q.append(q_star)

    exp_profit = sum(per_profit) / len(per_profit)
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
