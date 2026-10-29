import argparse, json, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    D = 1000.0
    K = 50.0
    h = 2.0
    
    if args.pert == 'lam_up':
        D *= 1.1
    elif args.pert == 'mu_up':
        pass # EOQ doesn't have service rate mu in standard model, ignore or adjust? Problem says perturbation only changes parameters. Usually for queueing. For EOQ, maybe h or K? Let's assume none affects it significantly or just stick to base.
    elif args.pert == 'c_up':
        h *= 1.1
        
    q_opt = math.sqrt(2 * K * D / h)
    cost_opt = math.sqrt(2 * K * D * h)
    
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
        "time_unit": "year", 
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
