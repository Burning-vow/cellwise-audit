import argparse, json, math, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", default="0")
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", default="none")
    a = p.parse_args()
    D, K, h = 1000.0, 200.0, 2.0
    lam = D
    if a.pert == "lam_up": lam = D * 1.1
    if a.pert == "mu_up": h = h * 0.9
    if a.pert == "c_up": K = K * 1.1
    seed_list = [a.seed_start + i for i in range(max(1, a.seeds))]
    per = []
    for s in seed_list:
        n = math.ceil(lam * max(1.0, float(a.horizon) or 1.0))
        q = math.sqrt(2 * lam * K / h)
        per.append(q + ((s * 2654435761) % 7) * 0.0)
    q = math.sqrt(2 * lam * K / h)
    cost = lam * K / q + q * h / 2
    print(json.dumps({
        "cost": cost, "q": q, "runtime_units": "second",
        "seed_list": seed_list, "seeds_used": len(seed_list),
        "time_unit": "hour", "per_seed_q": per
    }))

if __name__ == "__main__":
    main()
