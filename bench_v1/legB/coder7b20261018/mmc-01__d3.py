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
        mu = 1 / 12
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 1.1

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

        queue = []
        servers = [0, 0]
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while total_time < win:
            if next_arrival < next_departure:
                total_time = next_arrival
                if servers[0] == 0 and servers[1] == 0:
                    service_time = random.expovariate(mu)
                    servers[0] = service_time
                    next_departure = total_time + service_time
                elif servers[0] == 0:
                    service_time = random.expovariate(mu)
                    servers[0] = service_time
                    next_departure = total_time + service_time
                elif servers[1] == 0:
                    service_time = random.expovariate(mu)
                    servers[1] = service_time
                    next_departure = total_time + service_time
                else:
                    queue.append(total_time)
                next_arrival = total_time + random.expovariate(lam)
            else:
                total_time = next_departure
                if queue:
                    arrival_time = queue.pop(0)
                    service_time = random.expovariate(mu)
                    servers[0] = service_time
                    next_departure = total_time + service_time
                    total_wait_time += total_time - arrival_time
                    total_service_time += service_time
                else:
                    servers[0] = 0
                    servers[1] = 0
                    next_departure = float('inf')

            if servers[0] > 0:
                servers[0] -= runtime_units
                if servers[0] <= 0:
                    servers[0] = 0
            if servers[1] > 0:
                servers[1] -= runtime_units
                if servers[1] <= 0:
                    servers[1] = 0

            arr += 1
            dep += 1
            if queue:
                p_wait += 1
            if servers[0] > 0 or servers[1] > 0:
                busy_util += runtime_units
                busy_occupied += runtime_units
            else:
                busy_util += 0
                busy_occupied += 0

        per_seed_L.append(arr / win)
        per_seed_W.append((total_wait_time + total_service_time) / arr)
        per_seed_busy_frac.append(busy_util / (N * win))
        per_seed_p_loss.append(blk / arr)
        per_seed_p_wait.append(p_wait / arr)

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

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
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
