import json
import sys
import random
import math
import time

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
    arr = []
    blk = []
    dep = []
    dep_rate = []
    p_loss = []
    p_wait = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    L = 0
    W = 0
    busy_frac = 0
    for seed in seed_list:
        random.seed(seed)
        lambda_ = 4 / 60
        mu1 = 1 / 6
        mu2 = 1 / 6
        if args.pert == 'lam_up':
            lambda_ = lambda_ * 1.1
        elif args.pert == 'mu_up':
            mu1 = mu1 * 1.1
            mu2 = mu2 * 1.1
        elif args.pert == 'c_up':
            mu1 = mu1 * 1.1
            mu2 = mu2 * 1.1
        t = 0
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        start_time = time.time()
        while t < win:
            t += 1 / 60
            if random.random() < lambda_:
                queue1.append(t)
            if not busy1 and queue1:
                busy1 = True
                service_time = -math.log(random.random()) / mu1
                finish_time = t + service_time
                queue2.append(finish_time)
            if not busy2 and queue2:
                busy2 = True
                service_time = -math.log(random.random()) / mu2
                finish_time = queue2.pop(0) + service_time
                dep.append(finish_time)
            if not busy1 and not queue1:
                busy1 = False
            if not busy2 and not queue2:
                busy2 = False
        busy_frac += (busy1 or busy2) * win
        arr.append(len(queue1))
        blk.append(len(queue2))
        dep.append(len(dep))
        dep_rate.append(len(dep) / win)
        p_loss.append(0)
        p_wait.append(0)
        per_seed_L.append(len(queue1) + len(queue2))
        per_seed_W.append(0)
        per_seed_busy_frac.append((busy1 or busy2) * win)
    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac /= seeds_used
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