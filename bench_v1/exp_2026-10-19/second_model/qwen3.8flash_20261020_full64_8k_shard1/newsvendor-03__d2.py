import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    price = 30.0
    cost = 12.0
    salvage = 4.0

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        # Approximation for inverse normal CDF using rational approximation
        # Abramowitz and Stegun formula 26.2.23
        if p < 0.5:
            t = math.sqrt(-2 * math.log(p))
        else:
            t = math.sqrt(-2 * math.log(1 - p))
        
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        
        z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
        if p < 0.5:
            return -z
        else:
            return z

    q_opt = mu_d + sigma_d * norm_ppf(critical_ratio)
    
    # Calculate expected profit analytically or via simulation? 
    # The prompt asks for "optimal order quantity q" and "expected daily profit".
    # Since it's a discrete event simulation engineer role, but the problem is static optimization,
    # I will compute the optimal q analytically as above.
    # For expected profit, we can integrate or use standard newsvendor formulas.
    # E[Profit] = (p-c)*mu - (p-s)*E[(q-D)^+] ... actually simpler:
    # E[Profit] = (p-c)*q - (p-s)*E[(q-D)^+] is not quite right because sales are min(q,D).
    # Profit = p*min(q,D) - c*q + s*(q-min(q,D)) = (p-s)*min(q,D) - (c-s)*q
    # E[min(q,D)] = mu - integral_{q}^{inf} (x-q)f(x)dx ...
    # Let's just simulate to get the per-seed estimates as requested by output format keys like per_seed_exp_profit.
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_exp_profit = []
    per_seed_q = []
    
    total_profit_sum = 0.0
    
    for i in range(seeds_used):
        seed = seed_list[i]
        rng = random.Random(seed)
        
        # Use fixed optimal q for all seeds to estimate its profit, 
        # OR should we optimize per seed? The question asks for THE optimal q.
        # Usually, in such tasks, q is the global optimum derived from parameters.
        # However, "per_seed_q" suggests variation. But Newsvendor q is deterministic given params.
        # If perturbation changes params, q might change. Here pert is none/lam_up etc.
        # Let's assume q is calculated once based on base parameters unless pert affects them.
        # Perturbations: lam_up/mu_up/c_up likely affect demand mean/std or cost.
        
        current_mu = mu_d
        current_sigma = sigma_d
        current_cost = cost
        
        if args.pert == "lam_up":
            current_mu *= 1.1
        elif args.pert == "mu_up":
            current_mu *= 1.1
        elif args.pert == "c_up":
            current_cost *= 1.1
            
        cu_c = price - current_cost
        co_c = current_cost - salvage
        cr_c = cu_c / (cu_c + co_c)
        q_current = current_mu + current_sigma * norm_ppf(cr_c)
        
        # Simulate horizon days
        num_days = int(args.horizon)
        if num_days <= 0: num_days = 1
        
        day_profits = []
        for _ in range(num_days):
            demand = rng.gauss(current_mu, current_sigma)
            if demand < 0: demand = 0
            sales = min(q_current, demand)
            leftover = max(0, q_current - demand)
            profit = price * sales - current_cost * q_current + salvage * leftover
            day_profits.append(profit)
            
        avg_profit = sum(day_profits) / len(day_profits)
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_current)
        total_profit_sum += avg_profit

    overall_exp_profit = total_profit_sum / seeds_used if seeds_used > 0 else 0.0
    final_q = sum(per_seed_q) / seeds_used if seeds_used > 0 else q_opt
    
    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": round(final_q, 4),
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
