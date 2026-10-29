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
    exp_profit = 0
    p_loss = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    q = 0
    runtime_units = 0
    for seed in seed_list:
        random.seed(seed)
        demand_mean = 60
        demand_std = 15
        price = 20
        cost = 12
        salvage = 7
        if args.pert == 'lam_up':
            demand_mean += 10
        elif args.pert == 'mu_up':
            demand_std += 5
        elif args.pert == 'c_up':
            price += 5
        demand = max(0, int(random.gauss(demand_mean, demand_std)))
        q = round(demand_mean + 1.645 * demand_std)
        profit = 0
        if demand <= q:
            profit += (price - cost) * demand
        else:
            profit += (price - cost) * q
            profit += (salvage - cost) * (demand - q)
        exp_profit += profit
        p_loss += 1 if demand > q else 0
        p_wait += 0
        per_seed_L.append(0)
        per_seed_W.append(0)
        per_seed_busy_frac.append(0)
    exp_profit /= seeds_used
    p_loss /= seeds_used
    p_wait /= seeds_used
    per_seed_L = [0]*seeds_used
    per_seed_W = [0]*seeds_used
    per_seed_busy_frac = [0]*seeds_used
    runtime_units = win
    result = {
        "arr": arr,
        "blk": blk,
        "busy_frac": 0,
        "dep": dep,
        "dep_rate": dep_rate,
        "exp_profit": exp_profit,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "q": q,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win
    }
    print(json.dumps(result))
if __name__ == "__main__":
    main()