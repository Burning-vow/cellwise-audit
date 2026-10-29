import sys, json, math, random
from argparse import ArgumentParser

def main():
    parser = ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    p = 20.0
    c = 12.0
    s = 7.0
    
    # Critical fractile for newsvendor model: (p-c)/(p-s)
    cf = (p - c) / (p - s)
    
    # Optimal q is the quantile of the demand distribution corresponding to cf
    # For normal distribution, we can use inverse CDF. 
    # Python's statistics module doesn't have inv_cdf directly in older versions or standard lib easily without scipy.
    # We can approximate using a simple binary search on the CDF or use a known approximation.
    # Since we must use standard library only, let's implement a simple binary search for the normal quantile.
    
    def norm_cdf(x, mean, std):
        return 0.5 * (1 + math.erf((x - mean) / (std * math.sqrt(2))))
        
    def find_q(cf, mean, std):
        low = mean - 5 * std
        high = mean + 5 * std
        for _ in range(100):
            mid = (low + high) / 2
            if norm_cdf(mid, mean, std) < cf:
                low = mid
            else:
                high = mid
        return (low + high) / 2

    q_opt = find_q(cf, mu_d, sigma_d)
    
    # Expected profit calculation analytically or via simulation?
    # The problem asks for "optimal order quantity q and corresponding expected daily profit".
    # Usually, this implies the theoretical optimum. However, the output keys suggest simulation results (per_seed...).
    # Let's simulate to get per-seed estimates and average them.
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    horizon = args.horizon
    
    all_profits = []
    all_qs = []
    
    # Warmup ratio 25%
    warmup_ratio = 0.25
    
    for seed in seed_list:
        rng = random.Random(seed)
        profits = []
        qs = []
        
        # Simulate 'horizon' days
        # Note: Horizon is in time units. If time_unit is day, then H days.
        # The prompt says "time_unit" is hour/minute/second. But Newsvendor is daily.
        # Let's assume 1 unit = 1 day for simplicity, but report time_unit as "day"? 
        # Constraint: time_unit must be hour/minute/second.
        # This is a mismatch. A newsvendor problem is discrete daily.
        # Perhaps we treat each "day" as a fixed duration, e.g., 24 hours.
        # Or maybe the simulation runs for H hours, and every 24 hours an order is placed?
        # Given "daily order", let's assume the simulation clock advances by 1 day per iteration.
        # To satisfy the constraint, I will set time_unit to "hour" and assume 1 day = 24 hours.
        # So number of days = int(horizon / 24).
        
        num_days = int(horizon / 24.0)
        if num_days == 0:
            num_days = 1
            
        start_idx = int(num_days * warmup_ratio)
        
        for d in range(num_days):
            # Generate demand
            demand = rng.gauss(mu_d, sigma_d)
            if demand < 0:
                demand = 0
                
            # In simulation, do we fix q to optimal or optimize?
            # The task asks for optimal q. Usually, we calculate it once.
            # But per_seed_q suggests variation? No, q is deterministic based on parameters.
            # Unless perturbation changes parameters.
            
            current_mu = mu_d
            current_sigma = sigma_d
            current_p = p
            current_c = c
            current_s = s
            
            if args.pert == "lam_up": # Not applicable directly, maybe scale demand?
                pass
            elif args.pert == "mu_up":
                current_mu *= 1.1
            elif args.pert == "c_up":
                current_c *= 1.1
                
            # Recalculate optimal q for this seed/perturbation context if needed
            # Actually, q is usually constant across seeds unless params change.
            # Let's compute q_opt dynamically based on current params
            cf_curr = (current_p - current_c) / (current_p - current_s)
            q_curr = find_q(cf_curr, current_mu, current_sigma)
            
            # Profit calculation
            sold = min(demand, q_curr)
            leftover = max(0, q_curr - demand)
            revenue = sold * current_p
            cost = q_curr * current_c
            salvage = leftover * current_s
            profit = revenue - cost + salvage
            
            if d >= start_idx:
                profits.append(profit)
                qs.append(q_curr)
                
        if not profits:
            exp_profit = 0.0
            avg_q = 0.0
        else:
            exp_profit = sum(profits) / len(profits)
            avg_q = sum(qs) / len(qs)
            
        all_profits.append(exp_profit)
        all_qs.append(avg_q)
        
    final_exp_profit = sum(all_profits) / len(all_profits) if all_profits else 0.0
    final_q = sum(all_qs) / len(all_qs) if all_qs else 0.0
    
    result = {
        "exp_profit": round(final_exp_profit, 4),
        "q": round(final_q, 4),
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_exp_profit": [round(p, 4) for p in all_profits],
        "per_seed_q": [round(q, 4) for q in all_qs]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
