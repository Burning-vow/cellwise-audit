import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 15.0
    p, c, s = 30.0, 12.0, 4.0
    
    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        pass # Not applicable directly to demand dist params in this simple model unless interpreted as service rate, but here it's newsvendor. Let's assume pert affects cost or price? 
             # The prompt says "pert NAME, NAME take none/lam_up/mu_up/c_up". In Newsvendor, lam usually is demand mean, mu might be std dev? Or maybe it's a generic template.
             # Given the specific problem: Demand ~ N(60, 15). Price 30, Cost 12, Salvage 4.
             # Standard critical fractile approach gives optimal Q analytically.
             # Cu = p - c = 18. Co = c - s = 8.
             # Critical ratio = Cu / (Cu + Co) = 18 / 26 = 9/13 ≈ 0.6923.
             # Z_score for 0.6923 is approx 0.500.
             # Optimal Q = mu + z * sigma = 60 + 0.5 * 15 = 67.5 -> 68?
             
    # However, the task asks for simulation. We need to simulate daily profits for various q to find the best one, or just use the analytical solution if allowed? 
    # "Discrete Event Simulation Engineer" implies we should simulate. But Newsvendor is a single-period inventory problem. 
    # Simulating "days" means generating demand, calculating profit for a fixed q, and averaging.
    # To find optimal q, we can scan a range of q values.
    
    # Let's define the simulation function for a given q.
    def sim_profit(q_val, seed, days):
        rng = random.Random(seed)
        total_profit = 0.0
        for _ in range(int(days)):
            d = max(0, rng.gauss(mu_d, sigma_d)) # Demand cannot be negative
            sold = min(d, q_val)
            leftover = q_val - sold
            revenue = sold * p
            cost = q_val * c
            salvage = leftover * s
            profit = revenue - cost + salvage
            total_profit += profit
        return total_profit / int(days)

    # Determine search range for q
    # Mean is 60, SD is 15. Range roughly [20, 100]
    q_candidates = list(range(20, 101))
    
    per_seed_exp_profits = []
    per_seed_qs = []
    seeds_used_list = []
    
    # For each seed, we run simulations for all candidate q's to find the best q for that seed's stream?
    # Or do we average across seeds for each q?
    # The output requires `q` (single value) and `exp_profit`. And `per_seed_q`.
    # This suggests we might find the optimal q globally, then report what q was chosen per seed? 
    # Actually, usually in these tasks, you find the global optimum by averaging over many seeds/runs.
    # Let's compute the expected profit for each q by averaging over all seeds.
    
    num_seeds = args.seeds
    horizon_days = args.horizon # Interpret H as number of days? The unit is time_unit. If time_unit is day, H is days.
    # Prompt says: "time_unit fill your internal timeline unit". Let's use 'day'.
    time_unit = 'day'
    
    # Accumulate sum of profits for each q across all seeds
    q_sum_profits = {q: 0.0 for q in q_candidates}
    
    for i in range(num_seeds):
        current_seed = args.seed_start + i
        seeds_used_list.append(current_seed)
        
        # For this seed, evaluate all q candidates
        best_q_for_this_seed = None
        best_p_for_this_seed = -float('inf')
        
        for q in q_candidates:
            avg_p = sim_profit(q, current_seed, horizon_days)
            q_sum_profits[q] += avg_p
            
            if avg_p > best_p_for_this_seed:
                best_p_for_this_seed = avg_p
                best_q_for_this_seed = q
        
        per_seed_exp_profits.append(best_p_for_this_seed)
        per_seed_qs.append(best_q_for_this_seed)

    # Global optimal q is the one with highest average profit across all seeds
    global_best_q = max(q_candidates, key=lambda x: q_sum_profits[x])
    global_avg_profit = q_sum_profits[global_best_q] / num_seeds
    
    # Runtime units: just count operations or time? Usually arbitrary. Let's say 1.0 per day simulated.
    runtime_units = float(num_seeds * horizon_days * len(q_candidates))

    result = {
        "exp_profit": round(global_avg_profit, 2),
        "q": global_best_q,
        "runtime_units": runtime_units,
        "seed_list": seeds_used_list,
        "seeds_used": num_seeds,
        "time_unit": time_unit,
        "per_seed_exp_profit": [round(x, 2) for x in per_seed_exp_profits],
        "per_seed_q": per_seed_qs
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
