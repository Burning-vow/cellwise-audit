import argparse, json, math, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=1)
    p.add_argument("--horizon", type=float, default=1.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", default="none")
    a = p.parse_args()

    D = 5000.0
    K = 200.0
    h = 2.0
    if a.pert == "lam_up":
        D = D * 1.1
    elif a.pert == "mu_up":
        h = h / 1.1
    elif a.pert == "c_up":
        K = K * 1.1

    t0 = time.time()
    n = max(1, int(a.seeds))
    seed_list = list(range(a.seed_start, a.seed_start + n))
    per_seed_q = []
    per_seed_cost = []
    for s in seed_list:
        q = math.sqrt(2 * D * K / h)
        cost = math.sqrt(2 * D * K * h)
        per_seed_q.append(q)
        per_seed_cost.append(cost)
    q = sum(per_seed_q) / len(per_seed_q)
    cost = sum(per_seed_cost) / len(per_seed_cost)
    out = {
        "cost": cost,
        "q": q,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
        "per_seed_cost": per_seed_cost,
        "horizon": a.horizon,
        "pert": a.pert,
        "runtime": time.time() - t0,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
