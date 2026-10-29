import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    mu_d, sigma_d = 60.0, 25.0
    price, cost, salvage = 20.0, 12.0, 7.0
    
    if a.pert == "lam_up":
        mu_d *= 1.1
    elif a.pert == "mu_up":
        pass # Not applicable directly to demand mean in this context, but structure kept
    elif a.pert == "c_up":
        cost *= 1.1
        
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    
    def norm_ppf(p):
        return math.sqrt(2) * erfinv(2*p - 1)
        
    def erfinv(x):
        # Approximation for inverse error function
        w = -math.log((1-x)*(1+x))
        if w < 5:
            y = math.sqrt(w) - 3
            z = 0.9898093338858801e-01 + 0.6847968999185822e-01*y + 0.2548295920293020e+00*y**2 + 0.1852163127789467e+00*y**3 + 0.1003985923786909e+00*y**4 + 0.4308166932541904e-01*y**5 + 0.1225165918125263e-01*y**6 + 0.1185951445649841e-02*y**7 + 0.1198254663808310e-03*y**8
            return z
        else:
            y = math.sqrt(w) - 3
            z = 0.1003985923786909e+00 + 0.4308166932541904e-01*y + 0.1225165918125263e-01*y**2 + 0.1185951445649841e-02*y**3 + 0.1003985923786909e-03*y**4 + 0.4308166932541904e-04*y**5 + 0.1225165918125263e-05*y**6 + 0.1185951445649841e-06*y**7 + 0.1003985923786909e-07*y**8
            return z

    q_opt = mu_d + sigma_d * norm_ppf(crit_ratio)
    
    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    horizon_days = int(a.horizon) if a.horizon >= 1 else 1000
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        profits = []
        warmup_count = int(horizon_days * 0.25)
        
        for d in range(horizon_days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            if d >= warmup_count:
                profits.append(profit)
                
        exp_p = sum(profits) / len(profits) if profits else 0
        per_seed_exp_profit.append(exp_p)
        per_seed_q.append(q_opt)
        seed_list.append(s)
        
    total_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0
    
    result = {
        "exp_profit": round(total_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
