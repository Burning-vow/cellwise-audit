import argparse, json, math, random, heapq

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    D = 1000.0; K = 200.0; h = 2.0
    lam = D; mu = 1.0; c = 0.0
    if a.pert == "lam_up": lam = D * 1.1
    elif a.pert == "mu_up": mu = 1.1
    elif a.pert == "c_up": c = 1.0
    q_star = math.sqrt(2 * K * lam / (h + c if h + c > 0 else h))
    per_seed_q = []
    seed_list = []
    for s in range(seeds):
        seed = S + s
        rng = random.Random(seed)
        seed_list.append(seed)
        q = q_star
        t = 0.0
        level = 0.0
        pending = False
        area = 0.0
        n_orders = 0
        warm_end = H * 0.25
        events = []
        def schedule_demand(t):
            heapq.heappush(events, (t + rng.expovariate(lam), 0))
        schedule_demand(0.0)
        last = 0.0
        while events:
            te, kind = heapq.heappop(events)
            if te > H:
                break
            if te >= warm_end:
                area += level * (te - max(last, warm_end))
            last = te
            if kind == 0:
                if level > 0:
                    level -= 1.0
                schedule_demand(te)
            if level <= 0 and not pending:
                q = q_star * (1.0 + 0.05 * (rng.random() - 0.5))
                level += q
                pending = False
                if te >= warm_end:
                    n_orders += 1
        T = H - warm_end
        hold = area / T
        ordc = n_orders * K / T
        cost = hold + ordc
        per_seed_q.append(q)
        seed_cost = cost
    avg_cost = seed_cost
    out = {
        "cost": avg_cost,
        "q": q_star,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": seeds,
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
