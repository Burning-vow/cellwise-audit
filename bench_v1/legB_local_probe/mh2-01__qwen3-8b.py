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
    arr = 0
    blk = 0
    dep = 0
    dep_rate = 0
    p_loss = 0
    p_wait = 0
    busy_frac = 0
    L = 0
    W = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    for seed in seed_list:
        random.seed(seed)
        if args.pert == 'lam_up':
            lam = 3 * 1.1
        elif args.pert == 'mu_up':
            mu = 6 * 1.1
        elif args.pert == 'c_up':
            c = 1.5 * 1.1
        else:
            lam = 3
            mu = 6
            c = 1.5
        t = 0
        queue = []
        busy = False
        busy_time = 0
        total_time = 0
        total_L = 0
        total_W = 0
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
            if not busy:
                service_time = 0
                if random.random() < 0.5:
                    service_time = random.expovariate(1 / mu)
                else:
                    service_time = random.expovariate(1 / (mu * c))
                service_time = service_time * 60
                busy = True
                busy_time = t + service_time
                queue.append(service_time)
            else:
                queue.append(0)
            if len(queue) > 0:
                if queue[0] <= t:
                    total_dep += 1
                    total_dep_rate += 1 / win
                    total_blk += 1
                    queue.pop(0)
                    total_L += 1
                    total_W += t - (t - queue[0])
                    total_busy += 1
                    busy = False
                    if len(queue) > 0:
                        service_time = 0
                        if random.random() < 0.5:
                            service_time = random.expovariate(1 / mu)
                        else:
                            service_time = random.expovariate(1 / (mu * c))
                        service_time = service_time * 60
                        busy = True
                        busy_time = t + service_time
                        queue.append(service_time)
                    else:
                        busy = False
                else:
                    total_L += 1
                    total_W += t - (t - queue[0])
                    total_busy += 1
        total_L /= win
        total_W /= win
        total_busy /= win
        total_dep_rate /= win
        total_p_loss = total_dep / total_arr
        total_p_wait = total_blk / total_arr
        per_seed_L.append(total_L)
        per_seed_W.append(total_W)
        per_seed_busy_frac.append(total_busy)
    L = total_L
    W = total_W
    busy_frac = total_busy
    dep_rate = total_dep_rate
    p_loss = total_p_loss
    p_wait = total_p_wait
    arr = total_arr
    blk = total_blk
    dep = total_dep
    result = {
        "L": L,
        "W": W,
        "arr": arr,
        "blk": blk,
        "busy_frac": busy_frac,
        "dep": dep,
        "dep_rate": dep_rate,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()