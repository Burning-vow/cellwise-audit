import json
import sys
import random
import math
from datetime import datetime

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    time_unit = 'minute'
    win = args.horizon
    arr = 0
    blk = 0
    dep = 0
    dep_rate = 0
    busy_frac = 0
    exp_profit = 0
    p_loss = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    
    for seed in seed_list:
        random.seed(seed)
        demand_mean = 60
        demand_std = 25
        price = 20
        cost = 12
        salvage = 7
        q = 0
        for _ in range(1000):
            demand = int(random.gauss(demand_mean, demand_std))
            sold = min(demand, q)
            unsold = q - sold
            profit = sold * price + unsold * salvage - q * cost
            exp_profit += profit
        exp_profit /= 1000
        
        for _ in range(1000):
            demand = int(random.gauss(demand_mean, demand_std))
            if demand > q:
                p_loss += 1
            if demand < q:
                p_wait += 1
        p_loss /= 1000
        p_wait /= 1000
        
        for _ in range(1000):
            demand = int(random.gauss(demand_mean, demand_std))
            if demand > q:
                arr += 1
            if demand < q:
                dep += 1
        arr /= 1000
        dep /= 1000
        dep_rate = dep / win
        
        for _ in range(1000):
            demand = int(random.gauss(demand_mean, demand_std))
            if demand > q:
                blk += 1
            if demand < q:
                blk += 1
        blk /= 1000
        busy_frac = blk / win
        
        per_seed_L.append(arr)
        per_seed_W.append(dep)
        per_seed_busy_frac.append(busy_frac)
    
    result = {
        "arr": arr,
        "blk": blk,
        "busy_frac": busy_frac,
        "dep": dep,
        "dep_rate": dep_rate,
        "exp_profit": exp_profit,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "q": q,
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()