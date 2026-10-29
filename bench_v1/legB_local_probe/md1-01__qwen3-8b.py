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
        lambda_ = 4.0
        service_time = 6.0
        horizon = args.horizon
        time_unit = 'minute'
        time_scale = 1.0
        if args.pert == 'lam_up':
            lambda_ *= 1.1
        elif args.pert == 'mu_up':
            service_time *= 0.9
        elif args.pert == 'c_up':
            service_time *= 1.1

        events = []
        current_time = 0.0
        busy = False
        busy_time = 0.0
        queue = []
        L = 0.0
        W = 0.0
        arr = 0.0
        blk = 0.0
        dep = 0.0
        dep_rate = 0.0
        p_loss = 0.0
        p_wait = 0.0
        busy_frac = 0.0

        while current_time < horizon:
            if not events:
                next_arrival = random.expovariate(lambda_)
                events.append((current_time + next_arrival, 'arrival'))
            else:
                next_event = min(events)
                current_time = next_event[0]
                event_type = next_event[1]
                if event_type == 'arrival':
                    arr += 1
                    if not busy:
                        busy = True
                        busy_time = current_time + service_time
                        events.append((busy_time, 'departure'))
                    else:
                        queue.append(current_time)
                elif event_type == 'departure':
                    busy = False
                    dep += 1
                    dep_rate = dep / (horizon / 60.0)
                    if queue:
                        wait_time = current_time - queue.pop(0)
                        W += wait_time
                        L += wait_time
                    else:
                        L += 0.0
                    if queue:
                        events.append((current_time, 'arrival'))
                    else:
                        events.append((current_time + random.expovariate(lambda_), 'arrival'))
                else:
                    pass

        L = L / (horizon / 60.0)
        W = W / (horizon / 60.0)
        busy_frac = busy_time / horizon
        p_loss = 0.0
        p_wait = 0.0
        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)

    print(json.dumps({
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
    }))