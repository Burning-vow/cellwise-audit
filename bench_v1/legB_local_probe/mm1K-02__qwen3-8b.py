import json
import sys
import random
import math
from datetime import datetime

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    time_unit = 'minute'
    runtime_units = 'minute'
    win = args.horizon
    pert = args.pert
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    arr = 0
    blk = 0
    dep = 0
    dep_rate = 0
    p_loss = 0
    p_wait = 0
    busy_frac = 0
    L = 0
    W = 0
    for seed in seed_list:
        random.seed(seed)
        if pert == 'lam_up':
            lam = 6 * 60 / 100
        elif pert == 'mu_up':
            mu = 5 / 60
        elif pert == 'c_up':
            c = 4
        else:
            lam = 6 * 60
            mu = 5 / 60
            c = 4
        t = 0
        queue = []
        busy = False
        busy_time = 0
        total_time = 0
        total_wait = 0
        total_L = 0
        total_busy = 0
        total_arr = 0
        total_blk = 0
        total_dep = 0
        total_dep_rate = 0
        total_p_loss = 0
        total_p_wait = 0
        while t < win:
            t += random.expovariate(lam)
            total_arr += 1
            if len(queue) < c:
                queue.append(random.expovariate(mu))
            else:
                total_blk += 1
        total_time = win
        total_wait = sum([q for q in queue])
        total_L = len(queue)
        total_busy = busy_time
        total_busy_frac = total_busy / total_time
        total_p_loss = total_blk / total_arr
        total_p_wait = sum([q for q in queue]) / total_arr
        per_seed_L.append(total_L)
        per_seed_W.append(total_wait / total_arr)
        per_seed_busy_frac.append(total_busy_frac)
        arr += total_arr
        blk += total_blk
        dep += total_dep
        dep_rate += total_dep / total_time
        p_loss += total_p_loss
        p_wait += total_p_wait
        busy_frac += total_busy_frac
        L = total_L
        W = total_wait / total_arr
    p_loss /= seeds_used
    p_wait /= seeds_used
    busy_frac /= seeds_used
    dep_rate /= seeds_used
    result = {
        'L': L,
        'W': W,
        'arr': arr / seeds_used,
        'blk': blk / seeds_used,
        'busy_frac': busy_frac,
        'dep': dep / seeds_used,
        'dep_rate': dep_rate,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win
    }
    print(json.dumps(result))
if __name__ == "__main__":
    main()