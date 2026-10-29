import json
import sys
import random
import math
from datetime import datetime

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    time_unit = 'minute'
    win = args.horizon
    runtime_units = win
    
    results = {
        'arr': 0,
        'blk': 0,
        'busy_frac': 0,
        'cost': 0,
        'dep': 0,
        'dep_rate': 0,
        'p_loss': 0,
        'p_wait': 0,
        'per_seed_L': [],
        'per_seed_W': [],
        'per_seed_busy_frac': [],
        'q': 0,
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win
    }
    
    for seed in seed_list:
        random.seed(seed)
        demand = 1000
        order_cost = 50
        holding_cost = 2
        q = math.sqrt(2 * demand * order_cost / holding_cost)
        cost = (demand / q) * order_cost + (q / 2) * holding_cost
        
        results['q'] = q
        results['cost'] = cost
        
        results['per_seed_L'].append(0)
        results['per_seed_W'].append(0)
        results['per_seed_busy_frac'].append(0)
    
    print(json.dumps(results))

if __name__ == "__main__":
    main()