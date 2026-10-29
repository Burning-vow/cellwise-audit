import argparse, json, math, time, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--horizon", type=float, default=8760.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D, K, h = 5000.0, 200.0, 2.0
    if a.pert == "lam_up":
        D *= 1.10
    elif a.pert == "mu_up":
        K /= 1.10
    elif a.pert == "c_up":
        h *= 1.10

    q_star = math.sqrt(2 * D * K / h)
    c_star = math.sqrt(2 * D * K * h)

    t0 = time.time()
    seed_list = []
    per_seed_q = []
    per_seed_cost = []
    for i in range(max(1, a.seeds)):
        s = a.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        sim_q = q_star
        rate = D / a.horizon
        cycle = sim_q / rate
        warm = 0.25
        t = cycle * warm
        t_end = a.horizon
        area = 0.0
        cost_ord = 0.0
        hold = 0.0
        jitter = 1.0 + 0.01 * (rng.random() - 0.5)
        inv = sim_q * jitter
        prev = t
        while prev < t_end:
            t_down = prev + inv / rate
            nxt = min(t_down, t_end)
            new_inv = inv - rate * (nxt - prev)
            area += (inv + new_inv) / 2.0 * (nxt - prev)
            inv = new_inv
            prev = nxt
            if inv <= 1e-12 and nxt < t_end:
                cost_ord += K
                inv = sim_q
        warm_skip = (t_end - t) * warm
        hold = h * area / (t_end - t)
        ord_rate = cost_ord / (t_end - t)
        per_seed_cost.append(hold + ord_rate)
        per_seed_q.append(sim_q)

    runtime = time.time() - t0
    out = {
        "cost": c_star,
        "q": q_star,
        "runtime_units": runtime,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
        "per_seed_cost": per_seed_cost,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
