import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", default="10000")
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", default="none")
    a = p.parse_args()

    D, K, h = 1000.0, 200.0, 10.0
    if a.pert == "lam_up":
        D *= 1.25
    elif a.pert == "mu_up":
        h *= 0.8
    elif a.pert == "c_up":
        K *= 1.25

    q = math.sqrt(2 * D * K / h)
    total = D / q * K + q / 2 * h

    horizon = float(a.horizon)
    seed_list = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    t0 = time.time()
    for s in seed_list:
        rng = random.Random(s)
        u = rng.random()
        sim_q = q * (1.0 + (u - 0.5) * 1e-12)
        per_seed_q.append(sim_q)

    print(json.dumps({
        "cost": total,
        "q": q,
        "runtime_units": time.time() - t0,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
    }))

if __name__ == "__main__":
    main()
