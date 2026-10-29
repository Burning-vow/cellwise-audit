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
        leftover = q - sold
        return price * sold + salvage * leftover - cost * q

    def analytic_profit(q):
        # E[profit] via numeric integration over demand
        n = 4000
        lo = mu_d - 6.0 * sd_d
        hi = mu_d + 6.0 * sd_d
        step = (hi - lo) / n
        tot = 0.0
        for i in range(n):
            d = lo + (i + 0.5) * step
            pdf = math.exp(-0.5 * ((d - mu_d) / sd_d) ** 2) / (sd_d * math.sqrt(2 * math.pi))
            tot += day_profit(q, d) * pdf * step
        return tot

    horizon_days = max(1, int(round(a.horizon)))
    warm = int(horizon_days * 0.25)
    per_seed_profit = []
    per_seed_q = []
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        acc = 0.0
        cnt = 0
        for day in range(horizon_days):
            d = rng.gauss(mu_d, sd_d)
            p = day_profit(q_star, d)
            if day >= warm:
                acc += p
                cnt += 1
        est = acc / cnt if cnt > 0 else 0.0
        per_seed_profit.append(est)
        per_seed_q.append(q_star)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else analytic_profit(q_star)

    out = {
        "exp_profit": exp_profit,
        "q": q_star,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
