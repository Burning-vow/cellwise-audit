import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    mu_d, sigma_d = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    
    if a.pert == 'lam_up': mu_d *= 1.1
    elif a.pert == 'mu_up': sigma_d *= 1.1
    elif a.pert == 'c_up': cost *= 1.1
    
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    
    from statistics import NormalDist
    nd = NormalDist(mu_d, sigma_d)
    q_opt = nd.inv_cdf(crit_ratio)
    q_int = int(round(q_opt))
    
    per_seed_profit = []
    per_seed_q = []
    seeds_used = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        total_profit = 0.0
        days = int(a.horizon)
        warmup_days = int(days * 0.25)
        
        daily_profits = []
        for d in range(days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            order_qty = q_int
            sold = min(demand, order_qty)
            leftover = order_qty - sold
            profit = sold * price + leftover * salvage - order_qty * cost
            daily_profits.append(profit)
            
        valid_profits = daily_profits[warmup_days:]
        if valid_profits:
            avg_p = sum(valid_profits) / len(valid_profits)
        else:
            avg_p = sum(daily_profits) / len(daily_profits) if daily_profits else 0.0
            
        per_seed_profit.append(avg_p)
        per_seed_q.append(q_int)
        seeds_used.append(seed)
        
    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    
    result = {
        "exp_profit": round(exp_profit, 4),
        "q": q_int,
        "runtime_units": a.horizon,
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_profit],
        "per_seed_q": per_seed_q
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
