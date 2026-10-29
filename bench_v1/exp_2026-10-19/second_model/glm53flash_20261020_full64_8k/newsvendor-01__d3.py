import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=10000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    mu, sd, price, cost, salvage = 60.0, 15.0, 20.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu += 6.0
    elif a.pert == "mu_up":
        mu += 6.0
    elif a.pert == "c_up":
        cost += 1.0

    def inv_phi(x):
        lo, hi = -8.0, 8.0
        for _ in range(200):
            m = 0.5 * (lo + hi)
            if 0.5 * (1.0 + math.erf(m / math.sqrt(2.0))) < x:
                lo = m
            else:
                hi = m
        return 0.5 * (lo + hi)

    t0 = time.time()
    per_seed_exp_profit = []
    per_seed_q = []
    n_days = int(max(1, a.horizon))
    grid = list(range(1, 200))
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        demands = []
        for _ in range(n_days):
            u1 = rng.random()
            while u1 <= 0.0:
                u1 = rng.random()
            u2 = rng.random()
            z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            d = mu + sd * z
            if d < 0.0:
                d = 0.0
            demands.append(d)
        best_q, best_profit = 0, -1e18
        for q in grid:
            tot = 0.0
            for d in demands:
                sold = d if d < q else q
                left = q - sold
                tot += price * sold + salvage * left - cost * q
            avg = tot / n_days
            if avg > best_profit:
                best_profit = avg
                best_q = q
        per_seed_exp_profit.append(best_profit)
        per_seed_q.append(float(best_q))

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    cu = price - cost
    co = cost - salvage
    q_star = mu + sd * inv_phi(cu / (cu + co)) if (cu + co) > 0 else mu
    q_out = per_seed_q[0] if per_seed_q else q_star
    out = {
        "exp_profit": exp_profit,
        "q": q_out,
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": [a.seed_start + s for s in range(a.seeds)],
        "seeds_used": len(per_seed_exp_profit),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
