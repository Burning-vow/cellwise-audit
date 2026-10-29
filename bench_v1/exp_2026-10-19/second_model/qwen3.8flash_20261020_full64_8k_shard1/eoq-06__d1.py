import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--horizon", type=float, default=8760.0)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    D_annual = 5000.0
    K = 200.0
    h = 2.0
    
    q_opt = math.sqrt(2 * K * D_annual / h)
    cost_opt = (D_annual / q_opt) * K + (q_opt / 2.0) * h
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    total_cost_sum = 0.0
    
    time_unit = "hour"
    horizon_hours = args.horizon
    
    for s in seed_list:
        rng = random.Random(s)
        
        # Simulate EOQ logic over the horizon to estimate q and cost
        # In deterministic EOQ, orders are placed when inventory hits zero.
        # We simulate discrete events of demand consumption and replenishment.
        
        current_time = 0.0
        inventory = q_opt
        last_order_time = -math.inf
        
        # To make it a simulation with randomness as per prompt style, 
        # we can add slight noise to demand rate or just track the deterministic cycle.
        # However, standard EOQ is deterministic. The prompt asks for a simulation engineer role.
        # Let's assume uniform demand rate r = D_annual / 8760 per hour.
        
        r = D_annual / 8760.0
        
        # Adjust parameters if perturbation exists
        if args.pert == "lam_up":
            r *= 1.1
        elif args.pert == "mu_up":
            pass # Not applicable directly to EOQ params in this simple model
        elif args.pert == "c_up":
            h *= 1.1
            
        q_sim = q_opt
        if args.pert == "c_up":
             q_sim = math.sqrt(2 * K * (r * 8760) / h)
             
        # Simulate cycles
        num_cycles = int(horizon_hours / (q_sim / r)) if r > 0 else 0
        
        # Warmup removal: skip first 25% of time
        warmup_end = 0.25 * horizon_hours
        
        accumulated_cost = 0.0
        accumulated_time = 0.0
        
        t = 0.0
        inv = q_sim
        
        while t < horizon_hours:
            # Time until next order (inventory depletion)
            if r <= 0: break
            dt_to_empty = inv / r
            event_time = min(t + dt_to_empty, horizon_hours)
            
            # Integrate holding cost for this interval
            # Average inventory during linear depletion from inv to 0 is inv/2
            avg_inv = inv / 2.0
            duration = event_time - t
            
            if t >= warmup_end:
                accumulated_cost += avg_inv * h * duration
                accumulated_time += duration
                
            t = event_time
            inv = 0.0
            
            if t >= horizon_hours:
                break
                
            # Place order
            if t >= warmup_end:
                accumulated_cost += K
                accumulated_time += 0 # Order placement is instantaneous in basic EOQ sim? 
                                      # Or we count the fixed cost occurrence.
                
            inv = q_sim
            
        # Estimate q based on observed cycles in valid window
        # This is a bit abstract for pure EOQ, but we report the theoretical q used in sim
        per_seed_q.append(q_sim)
        total_cost_sum += accumulated_cost
        
    avg_cost = total_cost_sum / seeds_used if seeds_used > 0 else 0.0
    
    result = {
        "cost": round(avg_cost, 4),
        "q": round(q_opt, 4),
        "runtime_units": horizon_hours,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
