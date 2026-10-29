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
    lam = 8 / 60
    mu = 1 / 12
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
    elif args.pert == 'c_up':
        pass

    time_unit = 'minute'
    win = args.horizon
    runtime_units = win

    arr = 0
    dep = 0
    blk = 0
    dep_rate = 0
    lam_eff = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        queue = []
        lanes = [0] * 3
        busy_time = 0
        total_time = 0
        loss_count = 0
        wait_count = 0

        for t in range(int(win * 60)):
            if random.random() < lam:
                queue.append(t)
                wait_count += 1

            if queue and lanes.count(0) > 0:
                car = queue.pop(0)
                lane = lanes.index(0)
                service_time = exponential(mu)
                lanes[lane] = service_time
                busy_time += service_time
                dep += 1

            lanes = [max(0, t - dt) for t, dt in zip(lanes, lanes)]

            if lanes.count(0) < 3 and queue:
                loss_count += 1

            total_time += 1

        arr += len(queue)
        dep_rate += dep / win
        lam_eff += lam * win / total_time
        p_wait += wait_count / total_time
        per_seed_L.append(len(queue))
        per_seed_W.append(busy_time / win)
        per_seed_busy_frac.append(1 - exp(-lam * win))
        per_seed_p_loss.append(loss_count / total_time)
        per_seed_p_wait.append(wait_count / total_time)

    busy_frac = 1 - exp(-lam * win)
    p_loss = sum(per_seed_p_loss) / seeds_used
    W = sum(per_seed_W) / seeds_used
    L = sum(per_seed_L) / seeds_used
    busy_util = busy_time / (win * 3)
    busy_occupied = 1 - exp(-lam * win)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
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
