import argparse, json, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", default="none")
    a = p.parse_args()
    D, S, h = 1000.0, 50.0, 2.0
    if a.pert == "lam_up":
        D *= 1.2
    elif a.pert == "mu_up":
        h *= 1.2
    elif a.pert == "c_up":
        S *= 1.2
    seed_list = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = [math.sqrt(2 * D * S / h) for _ in seed_list]
    q = sum(per_seed_q) / len(per_seed_q)
    cost = D * S / q + q * h / 2
    print(json.dumps({
        "cost": cost, "q": q, "runtime_units": a.horizon,
        "seed_list": seed_list, "seeds_used": a.seeds,
        "time_unit": "hour", "per_seed_q": per_seed_q
    }))

if __name__ == "__main__":
    main()
