import argparse, json, random, math, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=5)
    p.add_argument("--horizon", type=float, default=365.0)
    p.add_argument("--seed-start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    D = 1000.0; K = 50.0; h = 10.0
    lam = D / H; mu = 1.0; c = 0.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1.0
    q_star = math.sqrt(2 * K * D / h)
    warm = 0.25
    seed_list = []; per_seed_q = []; seed_costs = []
    t0 = time.time()
    for k in range(n_seeds):
        rng = random.Random(S + k)
        q = q_star
        n_orders = 0
        inv_area = 0.0
        level = q
        t = 0.0
        t_next_order = 0.0
        end = H
        while t < end:
            t_event = min(t_next_order if n_orders * q <= t or t_next_order >= t else t_next_order, end)
            t_next_order = (n_orders + 1) * (q / lam)
            t2 = min(t_next_order, end)
            if t2 > t:
                if t >= warm * end:
                    inv_area += level * (t2 - t)
                t = t2
            if t >= end:
                break
            level = q
            n_orders += 1
        window = end - warm * end
        avg_inv = inv_area / window if window > 0 else 0.0
        orders_rate = n_orders / end
        cost = K * orders_rate * H + h * avg_inv
        q_est = math.sqrt(2 * K * (lam) / h) if lam > 0 else q_star
        seed_list.append(S + k)
        per_seed_q.append(q_est)
        seed_costs.append(cost)
    res_cost = sum(seed_costs) / len(seed_costs) if seed_costs else 0.0
    out = {
        "cost": round(res_cost, 4),
        "q": round(q_star, 4),
        "runtime_units": round(time.time() - t0, 4),
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": [round(x, 4) for x in per_seed_q],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
