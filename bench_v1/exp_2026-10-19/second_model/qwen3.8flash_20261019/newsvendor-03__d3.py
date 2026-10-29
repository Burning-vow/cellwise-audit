import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    p = 30.0
    c = 12.0
    s = 4.0
    
    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        pass # Newsvendor doesn't have service rate in same sense, but maybe cost? No, pert usually affects demand or costs. Let's assume mu_up affects mean demand slightly differently or ignore if not applicable to structure. But prompt says "disturbance only changes parameters". For newsvendor, typical perturbations are on demand mean/std or costs. 
        # Let's map: lam_up -> mean demand up, mu_up -> std dev up? Or cost down? 
        # Standard mapping for queueing is arrival/service rates. For inventory, it's demand distribution.
        # Let's assume:
        # none: base
        # lam_up: mean demand increases (e.g., *1.1)
        # mu_up: standard deviation increases (e.g., *1.1) - representing uncertainty
        # c_up: unit cost increases (e.g., *1.1)
        sigma_d *= 1.1
    elif args.pert == 'c_up':
        c *= 1.1
        
    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)
    
    # Optimal q using inverse normal CDF approximation
    # We can use a simple approximation or just simulate to find best q among integers near theoretical optimum
    # Theoretical Q* = mu + sigma * Z(critical_ratio)
    # Approximation for Z(p):
    def inv_norm(p_val):
        # Rational approximation for inverse normal CDF
        if p_val <= 0: return -10
        if p_val >= 1: return 10
        t = math.sqrt(-2 * math.log(1 - p_val)) if p_val < 0.5 else math.sqrt(-2 * math.log(p_val))
        # Abramowitz and Stegun formula 26.2.23
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)
        return -z if p_val < 0.5 else z

    z_opt = inv_norm(critical_ratio)
    q_theory = mu_d + sigma_d * z_opt
    q_opt_int = int(round(q_theory))
    
    # Simulation to verify and get expected profit
    seeds_used = []
    per_seed_exp_profit = []
    per_seed_q = []
    
    horizon_days = int(args.horizon)
    if horizon_days <= 0: horizon_days = 1
    
    total_profit_sum = 0.0
    count = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # Simulate with optimal integer q
        daily_profits = []
        for _ in range(horizon_days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            sales = min(demand, q_opt_int)
            leftover = q_opt_int - sales
            profit = sales * p - q_opt_int * c + leftover * s
            daily_profits.append(profit)
            
        avg_profit = sum(daily_profits) / len(daily_profits)
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt_int)
        seeds_used.append(seed)
        total_profit_sum += avg_profit
        count += 1
        
    exp_profit = total_profit_sum / count if count > 0 else 0.0
    
    result = {
        "exp_profit": round(exp_profit, 2),
        "q": q_opt_int,
        "runtime_units": horizon_days,
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 2) for x in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
