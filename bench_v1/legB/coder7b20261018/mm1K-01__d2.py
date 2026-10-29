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
    lam = 6
    mu = 6
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
    elif args.pert == 'c_up':
        pass  # Capacity unchanged

    time_unit = 'minute'
    win = args.horizon
    runtime_units = win / seeds_used

    L = 0
    W = 0
    busy_frac = 0
    p_loss = 0
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
        doctor_free = True
        doctor_start_time = 0
        total_time = 0
        total_busy_time = 0
        total_wait_time = 0
        total_arrivals = 0
        total_departures = 0
        total_rejections = 0

        for t in range(int(win * 60)):
            if doctor_free:
                if queue:
                    doctor_free = False
                    doctor_start_time = t
                    service_time = exponential(mu)
                    total_busy_time += service_time
                    total_departures += 1
                else:
                    doctor_start_time = t
            else:
                if t - doctor_start_time >= exponential(mu):
                    doctor_free = True

            if random.random() < lam / 60:
                total_arrivals += 1
                if len(queue) < 4:
                    queue.append(t)
                else:
                    total_rejections += 1

            if queue and t >= queue[0]:
                queue.pop(0)

            total_time += 1

        if total_time > 0:
            busy_frac += total_busy_time / total_time
            p_loss += total_rejections / total_arrivals
            arr += total_arrivals / seeds_used
            dep += total_departures / seeds_used
            blk += total_rejections / seeds_used
            dep_rate += total_departures / win
            lam_eff += total_arrivals / win
            p_wait += total_wait_time / total_arrivals

        per_seed_L.append(total_arrivals / seeds_used)
        per_seed_W.append(total_departures / seeds_used)
        per_seed_busy_frac.append(total_busy_time / total_time)
        per_seed_p_loss.append(total_rejections / total_arrivals)
        per_seed_p_wait.append(total_wait_time / total_arrivals)

    busy_util = total_busy_time / (seeds_used * win * 60)
    busy_occupied = 1 - exp(-lam * win / 60)

    print(json.dumps({
        'L': arr,
        'W': dep,
        'busy_frac': busy_frac / seeds_used,
        'p_loss': p_loss / seeds_used,
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
