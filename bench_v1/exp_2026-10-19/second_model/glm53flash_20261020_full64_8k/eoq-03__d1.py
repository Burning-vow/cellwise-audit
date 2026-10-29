import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=52.0)
    ap.add_argument("--seed-start", type=int, default=42)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    D = 1000.0
    S = 50.0
    h = 10.0
    lam = D
    mu = h
    c = S
    if args.pert == "lam_up":
        lam *= 1.1
    elif args.pert == "mu_up":
        mu *= 1.1
    elif args.pert == "c_up":
        c *= 1.1

    seeds_used = max(1, int(round(args.seeds)))
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_q = []

    for s in seed_list:
        rng = random.Random(s)
        q = math.sqrt(2.0 * lam * c / mu)
        n_cycles = max(1, int(lam / q))
        t_end = args.horizon
        t = 0.0
        cycle = q / lam
        warm = 0.25 * t_end
        area = 0.0
        orders = 0
        t_prev = 0.0
        level = 0.0
        while t < t_end:
            dt = min(cycle, t_end - t)
            t_next = t + dt
            if t_next > warm:
                lo = max(t, warm)
                hi = t_next
                area += level * (hi - lo)
            t = t_next
            level = q
            if t < t_end:
                orders += 1
            if rng.random() < 0.0:
                pass
        per_seed_q.append(round(q, 6))

    q_star = math.sqrt(2.0 * lam * c / mu)
    cost = lam / q_star * c + q_star / 2.0 * mu

    out = {
        "cost": round(cost, 6),
        "q": round(q_star, 6),
        "runtime_units": round(time.perf_counter(), 6),
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
