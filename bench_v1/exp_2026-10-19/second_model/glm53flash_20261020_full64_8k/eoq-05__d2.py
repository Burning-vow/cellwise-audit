import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()

    D, K, h = 5000.0, 50.0, 2.0
    if a.pert == "lam_up":
        D *= 1.1
    elif a.pert == "mu_up":
        h *= 0.9
    elif a.pert == "c_up":
        K *= 1.1

    q = math.sqrt(2.0 * D * K / h)
    per_seed_q = []
    per_seed_cost = []
    t0 = time.time()
    for i in range(a.seeds):
        rng = random.Random(a.seed_start + i)
        s = rng.random()
        q_i = q * (1.0 + 0.02 * (s - 0.5))
        n_orders = math.ceil(a.horizon * D / q_i)
        inv_area = 0.0
        t = 0.0
        level = 0.0
        tc = q_i
        cycle = q_i / D
        while t < a.horizon:
            dt = min(cycle, a.horizon - t)
            inv_area += level * dt
            t += dt
            level = q_i
        cost_i = (n_orders * K + inv_area * h) / a.horizon
        per_seed_q.append(q_i)
        per_seed_cost.append(cost_i)
    cost = sum(per_seed_cost) / len(per_seed_cost)
    out = {
        "cost": cost,
        "q": q,
        "runtime_units": time.time() - t0,
        "seed_list": list(range(a.seed_start, a.seed_start + a.seeds)),
        "seeds_used": a.seeds,
        "time_unit": "year",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
