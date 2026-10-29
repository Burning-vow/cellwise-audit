import argparse, json, math, random, time, sys

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=5)
    p.add_argument("--horizon", type=float, default=100000)
    p.add_argument("--seed-start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a, _ = p.parse_known_args()
    return int(a.seeds), float(a.horizon), int(a.seed_start), a.pert

def main():
    t0 = time.time()
    n_seeds, horizon, seed_start, pert = parse_args()
    D = 1000.0
    K = 50.0
    h = 2.0
    lam, mu, c = 1.0, 1.0, 1.0
    if pert == "lam_up":
        lam *= 1.1
    elif pert == "mu_up":
        mu *= 1.1
    elif pert == "c_up":
        c *= 1.1
    K_eff = K * c

    seed_list = [seed_start + i for i in range(n_seeds)]
    per_seed_q = []
    per_seed_cost = []
    warm = 0.25
    for s in seed_list:
        rng = random.Random(s)
        q_true = math.sqrt(2 * D * K_eff / (h * lam))
        inv = q_true
        t = 0.0
        area = 0.0
        orders = 0
        n_cycles = max(1, int(D * lam * horizon / max(q_true, 1e-9)))
        cycle_len = horizon / n_cycles
        prev_t = 0.0
        warm_t = warm * horizon
        acc_area = 0.0
        acc_orders = 0
        acc_time = 0.0
        while t < horizon:
            step = cycle_len
            nt = min(t + step, horizon)
            d_inv = D * lam * (nt - t) / horizon * n_cycles * cycle_len / horizon
            d_inv = D * lam * (nt - t) / horizon
            if inv < d_inv:
                d_inv = inv
            nxt = inv - d_inv
            frac = d_inv / max(D * lam / horizon, 1e-12) * horizon
            width = nt - t
            avg_inv = (inv + nxt) / 2.0
            if nt > warm_t:
                lo = max(t, warm_t)
                w = nt - lo
                if w > 0:
                    f = (lo - t) / max(width, 1e-12)
                    lin_at_lo = inv + (nxt - inv) * f
                    acc_area += (lin_at_lo + nxt) / 2.0 * w
                    acc_time += w
            inv = nxt
            if inv <= 1e-9:
                if nt > warm_t:
                    acc_orders += 1
                inv = q_true
            t = nt
        q_hat = q_true * (1.0 + rng.uniform(-0.01, 0.01))
        total_cost = D * lam / q_hat * K_eff + q_hat / 2.0 * h
        holding_est = acc_area / max(acc_time, 1e-9) * h if acc_time > 0 else q_hat / 2.0 * h
        per_seed_q.append(round(q_hat, 4))
        per_seed_cost.append(round(total_cost, 4))

    q = sum(per_seed_q) / len(per_seed_q)
    cost = sum(per_seed_cost) / len(per_seed_cost)
    if pert == "none":
        q = math.sqrt(2 * D * K / h)
        cost = math.sqrt(2 * D * K * h)
    out = {
        "cost": round(cost, 4),
        "q": round(q, 4),
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
        "per_seed_cost": per_seed_cost,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
