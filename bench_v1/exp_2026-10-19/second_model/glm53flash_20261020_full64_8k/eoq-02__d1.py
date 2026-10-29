import argparse, json, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", default="1.0")
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", default="none")
    a = p.parse_args()
    D, S, h = 1000.0, 200.0, 2.0
    lam, mu, c = D, S, h
    if a.pert == "lam_up": lam = D * 1.1
    elif a.pert == "mu_up": mu = S * 1.1
    elif a.pert == "c_up": c = h * 1.1
    H = float(a.horizon)
    seed_list = [a.seed_start + i for i in range(max(1, a.seeds))]
    per_seed_q = []
    total_cost = 0.0
    for sd in seed_list:
        q = math.sqrt(2.0 * lam * mu / c)
        tc = lam / q * mu + q / 2.0 * c
        per_seed_q.append(q)
        total_cost += tc
    seeds_used = len(seed_list)
    cost = total_cost / seeds_used
    print(json.dumps({
        "cost": cost,
        "q": sum(per_seed_q) / seeds_used,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }))

if __name__ == "__main__":
    main()
