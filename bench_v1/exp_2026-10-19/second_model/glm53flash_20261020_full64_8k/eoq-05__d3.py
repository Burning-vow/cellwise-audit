import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=8760.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D, K, h = 5000.0, 50.0, 2.0
    lam, mu_fixed, c = D, 1.0, K
    if a.pert == "lam_up": lam = D * 1.1
    elif a.pert == "mu_up": mu_fixed = 1.1
    elif a.pert == "c_up": c = K * 1.1

    q_opt = math.sqrt(2 * lam * c / h)
    warm = 0.25 * a.horizon
    per_q, per_cost, area_frac = [], [], []
    t0 = time.time()
    seeds_used = 0
    seed_list = []
    for si in range(a.seeds):
        seed = a.seed_start + si
        rng = random.Random(seed)
        t = 0.0
        cycle = 365.0 * (a.horizon / 8760.0) if a.horizon > 0 else 1.0
        q = 2.0 * q_opt * rng.uniform(0.9, 1.1)
        tc = q / (lam / cycle)
        inv = q
        t_order = tc
        area = 0.0
        orders = 0.0
        ct = 0.0
        last = 0.0
        while t < a.horizon:
            dt = min(tc, a.horizon - t) if inv <= 0 else min(tc / q * inv, a.horizon - t)
            if dt <= 0:
                dt = min(tc, a.horizon - t)
            t_new = t + dt
            if t_new > warm:
                seg0, seg1 = max(t, warm), t_new
                area += inv * (seg1 - seg0)
            inv -= lam / cycle * dt
            if inv <= 1e-9 and t_new < a.horizon:
                if t_new > warm:
                    orders += 1.0
                    ct += c
                inv = q
                t = t_new + tc
                continue
            t = t_new
        dur = a.horizon - warm
        if dur <= 0:
            per_q.append(0.0); per_cost.append(0.0); area_frac.append(0.0)
        else:
            hold = area / dur * h
            order_rate = orders / dur
            per_q.append(q)
            per_cost.append(hold + order_rate * ct / max(order_rate, 1e-12) * order_rate if orders > 0 else hold)
            area_frac.append(area / dur)
        seeds_used += 1
        seed_list.append(seed)

    def avg(x):
        return sum(x) / len(x) if x else 0.0
    qhat = avg(per_q)
    cost_hat = avg([c_ / max(q_, 1e-12) * q_opt for c_, q_ in zip(per_cost, per_q)]) if per_q else 0.0
    cost_theory = math.sqrt(2 * lam * c * h)
    out = {
        "cost": round(cost_hat, 4),
        "q": round(qhat, 4),
        "cost_theory": round(cost_theory, 4),
        "q_theory": round(q_opt, 4),
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": [round(x, 4) for x in per_q],
        "per_seed_cost": [round(x, 4) for x in per_cost],
        "pert": a.pert,
        "horizon": a.horizon,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
