import sys
import json
import random
from math import exp, sqrt

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
            demand_mean = 60 * 1.1
        elif args.pert == 'mu_up':
            demand_mean = 60 * 0.9
        elif args.pert == 'c_up':
            cost = 12 * 1.1
        else:
            demand_mean = 60
            cost = 12

        demand_std = 25
        price = 30
        salvage = 7

        total_profit = 0
        for _ in range(int(args.horizon)):
            demand = random.gauss(demand_mean, demand_std)
            demand = max(0, demand)
            q = int(demand_mean)
            profit = q * price - q * cost
            if demand < q:
                profit += (q - demand) * salvage
            total_profit += profit

        per_seed_exp_profit.append(total_profit / args.horizon)
        per_seed_q.append(q)

    exp_profit = sum(per_seed_exp_profit) / seeds_used
    runtime_units = 'hour'
    time_unit = 'hour'

    print(json.dumps({
        'exp_profit': exp_profit,
        'q': per_seed_q[0],
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'per_seed_exp_profit': per_seed_exp_profit,
        'per_seed_q': per_seed_q
    }))

if __name__ == "__main__":
    main()
