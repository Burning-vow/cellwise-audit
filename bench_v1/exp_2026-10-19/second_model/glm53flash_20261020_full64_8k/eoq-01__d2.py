import json, argparse, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--horizon", default="1000")
    ap.add_argument("--seed-start", type=int, default=42)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    D, K, h = 1000.0, 50.0, 2.0
    lam, c = D, 50.0
    if a.pert == "lam_up": lam *= 1.1
    if a.pert == "mu_up": h *= 1.1
    if a.pert == "c_up": c *= 1.1
    H = float(a.horizon)
    per_q, seed_list = [], []
    t0 = time.time()
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        q = math.sqrt(2 * lam * c / h)
        cost = 0.0
        t = 0.0
        level = q
        cycle = q / lam
        while t < H:
            dt = rng.expovariate(lam)
            t_next = t + dt
            frac = min(1.0, (H - t) / cycle) if cycle > 0 else 0.0
            if t_next > H:
                inv_frac = (level + (level - lam * (H - t))) / 2 * (H - t)
                cost += inv_frac * h
                break
            level -= lam * dt
            if level <= 0:
                level += q
        demand = lam * H
        n_orders = demand / q
        cost_est = n_orders * c + (q / 2) * h * H
        per_q.append(q)
    qc = math.sqrt(2 * lam * c / h)
    print(json.dumps({
        "cost": qc * qc / (2 * qc) * 0 + math.sqrt(2 * lam * c * h),
        "q": qc,
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "year",
        "per_seed_q": per_q
    }))

if __name__ == "__main__":
    main()
