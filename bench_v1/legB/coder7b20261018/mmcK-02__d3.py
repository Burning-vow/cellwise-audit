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

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    lam = 6
    mu = 1 / 6
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 0.9
    elif args.pert == 'c_up':
        pass

    time_unit = 'minute'
    win = args.horizon
    runtime_units = win / seeds_used

    arr = [0] * seeds_used
    dep = [0] * seeds_used
    blk = [0] * seeds_used
    dep_rate = [0] * seeds_used
    lam_eff = [0] * seeds_used
    p_wait = [0] * seeds_used
    per_seed_L = [0] * seeds_used
    per_seed_W = [0] * seeds_used
    per_seed_busy_frac = [0] * seeds_used
    per_seed_p_loss = [0] * seeds_used
    per_seed_p_wait = [0] * seeds_used

    for seed in seed_list:
        random.seed(seed)
        queue = []
        lanes = [0] * 2
        time = 0
        while time < win:
            if random.random() < lam * runtime_units:
                arr[seed] += 1
                if len(queue) < 4:
                    queue.append(time)
                else:
                    blk[seed] += 1
            if lanes[0] == 0 and queue:
                lanes[0] = queue.pop(0)
                lanes[0] += exponential(mu)
            if lanes[1] == 0 and queue:
                lanes[1] = queue.pop(0)
                lanes[1] += exponential(mu)
            if lanes[0] > 0:
                lanes[0] -= runtime_units
                if lanes[0] <= 0:
                    dep[seed] += 1
                    lanes[0] = 0
            if lanes[1] > 0:
                lanes[1] -= runtime_units
                if lanes[1] <= 0:
                    dep[seed] += 1
                    lanes[1] = 0
            time += runtime_units

        per_seed_L[seed] = arr[seed] / seeds_used
        per_seed_W[seed] = sum(lanes) / seeds_used
        per_seed_busy_frac[seed] = 1 - poisson(lam, win)
        per_seed_p_loss[seed] = blk[seed] / arr[seed]
        per_seed_p_wait[seed] = sum(lanes) / arr[seed]

    busy_frac = 1 - poisson(lam, win)
    p_loss = sum(blk) / sum(arr)
    p_wait = sum(lanes) / sum(arr)
    busy_util = sum(min(2, len(queue)) for queue in lanes) / (2 * win)
    busy_occupied = 1 - busy_frac

    print(json.dumps({
        'L': per_seed_L,
        'W': per_seed_W,
        'busy_frac': per_seed_busy_frac,
        'p_loss': per_seed_p_loss,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
