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
        order_cost = 50
        holding_cost = 2

        q = (2 * demand_rate * order_cost / holding_cost) ** 0.5
        cost = (demand_rate * order_cost / q) + (q * holding_cost / 2)

        per_seed_q.append(q)
        per_seed_cost.append(cost)

    cost = sum(per_seed_cost) / seeds_used
    q = sum(per_seed_q) / seeds_used

    runtime_units = 'hour'
    per_seed_q = [str(q) for q in per_seed_q]
    per_seed_cost = [str(cost) for cost in per_seed_cost]

    print(json.dumps({
        'cost': cost,
        'q': q,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': runtime_units,
        'per_seed_q': per_seed_q,
        'per_seed_cost': per_seed_cost
    }))

if __name__ == "__main__":
    main()
