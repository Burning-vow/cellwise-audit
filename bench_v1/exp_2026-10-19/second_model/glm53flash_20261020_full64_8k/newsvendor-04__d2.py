import argparse, json, math, random, time

def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", default="1000")
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if a.pert == "lam_up":
        mu *= 1.2
    elif a.pert == "mu_up":
        mu *= 1.2
    elif a.pert == "c_up":
        cost *= 1.2

    horizon = float(a.horizon)
    days = int(horizon)
    warm = int(days * 0.25)

    t0 = time.perf_counter()
    per_seed_exp = []
    per_seed_q = []
    seed_list = []

    q_grid = list(range(20, 141))

    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        demands = []
        for d in range(days):
            x = rng.gauss(mu, sd)
            if x < 0.0:
                x = 0.0
            demands.append(x)

        eval_days = demands[warm:] if warm < days else demands[-1:]
        n_eval = len(eval_days)

        best_q, best_p = q_grid[0], -1e18
        for q in q_grid:
            tot = 0.0
            for d in eval_days:
                sold = d if d < q else q
                tot += price * sold - cost * q + salvage * (q - sold)
            avg = tot / n_eval
            if avg > best_p:
                best_p, best_q = avg, q

        per_seed_q.append(float(best_q))
        per_seed_exp.append(best_p)

    runtime = time.perf_counter() - t0

    exp_profit = sum(per_seed_exp) / len(per_seed_exp) if per_seed_exp else 0.0
    q_mean = sum(per_seed_q) / len(per_seed_q) if per_seed_q else 0.0

    cr = (price - cost) / (price - salvage)
    z = 0.0
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if normal_cdf(mid) < cr:
            lo = mid
        else:
            hi = mid
    z = 0.5 * (lo + hi)
    q_theory = mu + sd * z

    out = {
        "exp_profit": exp_profit,
        "q": q_mean,
        "runtime_units": "days",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp,
        "per_seed_q": per_seed_q,
        "q_critical_ratio": q_theory,
        "horizon_days": horizon,
        "pert": a.pert,
        "runtime_seconds": runtime,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
