import sys
import json
import random

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_q = []
    per_seed_cost = []

    for seed in seed_list:
        random.seed(seed)
        demand_rate = 1000 / args.horizon
        order_cost = 200
        holding_cost = 2

        q = (2 * order_cost * demand_rate) ** 0.5 / holding_cost
        cost = (order_cost * demand_rate / q + holding_cost * q / 2) * args.horizon

        per_seed_q.append(q)
        per_seed_cost.append(cost)

    runtime_units = 'hour'
    cost = sum(per_seed_cost) / seeds_used
    q = sum(per_seed_q) / seeds_used

    output = {
        'cost': cost,
        'q': q,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': runtime_units,
        'per_seed_q': per_seed_q,
        'per_seed_cost': per_seed_cost
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
