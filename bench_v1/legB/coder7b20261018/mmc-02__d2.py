import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seeds:
        random.seed(seed)
        lam = 8 / 60
        mu = 1 / 10
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 2

        N = 2
        time_unit = 'minute'
        win = args.horizon
        runtime_units = win / args.seeds

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        total_time = 0
        total_wait_time = 0
        total_service_time = 0
        total_busy_time = 0
        total_arrival_time = 0
        total_departure_time = 0
        total_block_time = 0
        total_busy_fraction = 0
        total_p_loss = 0
        total_p_wait = 0

        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        queue = []
        busy = [False, False]

        while total_time < win:
            if next_arrival < next_departure:
                total_time += next_arrival
                next_arrival = float('inf')
                if queue:
                    customer = queue.pop(0)
                    service_time = random.expovariate(mu)
                    next_departure = total_time + service_time
                    busy[customer % N] = True
                    total_service_time += service_time
                    total_busy_time += service_time
                    total_wait_time += total_time - customer['arrival_time']
                else:
                    next_departure = float('inf')
                arr += 1
                total_arrival_time += total_time
            else:
                total_time += next_departure - total_time
                next_departure = float('inf')
                customer = queue.pop(0)
                dep += 1
                total_departure_time += total_time
                busy[customer % N] = False
                total_busy_time -= customer['service_time']
                if queue:
                    next_departure = total_time + queue[0]['service_time']
                else:
                    next_departure = float('inf')

            if total_time < win:
                next_arrival = total_time + random.expovariate(lam)
                if next_arrival < win:
                    queue.append({'arrival_time': total_time, 'service_time': random.expovariate(mu)})
                    if len(queue) == 1:
                        next_departure = total_time + queue[0]['service_time']
                    busy_fraction = sum(busy) / N
                    total_busy_fraction += busy_fraction
                    total_p_loss += 0
                    total_p_wait += 0
                else:
                    next_arrival = float('inf')

        per_seed_L.append(arr / args.seeds)
        per_seed_W.append(total_wait_time / total_arrival_time)
        per_seed_busy_frac.append(total_busy_fraction / win)
        per_seed_p_loss.append(total_p_loss / win)
        per_seed_p_wait.append(total_p_wait / win)

    L = sum(per_seed_L) / args.seeds
    W = sum(per_seed_W) / args.seeds
    busy_frac = sum(per_seed_busy_frac) / args.seeds
    p_loss = sum(per_seed_p_loss) / args.seeds
    p_wait = sum(per_seed_p_wait) / args.seeds

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': runtime_units,
        'seed_list': seeds,
        'seeds_used': args.seeds,
        'time_unit': time_unit,
        'win': win,
        'arr': arr / args.seeds,
        'blk': blk / args.seeds,
        'busy_util': busy_util / args.seeds,
        'dep': dep / args.seeds,
        'dep_rate': dep / win,
        'lam_eff': lam * N,
        'p_loss': p_loss,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
