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
    runtime_units = 'hour'
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
    start_time = time.time()

    for seed in seed_list:
        random.seed(seed)
        if args.pert == 'lam_up':
            lam = 4.5
        elif args.pert == 'mu_up':
            mu = 5.5
        elif args.pert == 'c_up':
            c = 0.9
        else:
            lam = 4
            mu = 5
            c = 1

        event_queue = []
        server_busy = False
        server_start_time = 0
        current_time = 0
        customers = 0
        total_time = 0
        total_L = 0
        total_W = 0
        busy_time = 0
        total_arr = 0
        total_blk = 0
        total_dep = 0
        total_dep_rate = 0
        total_p_loss = 0
        total_p_wait = 0
        total_busy_frac = 0
        time_window = 0
        time_window_start = 0
        time_window_end = 0
        time_window_count = 0

        while current_time < args.horizon:
            if event_queue:
                next_event = event_queue[0]
                if next_event[0] == 'arrival':
                    event_time = next_event[1]
                    service_time = -math.log(random.random()) / mu
                    event_queue.pop(0)
                    customers += 1
                    total_arr += 1
                    if server_busy:
                        event_queue.append(('departure', event_time + service_time))
                    else:
                        server_busy = True
                        server_start_time = event_time
                        event_queue.append(('departure', event_time + service_time))
                    current_time = event_time
                elif next_event[0] == 'departure':
                    event_time = next_event[1]
                    event_queue.pop(0)
                    customers -= 1
                    total_dep += 1
                    total_dep_rate += 1 / (args.horizon / 60)
                    if customers == 0:
                        server_busy = False
                    else:
                        service_time = -math.log(random.random()) / mu
                        event_queue.append(('departure', event_time + service_time))
                    current_time = event_time
            else:
                if customers == 0:
                    event_time = current_time + 1 / (lam * 60)
                else:
                    event_time = current_time + 1 / (lam * 60)
                event_queue.append(('arrival', event_time))
                current_time = event_time

            if current_time >= time_window_start and current_time <= time_window_end:
                time_window_count += 1
                total_L += customers
                total_W += customers * (current_time - server_start_time if server_busy else 0)
                busy_time += server_busy * (current_time - server_start_time)
                total_busy_frac += server_busy
                if customers > 0:
                    total_p_wait += 1
                if customers == 0:
                    total_p_loss += 1
            else:
                if time_window_count == 0:
                    time_window_start = current_time
                    time_window_end = current_time + win
                else:
                    time_window_start = current_time
                    time_window_end = current_time + win
                time_window_count = 0

        total_L /= time_window_count
        total_W /= time_window_count
        busy_frac = busy_time / (args.horizon * 60)
        p_loss = total_p_loss / time_window_count
        p_wait = total_p_wait / time_window_count
        per_seed_L.append(total_L)
        per_seed_W.append(total_W)
        per_seed_busy_frac.append(busy_frac)

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    arr = sum(total_arr for _ in range(seeds_used)) / seeds_used
    blk = sum(total_blk for _ in range(seeds_used)) / seeds_used
    dep = sum(total_dep for _ in range(seeds_used)) / seeds_used
    dep_rate = sum(total_dep_rate for _ in range(seeds_used)) / seeds_used
    p_loss = sum(total_p_loss for _ in range(seeds_used)) / seeds_used
    p_wait = sum(total_p_wait for _ in range(seeds_used)) / seeds_used
    runtime = time.time() - start_time
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