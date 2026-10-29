import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", default="1000")
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    mu, sd = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if a.pert == "lam_up": mu *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": cost *= 1.05
    H = float(a.horizon)
    n_days = max(1, int(H))
    warm = int(n_days * 0.25)
    use_days = n_days - warm
    if use_days <= 0: use_days = 1; warm = 0
    cr = (price - cost) / (price - cost + cost - salvage)
    z = 0.0
    for _ in range(200):
        f = 0.5 * (1 + math.erf(z / math.sqrt(2))) - cr
        d = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
        z -= f / max(d, 1e-12)
        if abs(f) < 1e-12: break
    q_star = mu + sd * z
    grid = [i for i in range(1, 200)]
    if q_star not in grid: grid.append(int(round(q_star)))
    grid.sort()
    per_q, per_qs = [], []
    seed_list, per_seed_ep, per_seed_q = [], [], []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s * 7919 + 13)
        demands = []
        for d in range(n_days):
            demands.append(rng.gauss(mu, sd))
        demands = demands[warm:]
        seed_list.append(s)
        best_q, best_p = None, -1e18
        for q in grid:
            tot = 0.0
            for d in demands:
                sold = min(d, q)
                tot += price * sold - cost * q - salvage * max(q - d, 0.0)
            tot /= len(demands)
            if tot > best_p: best_p, best_q = tot, q
        per_seed_ep.append(best_p)
        per_seed_q.append(best_q)
        per_q.append((best_q, best_p))
    seeds_used = len(seed_list)
    exp_p = sum(per_seed_ep) / seeds_used if seeds_used else 0.0
    qs = [x[0] for x in per_q]
    best_q, best_p = max(per_q, key=lambda t: t[1]) if per_q else (int(round(q_star)), 0.0)
    print(json.dumps({
        "exp_profit": exp_p, "q": best_q,
        "runtime_units": n_days, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "day",
        "per_seed_exp_profit": per_seed_ep, "per_seed_q": per_seed_q
    }))

if __name__ == "__main__":
    main()
