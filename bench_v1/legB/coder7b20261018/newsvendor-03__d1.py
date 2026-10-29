import sys
import json
import random
from math import sqrt, exp

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_exp_profit = []
    per_seed_q = []

    for seed in seed_list:
        random.seed(seed)
        if args.pert == 'lam_up':
            demand_mean += 5
        elif args.pert == 'mu_up':
            demand_mean += 1
        elif args.pert == 'c_up':
            cost += 1

        demand_std = 15
        price = 30
        cost = 12
        salvage = 4

        demand = [random.gauss(demand_mean, demand_std) for _ in range(int(args.horizon))]
        demand = [max(0, d) for d in demand]

        q = int(demand_mean + 4 * demand_std)
        exp_profit = sum(max(0, price * q - cost * q - salvage * max(0, q - d)) for d in demand)

        per_seed_exp_profit.append(exp_profit)
        per_seed_q.append(q)

    exp_profit = sum(per_seed_exp_profit) / seeds_used
    runtime_units = args.horizon
    time_unit = 'hour'

    print(json.dumps({
        'exp_profit': exp_profit,
        'q': q,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'per_seed_exp_profit': per_seed_exp_profit,
        'per_seed_q': per_seed_q
    }))

if __name__ == "__main__":
    main()
