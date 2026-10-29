import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--horizon", type=float, default=8760.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    D_annual = 1000.0
    K = 200.0
    h = 2.0
    
    q_opt = math.sqrt(2 * K * D_annual / h)
    
    horizon_hours = args.horizon
    if horizon_hours <= 0:
        horizon_hours = 8760.0
        
    time_unit = "hour"
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    
    for s in seed_list:
        rng = random.Random(s)
        
        demand_rate_per_hour = D_annual / 8760.0
        
        current_time = 0.0
        inventory_level = q_opt
        last_order_time = 0.0
        total_cost_accumulated = 0.0
        
        warmup_fraction = 0.25
        warmup_end_time = horizon_hours * (1 - warmup_fraction)
        
        stats_start_time = warmup_end_time
        
        avg_inventory_integral = 0.0
        last_stats_time = stats_start_time
        
        while current_time < horizon_hours:
            next_demand_time = current_time + rng.expovariate(demand_rate_per_hour)
            
            if next_demand_time > horizon_hours:
                break
                
            if current_time >= stats_start_time and last_stats_time < stats_start_time:
                 pass
            
            if current_time >= stats_start_time:
                dt = next_demand_time - current_time
                avg_inventory_integral += inventory_level * dt
                last_stats_time = next_demand_time
            
            inventory_level -= 1.0
            current_time = next_demand_time
            
            if inventory_level <= 0:
                order_qty = q_opt
                inventory_level += order_qty
                setup_cost = K
                holding_cost_since_last_order = 0.0 
                
                if current_time >= stats_start_time:
                    total_cost_accumulated += setup_cost
                
                last_order_time = current_time

        if horizon_hours > stats_start_time:
            final_dt = horizon_hours - last_stats_time
            if final_dt > 0:
                avg_inventory_integral += inventory_level * final_dt
        
        estimated_avg_inv = avg_inventory_integral / (horizon_hours - stats_start_time) if (horizon_hours - stats_start_time) > 0 else 0
        
        per_seed_q.append(q_opt)

    cost = math.sqrt(2 * K * D_annual * h)
    
    result = {
        "cost": round(cost, 2),
        "q": round(q_opt, 2),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
