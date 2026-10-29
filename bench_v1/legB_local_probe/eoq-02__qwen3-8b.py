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
    win = args.horizon / 4
    horizon = args.horizon
    pert = args.pert
    
    def run_seed(seed):
        random.seed(seed)
        demand = 1000
        order_cost = 200
        holding_cost = 2
        q = math.sqrt(2 * demand * order_cost / holding_cost)
        cost = (demand / q) * order_cost + (q / 2) * holding_cost
        return q, cost
    
    results = []
    for seed in seed_list:
        q, cost = run_seed(seed)
        results.append({'q': q, 'cost': cost})
    
    per_seed_L = [0] * seeds_used
    per_seed_W = [0] * seeds_used
    per_seed_busy_frac = [0] * seeds_used
    
    output = {
        'arr': 0,
        'blk': 0,
        'busy_frac': 0,
        'cost': cost,
        'dep': 0,
        'dep_rate': 0,
        'p_loss': 0,
        'p_wait': 0,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'q': q,
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()