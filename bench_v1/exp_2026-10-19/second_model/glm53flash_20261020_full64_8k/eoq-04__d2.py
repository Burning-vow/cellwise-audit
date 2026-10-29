import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=87600.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D_YEAR = 1000.0
    HOURS = 8760.0
    lam = D_YEAR / HOURS
    K, h = 200.0, 10.0
    q_opt = math.sqrt(2 * K * D_YEAR / h)

    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        h *= 1.1
    elif a.pert == "c_up":
        K *= 1.1

    q = q_opt
    per_seed_q, seed_list = [], []
    t0 = time.time()
    burn = 0.25

    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        inv = q
        t = 0.0
        next_dem = rng.expovariate(lam)
        orders = 0
        hold_cost = 0.0
        ord_cost = 0.0
        tw = 0.0
        warm_t = a.horizon * burn
        while t < a.horizon:
            if next_dem > a.horizon:
                dt = a.horizon - t
                if t >= warm_t:
                    hold_cost += h / HOURS * inv * dt
                    tw += dt
                inv -= lam * dt
                t = a.horizon
                break
            dt = next_dem - t
            if t >= warm_t:
                hold_cost += h / HOURS * inv * dt
                tw += dt
            t = next_dem
            inv -= 1.0
            if t >= warm_t:
                tw += 0.0
            if inv <= 0:
                inv = q
                orders += 1
                if t >= warm_t:
                    ord_cost += K
            next_dem = t + rng.expovariate(lam)

        demand_w = lam * (a.horizon - warm_t)
        q_hat = demand_w / orders if orders > 0 else q
        per_seed_q.append(q_hat)

    seeds_used = a.seeds
    total_dem = lam * (a.horizon * 0.75)
    mean_q = sum(per_seed_q) / seeds_used if seeds_used else q
    orders_tot = total_dem / mean_q if mean_q > 0 else 0
    cost = K * orders_tot + h * mean_q / 2.0
    runtime = time.time() - t0
    print(json.dumps({
        "cost": cost,
        "q": mean_q,
        "runtime_units": runtime,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }))

if __name__ == "__main__":
    main()
