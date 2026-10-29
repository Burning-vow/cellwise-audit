import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    price = 30.0
    cost = 12.0
    salvage = 7.0

    if args.pert == "lam_up":
        pass 
    elif args.pert == "mu_up":
        pass
    elif args.pert == "c_up":
        pass
    
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)
    
    from statistics import NormalDist
    nd = NormalDist(mu_d, sigma_d)
    q_optimal = nd.inv_cdf(critical_ratio)
    q_int = int(round(q_optimal))
    
    def expected_profit(q):
        total_profit = 0.0
        n_samples = 100000
        rng = random.Random(999)
        for _ in range(n_samples):
            d = rng.gauss(mu_d, sigma_d)
            sold = min(d, q)
            leftover = max(0, q - d)
            profit = price * sold - cost * q + salvage * leftover
            total_profit += profit
        return total_profit / n_samples

    exp_profit_val = expected_profit(q_int)
    
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    horizon_days = int(args.horizon)
    if horizon_days <= 0:
        horizon_days = 1
        
    for i in range(args.seeds):
        s = args.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        
        best_q = 0
        best_p = float('-inf')
        
        search_range = list(range(max(0, int(mu_d - 3*sigma_d)), int(mu_d + 3*sigma_d) + 1))
        
        sample_size = max(100, horizon_days // len(search_range) if len(search_range)>0 else 100)
        
        profits = {}
        for q in search_range:
            p_sum = 0.0
            for _ in range(sample_size):
                d = rng.gauss(mu_d, sigma_d)
                sold = min(d, q)
                leftover = max(0, q - d)
                profit = price * sold - cost * q + salvage * leftover
                p_sum += profit
            avg_p = p_sum / sample_size
            profits[q] = avg_p
            
        best_q = max(profits, key=profits.get)
        best_p = profits[best_q]
        
        per_seed_q.append(best_q)
        per_seed_exp_profit.append(best_p)

    result = {
        "exp_profit": round(exp_profit_val, 4),
        "q": q_int,
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
