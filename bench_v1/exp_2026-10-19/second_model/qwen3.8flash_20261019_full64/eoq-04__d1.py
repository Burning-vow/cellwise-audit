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
    h = 10.0
    q_opt = math.sqrt(2 * K * D_annual / h)
    cost_opt = math.sqrt(2 * K * D_annual * h)

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    per_seed_q = []

    time_unit = "hour"
    horizon_hours = args.horizon
    if horizon_hours <= 0:
        horizon_hours = 8760.0

    demand_rate_per_hour = D_annual / (365.0 * 24.0)

    for s in seed_list:
        rng = random.Random(s)
        total_demand = 0.0
        t = 0.0
        next_arrival = rng.expovariate(demand_rate_per_hour) if demand_rate_per_hour > 0 else float('inf')
        
        while t < horizon_hours:
            if next_arrival < horizon_hours:
                t = next_arrival
                total_demand += 1.0
                next_arrival = t + rng.expovariate(demand_rate_per_hour) if demand_rate_per_hour > 0 else float('inf')
            else:
                break
        
        estimated_D = total_demand / (horizon_hours / (365.0 * 24.0)) if horizon_hours > 0 else D_annual
        if estimated_D <= 0:
            estimated_D = D_annual
            
        q_est = math.sqrt(2 * K * estimated_D / h)
        per_seed_q.append(q_est)

    result = {
        "cost": cost_opt,
        "q": q_opt,
        "runtime_units": horizon_hours,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
