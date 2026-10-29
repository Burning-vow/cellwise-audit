import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
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

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        pass # Not applicable directly to newsvendor params in same way, but keep structure
    elif args.pert == "c_up":
        c *= 1.1
    
    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)
    
    z_opt = 0.0
    for i in range(100):
        mid = (i * 10.0) / 99.0
        if abs(mid - critical_ratio) < 1e-9:
            z_opt = (i * 10.0) / 99.0
            break
        if mid > critical_ratio:
            prev_mid = ((i-1)*10.0)/99.0
            z_opt = prev_mid + (critical_ratio - prev_mid) * (z_opt - prev_mid) / (mid - prev_mid) if i>0 else 0.0
            break
            
    # Better approximation for inverse normal CDF using standard library only
    # Using a simple binary search or approximation since scipy is not allowed
    def norm_cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    low, high = -10.0, 10.0
    for _ in range(50):
        mid = (low + high) / 2.0
        if norm_cdf(mid) < critical_ratio:
            low = mid
        else:
            high = mid
    z_opt = (low + high) / 2.0
    
    q_opt = mu_d + z_opt * sigma_d
    
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    num_days = int(args.horizon)
    if num_days <= 0:
        num_days = 1
        
    for i in range(args.seeds):
        current_seed = args.seed_start + i
        rng = random.Random(current_seed)
        
        total_profit = 0.0
        warmup_days = int(num_days * 0.25)
        
        for d in range(num_days):
            demand = rng.gauss(mu_d, sigma_d)
            if demand < 0:
                demand = 0
                
            sales = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            profit = p * sales + s * leftover - c * q_opt
            
            if d >= warmup_days:
                total_profit += profit
                
        avg_profit = total_profit / (num_days - warmup_days) if (num_days - warmup_days) > 0 else 0.0
        
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(current_seed)
        
    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": overall_exp_profit,
        "q": q_opt,
        "runtime_units": num_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
