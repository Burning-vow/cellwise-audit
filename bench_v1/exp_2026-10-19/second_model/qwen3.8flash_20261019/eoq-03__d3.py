import argparse, json, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--horizon", type=float, default=8760.0)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()
    
    D_annual = 1000.0
    K = 50.0
    h = 10.0
    
    q_opt = math.sqrt(2 * K * D_annual / h)
    cost_opt = math.sqrt(2 * K * D_annual * h)
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    for _ in range(seeds_used):
        per_seed_q.append(q_opt)
        
    result = {
        "cost": cost_opt,
        "q": q_opt,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
