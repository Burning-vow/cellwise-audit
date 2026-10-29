import sys
import json
import random
import math

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    per_seed_exp_profit = []
    per_seed_q = []

    for seed in seeds:
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
            q = math.ceil(demand_mean)
            profit = (q - demand) * price + (demand - q) * salvage - q * cost
            total_profit += profit

        per_seed_exp_profit.append(total_profit / args.horizon)
        per_seed_q.append(q)

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit)
    q = sum(per_seed_q) / len(per_seed_q)
    runtime_units = 'hour'
    seeds_used = len(per_seed_exp_profit)
    seed_list = seeds

    print(json.dumps({
        'exp_profit': exp_profit,
        'q': q,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': runtime_units,
        'per_seed_exp_profit': per_seed_exp_profit,
        'per_seed_q': per_seed_q
    }))

if __name__ == "__main__":
    main()
