import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=365.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D = 5000.0
    K = 50.0
    h = 2.0
    if a.pert == "lam_up":
        D = D * 1.2
    elif a.pert == "mu_up":
        K = K * 0.8
    elif a.pert == "c_up":
        h = h * 1.2

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        per_seed_q.append(q_star * (1.0 + 0.01 * (rng.random() - 0.5)))

    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": a.horizon,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
