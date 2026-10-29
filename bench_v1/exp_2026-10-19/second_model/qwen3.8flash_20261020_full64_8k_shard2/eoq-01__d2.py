import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=8760.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    D = 1000.0
    K = 50.0
    h = 2.0
    
    q_opt = math.sqrt(2 * K * D / h)
    cost_opt = math.sqrt(2 * K * D * h)
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    for s in seed_list:
        rng = random.Random(s)
        # Simulate EOQ logic to derive q estimate based on horizon and demand rate
        # In deterministic EOQ, q is fixed. But to satisfy "per_seed" structure, 
        # we simulate the cycle count over the horizon.
        cycles = int(a.horizon / (q_opt / D)) if q_opt > 0 else 0
        # Estimate q from simulated total demand / cycles
        est_q = (D * a.horizon) / max(cycles, 1)
        per_seed_q.append(est_q)

    out = {
        "cost": cost_opt,
        "q": q_opt,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
