import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=4000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 25.0
    p, c, s = 30.0, 12.0, 4.0
    if a.pert == "lam_up": mu *= 1.2
    elif a.pert == "mu_up": mu *= 1.2
    elif a.pert == "c_up": c *= 1.1

    n = int(a.horizon)
    warm = int(n * 0.25)
    grid = list(range(40, 121))

    per_q, per_prof, seed_list = [], [], []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        demands = []
        for _ in range(n):
            d = rng.gauss(mu, sd)
            demands.append(d if d > 0 else 0.0)
        best_q, best_v = None, -1e18
        for q in grid:
            tot = 0.0
            for d in demands[warm:]:
                sold = d if d < q else q
                over = q - sold
                tot += p * sold + s * over - c * q
            v = tot / (n - warm)
            if v > best_v:
                best_v, best_q = v, q
        per_q.append(best_q)
        per_prof.append(best_v)
        seed_list.append(seed)

    q_star = per_q[int(len(per_q) / 2)]
    z = 0.5 * math.sqrt(2.0) * 1.0
    lo, hi = -8.0, 8.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        e = 0.5 * (1.0 + math.erf(mid / math.sqrt(2.0)))
        if e < (p - c) / (p - s): lo = mid
        else: hi = mid
    q_theory = mu + sd * 0.5 * (lo + hi)

    out = {
        "exp_profit": sum(per_prof) / len(per_prof),
        "q": sum(per_q) / len(per_q),
        "q_critical_fractile": q_theory,
        "runtime_units": n,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_exp_profit": per_prof,
        "per_seed_q": per_q,
        "pert": a.pert,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
