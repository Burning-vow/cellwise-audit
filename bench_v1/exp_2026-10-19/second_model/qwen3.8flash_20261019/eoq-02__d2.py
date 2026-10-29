import json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=8760.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    D_annual = 1000.0
    K = 200.0
    h = 2.0
    
    # EOQ formula: q = sqrt(2*D*K / h)
    q_opt = math.sqrt(2 * D_annual * K / h)
    
    # Total relevant cost at optimal Q: TRC = sqrt(2*D*K*h)
    trc_min = math.sqrt(2 * D_annual * K * h)
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    # Since this is a deterministic optimization problem (EOQ), 
    # the result does not depend on random seeds or simulation horizon in terms of variance.
    # However, we must provide per_seed_q as requested.
    per_seed_q = [q_opt] * seeds_used
    
    output = {
        "cost": trc_min,
        "q": q_opt,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
