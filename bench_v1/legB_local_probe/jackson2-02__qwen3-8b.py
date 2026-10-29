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

    time_unit = 'minute'
    runtime_units = 'minute'
    win = args.horizon
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []

    for seed in seed_list:
        random.seed(seed)
        lambda_1 = 4 / 60
        lambda_2 = 4 / 60
        mu_1 = 1 / 7.5
        mu_2 = 1 / 5
        t = 0
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        busy_time1 = 0
        busy_time2 = 0
        arr = 0
        dep = 0
        blk = 0
        p_loss = 0
        p_wait = 0
        L = 0
        W = 0
        busy_frac = 0
        dep_rate = 0
        time_start = time.time()
        while t < win:
            t += 1 / lambda_1
            arr += 1
            if not busy1:
                service_time = -math.log(random.random()) / mu_1
                busy1 = True
                busy_time1 = service_time
                queue1.append(service_time)
            else:
                queue1[0] -= 1 / lambda_1
                if queue1[0] <= 0:
                    queue1.pop(0)
                    busy_time1 -= 1 / lambda_1
                    if not queue1:
                        busy1 = False
                    else:
                        queue1[0] += 1 / lambda_1
            if not busy2:
                service_time = -math.log(random.random()) / mu_2
                busy2 = True
                busy_time2 = service_time
                queue2.append(service_time)
            else:
                queue2[0] -= 1 / lambda_1
                if queue2[0] <= 0:
                    queue2.pop(0)
                    busy_time2 -= 1 / lambda_1
                    if not queue2:
                        busy2 = False
                    else:
                        queue2[0] += 1 / lambda_1
            if not busy1 and not busy2:
                dep += 1
                dep_rate += 1 / win
            if not busy1:
                p_loss += 1
            if queue1:
                p_wait += 1
            if busy1:
                busy_frac += 1
            if busy2:
                busy_frac += 1
            L += len(queue1) + len(queue2)
            W += (len(queue1) + len(queue2)) * 1
        L /= win
        W /= win
        busy_frac /= win
        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
    result = {
        "L": L,
        "W": W,
        "arr": arr,
        "blk": blk,
        "busy_frac": busy_frac,
        "dep": dep,
        "dep_rate": dep_rate,
        "p_loss": p_loss / win,
        "p_wait": p_wait / win,
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