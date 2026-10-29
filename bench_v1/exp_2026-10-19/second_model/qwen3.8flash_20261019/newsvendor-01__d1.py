import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 15.0
    p, c, s = 20.0, 12.0, 7.0
    cu = p - c
    co = c - s
    crit_ratio = cu / (cu + co)
    
    # Optimal q via inverse normal approximation using standard library
    # We can use a simple approximation or just simulate to find best integer q
    # Since it's newsvendor, analytical solution is q* = mu + sigma * z_alpha
    # z_alpha for 0.8/0.8+0.5 = 0.8/1.3 approx 0.615 -> z ~ 0.29
    
    # Let's do a discrete search over plausible range to be robust and satisfy "simulation" vibe if needed, 
    # but the prompt asks for optimal q and expected profit. 
    # The prompt says "discrete event simulation engineer" but this is a static optimization problem essentially.
    # However, to fit the "simulation" constraint of the persona, I will simulate daily profits for candidate q values.
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    # Determine time unit: Days are natural here. But prompt requires hour/minute/second.
    # Let's assume 1 day = 24 hours. Horizon H is in days? Or hours?
    # Prompt: "H is integer style simulation horizon length, unit consistent with self-reported time_unit".
    # If I report 'hour', and H=100, that's 100 hours.
    # Newsvendor is daily. Let's map 1 day = 24 hours.
    # If H is large enough, we average over many days.
    
    time_unit = "hour"
    days_in_horizon = int(args.horizon // 24)
    if days_in_horizon < 1: days_in_horizon = 1
    
    # Search space for q
    q_min = int(mu_d - 3 * sigma_d)
    q_max = int(mu_d + 3 * sigma_d)
    
    best_q = q_min
    max_avg_profit = -float('inf')
    
    per_seed_exp_profit = []
    per_seed_q = []
    
    # For each seed, we run a simulation to estimate profit for various q?
    # That's expensive. Better: Use one long simulation per seed to evaluate all q?
    # No, demand depends on q only through sales/leftovers.
    # Profit(q, D) = p*min(q,D) + s*max(0,q-D) - c*q
    # We can generate demands once per seed and evaluate all q.
    
    for idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        demands = []
        for _ in range(days_in_horizon):
            d = rng.gauss(mu_d, sigma_d)
            if d < 0: d = 0
            demands.append(d)
        
        local_best_q = q_min
        local_max_profit = -float('inf')
        
        for q in range(q_min, q_max + 1):
            total_profit = 0.0
            for d in demands:
                sold = min(q, d)
                leftover = max(0, q - d)
                profit = p * sold + s * leftover - c * q
                total_profit += profit
            
            avg_profit = total_profit / len(demands)
            
            if avg_profit > local_max_profit:
                local_max_profit = avg_profit
                local_best_q = q
        
        per_seed_exp_profit.append(local_max_profit)
        per_seed_q.append(local_best_q)
        
        if local_max_profit > max_avg_profit:
            max_avg_profit = local_max_profit
            best_q = local_best_q
            
    # Final aggregate stats
    final_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit)
    final_q = round(sum(per_seed_q) / len(per_seed_q))
    
    output = {
        "exp_profit": final_exp_profit,
        "q": final_q,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
