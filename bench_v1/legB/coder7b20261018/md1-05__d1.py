import sys
import json
import random
from math import exp, factorial

def poisson(lam, k):
    return (lam ** k) * exp(-lam) / factorial(k)

def main():
    args = sys.argv[1:]
    seeds = int(next((arg.split('=')[1] for arg in args if arg.startswith('--seeds=')), 100))
    horizon = float(next((arg.split('=')[1] for arg in args if arg.startswith('--horizon=')), 1000))
    seed_start = int(next((arg.split('=')[1] for arg in args if arg.startswith('--seed-start=')), 0))
    perturbation = next((arg.split('=')[1] for arg in args if arg.startswith('--pert=')), 'none')

    if perturbation == 'lam_up':
        lam = 8 * 1.1
    elif perturbation == 'mu_up':
        lam = 8
        mu = 6 * 1.1
    elif perturbation == 'c_up':
        lam = 8
        mu = 6
        c = 2
    else:
        lam = 8
        mu = 6
        c = 1

    time_unit = 'hour'
    win = horizon
    runtime_units = win

    seed_list = list(range(seed_start, seed_start + seeds))
    seeds_used = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        queue = []
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = 0
        time = 0

        while time < horizon:
            if next_arrival < next_departure:
                time = next_arrival
                arr += 1
                if busy < c:
                    busy += 1
                    next_departure = time + 6
                    busy_util += 6
                    busy_occupied += 1
                else:
                    blk += 1
            else:
                time = next_departure
                dep += 1
                busy -= 1
                if queue:
                    next_arrival = time + random.expovariate(lam)
                    busy += 1
                    next_departure = time + 6
                    busy_util += 6
                    busy_occupied += 1
                else:
                    next_arrival = float('inf')

            if time >= horizon / 4:
                p_loss = blk / (arr + dep + blk)
                p_wait = sum(max(0, time - a) for a in queue) / (arr + dep + blk)
                per_seed_L.append(arr / (arr + dep + blk))
                per_seed_W.append(busy_util / (arr + dep + blk))
                per_seed_busy_frac.append(busy_occupied / (arr + dep + blk))
                per_seed_p_loss.append(p_loss)
                per_seed_p_wait.append(p_wait)
                seeds_used += 1

        if seeds_used == seeds:
            break

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep / horizon,
        'lam_eff': lam,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
