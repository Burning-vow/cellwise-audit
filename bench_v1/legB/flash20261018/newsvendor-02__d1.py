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
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif a.pert == "mu_up":
        price = price * 1.1
    elif a.pert == "c_up":
        cost = cost * 1.1

    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q_star = mu_d + sd_d * norm_ppf(crit)
    q_star = max(0.0, q_star)

    horizon = float(a.horizon)
    n_days = int(horizon)
    if n_days < 1:
        n_days = 1
    warm = int(n_days * 0.25)

    per_seed_profit = []
    per_seed_q = []
    seed_list = []
    seeds_used = 0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        seeds_used += 1
        total_profit = 0.0
        cnt = 0
        for day in range(n_days):
            demand = rng.gauss(mu_d, sd_d)
            if demand < 0.0:
                demand = 0.0
            sold = min(q_star, demand)
            leftover = q_star - sold
            profit = price * sold + salvage * leftover - cost * q_star
            if day >= warm:
                total_profit += profit
                cnt += 1
        if cnt == 0:
            cnt = 1
        per_seed_profit.append(total_profit / cnt)
        per_seed_q.append(q_star)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0

    out = {
        "exp_profit": exp_profit,
        "q": q_star,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
