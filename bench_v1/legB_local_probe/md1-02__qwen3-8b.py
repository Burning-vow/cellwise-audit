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
        service_time = 5.0
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
        next_arrival = -math.log(1.0 - random.random()) / lambda_
        busy = False
        start_time = 0.0
        busy_time = 0.0
        total_time = 0.0
        total_L = 0.0
        total_W = 0.0
        total_arr = 0.0
        total_blk = 0.0
        total_dep = 0.0
        total_dep_rate = 0.0
        total_p_loss = 0.0
        total_p_wait = 0.0
        total_busy_frac = 0.0
        time_window = 0.0
        time_window_start = 0.0
        time_window_end = 0.0
        time_window_count = 0
        time_window_total = 0.0
        time_window_L = 0.0
        time_window_W = 0.0
        time_window_arr = 0.0
        time_window_blk = 0.0
        time_window_dep = 0.0
        time_window_dep_rate = 0.0
        time_window_p_loss = 0.0
        time_window_p_wait = 0.0
        time_window_busy_frac = 0.0

        while total_time < horizon:
            if not events:
                next_event = next_arrival
                events.append(('arrival', next_event))
            else:
                next_event = min(events[0][1], next_event)
            if next_event > horizon:
                break
            event_type, event_time = events.pop(0)
            if event_type == 'arrival':
                total_arr += 1
                if not busy:
                    busy = True
                    start_time = event_time
                    service_end = event_time + service_time
                    events.append(('service_end', service_end))
                else:
                    total_p_loss += 1
                    total_p_wait += 1
                    total_L += 1
                    total_W += event_time - start_time
                    total_time = event_time
                    events.append(('arrival', event_time))
            elif event_type == 'service_end':
                total_dep += 1
                total_dep_rate += 1.0 / (event_time - start_time)
                total_L -= 1
                total_W += event_time - start_time
                total_time = event_time
                busy = False
                next_arrival = event_time + (-math.log(1.0 - random.random())) / lambda_
                events.append(('arrival', next_arrival))
            total_time = event_time
            if total_time >= time_window_start + win:
                time_window_count += 1
                time_window_total += total_time - time_window_start
                time_window_L += total_L
                time_window_W += total_W
                time_window_arr += total_arr
                time_window_blk += total_blk
                time_window_dep += total_dep
                time_window_dep_rate += total_dep_rate
                time_window_p_loss += total_p_loss
                time_window_p_wait += total_p_wait
                time_window_busy_frac += total_busy_frac
                time_window_start = total_time
                time_window_end = total_time
                time_window_count = 0
                time_window_total = 0.0
                time_window_L = 0.0
                time_window_W = 0.0
                time_window_arr = 0.0
                time_window_blk = 0.0
                time_window_dep = 0.0
                time_window_dep_rate = 0.0
                time_window_p_loss = 0.0
                time_window_p_wait = 0.0
                time_window_busy_frac = 0.0

        time_window_L /= time_window_count
        time_window_W /= time_window_count
        time_window_arr /= time_window_count
        time_window_blk /= time_window_count
        time_window_dep /= time_window_count
        time_window_dep_rate /= time_window_count
        time_window_p_loss /= time_window_count
        time_window_p_wait /= time_window_count
        time_window_busy_frac /= time_window_count

        per_seed_L.append(time_window_L)
        per_seed_W.append(time_window_W)
        per_seed_busy_frac.append(time_window_busy_frac)

    L = time_window_L
    W = time_window_W
    arr = time_window_arr
    blk = time_window_blk
    busy_frac = time_window_busy_frac
    dep = time_window_dep
    dep_rate = time_window_dep_rate
    p_loss = time_window_p_loss
    p_wait = time_window_p_wait
    per_seed_L = per_seed_L
    per_seed_W = per_seed_W
    per_seed_busy_frac = per_seed_busy_frac
    runtime_units = time_unit
    seed_list = seed_list
    seeds_used = seeds_used
    time_unit = time_unit
    win = win

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
    }, indent=2))