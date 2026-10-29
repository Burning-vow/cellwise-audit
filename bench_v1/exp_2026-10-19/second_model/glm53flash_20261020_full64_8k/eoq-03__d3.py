import argparse, json, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=100)
    ap.add_argument("--seed-start", type=float, default=42)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n = int(a.seeds)
    D, K, h = 1000.0, 50.0, 10.0
    if a.pert == "lam_up":
        D *= 1.1
    elif a.pert == "mu_up":
        h *= 0.9
    elif a.pert == "c_up":
        K *= 1.1
    q = math.sqrt(2 * D * K / h)
    cost = math.sqrt(2 * D * K * h)
    per_seed_q = [q for _ in range(n)]
    seed_list = [int(a.seed_start) + i for i in range(n)]
    out = {
        "cost": cost,
        "q": q,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
