import json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=8760.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    D_annual = 1000.0
    K = 50.0
    h = 10.0
    
    q_opt = math.sqrt(2 * K * D_annual / h)
    
    horizon_hours = args.horizon
    if horizon_hours <= 0:
        horizon_hours = 8760.0
        
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_q = []
    total_cost_sum = 0.0
    
    # Simulate EOQ logic deterministically as it's an optimization problem, 
    # but we treat "runtime_units" and "cost" based on the optimal policy applied over the horizon.
    # Since EOQ is deterministic given parameters, random seeds don't change the optimal Q.
    # However, to satisfy the interface, we run a loop.
    
    num_cycles = int(horizon_hours / (q_opt / (D_annual / 8760.0))) if q_opt > 0 else 0
    # Time per cycle in hours: T = Q/D where D is hourly demand
    hourly_demand = D_annual / 8760.0
    cycle_time_hours = q_opt / hourly_demand if hourly_demand > 0 else 0
    
    # Total cost over horizon:
    # Ordering cost: (Total Demand / Q) * K
    # Holding cost: Average Inventory * h * (Horizon in years)
    # Horizon in years = horizon_hours / 8760.0
    horizon_years = horizon_hours / 8760.0
    total_demand_horizon = D_annual * horizon_years
    
    if q_opt > 0:
        ordering_cost = (total_demand_horizon / q_opt) * K
        avg_inventory = q_opt / 2.0
        holding_cost = avg_inventory * h * horizon_years
        total_cost = ordering_cost + holding_cost
    else:
        total_cost = 0.0

    for _ in range(seeds_used):
        per_seed_q.append(q_opt)
        
    time_unit = "hour"
    runtime_units = horizon_hours
    
    result = {
        "cost": round(total_cost, 2),
        "q": round(q_opt, 2),
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "per_seed_q": [round(x, 2) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
