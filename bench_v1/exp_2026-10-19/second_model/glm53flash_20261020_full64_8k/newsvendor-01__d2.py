import json, argparse, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2400.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        cost *= 1.1

    cu = price - cost
    co = cost - salvage
    z = None
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < cu / (cu + co):
            lo = mid
        else:
            hi = mid
    z = (lo + hi) / 2
    q_star = mu + sd * z

    t0 = time.time()
    per_q, per_p = [], []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        days = max(1, int(round(a.horizon / 24.0)))
        warm = int(days * 0.25)
        tot_profit = 0.0
        tot_days = 0
        for d in range(days):
            demand = rng.gauss(mu, sd)
            if demand < 0:
                demand = 0.0
            sold = min(q_star, demand)
            profit = sold * price - q_star * cost + (q_star - sold) * salvage
            if d >= warm:
                tot_profit += profit
                tot_days += 1
        per_p.append(tot_profit / tot_days)
        per_q.append(q_star)
    exp_profit = sum(per_p) / len(per_p)
    runtime_units = time.time() - t0

    out = {
        "exp_profit": exp_profit,
        "q": q_star,
        "runtime_units": runtime_units,
        "seed_list": [a.seed_start + k for k in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "hour",
        "per_seed_exp_profit": per_p,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
