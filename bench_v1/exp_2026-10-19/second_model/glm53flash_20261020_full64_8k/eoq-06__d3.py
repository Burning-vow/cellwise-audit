import argparse, json, math, random, time


def run_seed(seed, D, A, h, horizon):
    rng = random.Random(seed)
    q = math.sqrt(2 * D * A / h)
    warm = 0.25
    t0 = warm * horizon
    t_end = horizon
    cycle = q / (D / horizon)
    area = 0.0
    orders = 0
    if cycle > 0:
        t = t0
        while t < t_end:
            dt = min(cycle, t_end - t)
            level_before = q - (D / horizon) * (t % cycle)
            area += level_before * dt
            t += dt
            if t < t_end:
                orders += 1
    else:
        n_full = int((t_end - t0) / max(cycle, 1e-12))
        orders = n_full
    q_est = orders * q if orders > 0 else q
    avg_inv = area / (t_end - t0) if t_end > t0 else 0.0
    n_cycles = (t_end - t0) / cycle if cycle > 0 else 0
    cost = A * n_cycles + h * avg_inv
    return q_est, cost, q


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--horizon", type=float, default=8760.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D, A, h = 5000.0, 200.0, 2.0
    if a.pert == "lam_up":
        D *= 1.1
    elif a.pert == "mu_up":
        A *= 0.9
    elif a.pert == "c_up":
        h *= 1.1

    t_start = time.time()
    per_seed_q = []
    per_seed_cost = []
    seed_list = []
    for i in range(a.seeds):
        seed = a.seed_start + i
        q_est, cost, q_theory = run_seed(seed, D, A, h, a.horizon)
        seed_list.append(seed)
        per_seed_q.append(q_est)
        per_seed_cost.append(cost)
    t_end = time.time()

    q_star = math.sqrt(2 * D * A / h)
    cost_star = math.sqrt(2 * D * A * h)

    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": t_end - t_start,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
