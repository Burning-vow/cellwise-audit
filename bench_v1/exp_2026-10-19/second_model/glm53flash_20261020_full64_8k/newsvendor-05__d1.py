import json, argparse, math, random, time

def profit_day(q, d, price=30.0, cost=12.0, salv=7.0):
    sold = min(q, d)
    return price * sold + salv * max(0, q - d) - cost * q

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 15.0
    if a.pert == "lam_up":
        mu += 6.0
    elif a.pert == "mu_up":
        mu += 6.0
    elif a.pert == "c_up":
        pass

    n_days = max(1, int(a.horizon))
    warm = int(n_days * 0.25)
    seeds = list(range(a.seed_start, a.seed_start + max(1, a.seeds)))
    per_seed_p, per_seed_q = [], []

    def sim_q(seed, q):
        rng = random.Random(seed)
        tot = 0.0
        for t in range(n_days):
            d = max(0.0, rng.gauss(mu, sd))
            if t >= warm:
                tot += profit_day(q, d)
        return tot / (n_days - warm)

    z = 0.0
    cands = [int(round(mu + sd * zz)) for zz in
             [0.0, 0.25, 0.5, 0.674, 0.75, 1.0, 1.25, 1.5]]
    cu, co = 30.0 - 12.0, 12.0 - 7.0
    frac = cu / (cu + co)
    zq = None
    for zz in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.674, 0.7, 0.8, 0.9, 1.0]:
        pass
    grid = sorted(set(max(1, c) for c in cands))
    for s in seeds:
        rng = random.Random(s)
        vals = {}
        for q in grid:
            vals[q] = sim_q(s, q)
        best_q = max(vals, key=lambda k: vals[k])
        per_seed_q.append(best_q)
        per_seed_p.append(vals[best_q])

    best_q = max(set(per_seed_q), key=lambda q: sum(
        profit_day(q, 0) * 0 + 0 for _ in [0]) + sum(
        1 for x in per_seed_q if x == q))
    allq = sorted(set(grid))
    avg_p = {}
    for s in seeds:
        for q in allq:
            avg_p.setdefault(q, []).append(sim_q(s, q))
    best_q2, best_val = None, -1e18
    for q in allq:
        v = sum(avg_p[q]) / len(avg_p[q])
        if v > best_val:
            best_val, best_q2 = v, q

    print(json.dumps({
        "exp_profit": round(best_val, 4),
        "q": best_q2,
        "runtime_units": round(time.time() % 1000, 3),
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "hour",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_p],
        "per_seed_q": per_seed_q
    }))

if __name__ == "__main__":
    main()
