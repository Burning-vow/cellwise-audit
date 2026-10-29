import json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=8760.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    D = 5000.0 / 365.0 / 24.0
    K = 50.0
    h = 2.0 / 365.0 / 24.0
    
    q_opt = math.sqrt(2 * K * D / h)
    cost_opt = math.sqrt(2 * K * D * h)
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    for s in seed_list:
        import random
        rng = random.Random(s)
        
        t = 0.0
        horizon = args.horizon
        
        inv = q_opt
        next_order_time = horizon
        total_cost = 0.0
        
        while t < horizon:
            if inv <= 0:
                if t >= horizon: break
                inv += q_opt
                total_cost += K
                next_order_time = t + q_opt / D
            
            dt = min(next_order_time - t, horizon - t)
            if dt > 0:
                consumption = D * dt
                avg_inv = (inv + max(inv - consumption, 0)) / 2.0
                total_cost += h * avg_inv * dt
                inv -= consumption
                t += dt
            else:
                break
                
        per_seed_q.append(q_opt)

    out = {
        "cost": round(cost_opt, 2),
        "q": round(q_opt, 2),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
