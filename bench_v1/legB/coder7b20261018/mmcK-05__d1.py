import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def exponential(mu):
    return -1 / mu * log(random.random())

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1)
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
        lam = 6
        mu = 1 / (12 / 60)
        c = 3
        Q = 4
        W = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        time_unit = 'minute'
        win = args.horizon
        start_time = 0
        end_time = win
        next_arrival = exponential(lam)
        next_departure = float('inf')
        queue = []
        busy = [False] * c

        while start_time < end_time:
            if next_arrival < next_departure:
                current_time = next_arrival
                next_arrival = exponential(lam)
                if len(queue) < Q:
                    queue.append(current_time)
                    arr += 1
                    if len(queue) == 1:
                        next_departure = current_time + exponential(mu)
                    busy_frac += 1
                    p_wait += len(queue) - 1
                else:
                    p_loss += 1
            else:
                current_time = next_departure
                next_departure = float('inf')
                if queue:
                    dep += 1
                    queue.pop(0)
                    if queue:
                        next_departure = current_time + exponential(mu)
                    busy_frac += 1
                else:
                    busy_frac -= 1

            if busy_frac > 0:
                busy_util += 1
                busy_occupied += 1

            start_time = current_time

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac / win)
        per_seed_p_loss.append(p_loss / arr)
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
        'p_loss': p_loss,
        'runtime_units': time_unit,
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
