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
    L = 0
    W = 0
    arr = 0
    blk = 0
    dep = 0
    dep_rate = 0
    p_loss = 0
    p_wait = 0
    busy_frac = 0

    for seed in seed_list:
        random.seed(seed)
        lambda_1 = 4 / 60
        mu_1 = 1 / 7.5
        mu_2 = 1 / 6
        t = 0
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        busy_time1 = 0
        busy_time2 = 0
        events = []
        events.append(('arrival', 0))
        while t < win:
            if not events:
                break
            event = events.pop(0)
            if event[0] == 'arrival':
                arr += 1
                if not queue1 and not busy1:
                    service_time = -math.log(random.random()) / mu_1
                    t += service_time
                    busy1 = True
                    busy_time1 += service_time
                    events.append(('departure', t))
                else:
                    queue1.append(t)
            elif event[0] == 'departure':
                if queue1:
                    t = queue1.pop(0)
                    events.append(('arrival', t))
                else:
                    t += 1
                if not queue2 and not busy2:
                    service_time = -math.log(random.random()) / mu_2
                    t += service_time
                    busy2 = True
                    busy_time2 += service_time
                    events.append(('departure', t))
                else:
                    queue2.append(t)
            elif event[0] == 'end':
                t = event[1]
                busy1 = False
                busy2 = False
                busy_time1 = 0
                busy_time2 = 0
                if queue1:
                    t = queue1.pop(0)
                    events.append(('arrival', t))
                elif queue2:
                    t = queue2.pop(0)
                    events.append(('arrival', t))
                else:
                    t += 1
        if queue1:
            p_loss += len(queue1) / (len(queue1) + len(queue2))
        if queue2:
            p_wait += len(queue2) / (len(queue1) + len(queue2))
        if busy1:
            busy_frac += busy_time1 / win
        if busy2:
            busy_frac += busy_time2 / win
        if queue1:
            L += len(queue1) / win
        if queue2:
            L += len(queue2) / win
        if queue1:
            W += sum(queue1) / len(queue1)
        if queue2:
            W += sum(queue2) / len(queue2)
        per_seed_L.append(L / seeds_used)
        per_seed_W.append(W / seeds_used)
        per_seed_busy_frac.append(busy_frac / seeds_used)
        dep += len(queue1) + len(queue2)
        dep_rate += dep / win
        blk += len(queue1) + len(queue2)
    result = {
        'L': L,
        'W': W,
        'arr': arr,
        'blk': blk,
        'busy_frac': busy_frac,
        'dep': dep,
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