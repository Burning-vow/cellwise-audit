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
        mu = 5 * 1.1
    elif perturbation == 'c_up':
        lam = 8
        mu = 5
        c = 2
    else:
        lam = 8
        mu = 5
        c = 1

    time_unit = 'hour'
    win = horizon
    runtime_units = win

    seed_list = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in range(seed_start, seed_start + seeds):
        random.seed(seed)
        queue = []
        busy = False
        busy_time = 0
        total_wait_time = 0
        total_service_time = 0
        total_arrivals = 0
        total_departures = 0
        total_rejections = 0

        for t in range(int(horizon * 60)):
            if random.random() < lam / 60:
                total_arrivals += 1
                queue.append(t)

            if busy:
                busy_time += 1
                if busy_time >= mu:
                    busy = False
                    total_departures += 1
                    if queue:
                        next_arrival = queue.pop(0)
                        wait_time = t - next_arrival
                        total_wait_time += wait_time
                        total_service_time += mu
                    else:
                        total_rejections += 1

            if not busy and queue:
                busy = True
                busy_time = 0

        if total_arrivals > 0:
            avg_wait_time = total_wait_time / total_arrivals
            avg_service_time = total_service_time / total_departures
            avg_queue_length = sum(len(queue) for t in range(int(horizon * 60))) / (int(horizon * 60))
            busy_frac = busy_time / (int(horizon * 60))
            p_loss = total_rejections / total_arrivals
            p_wait = avg_wait_time / avg_service_time
            L = avg_queue_length
            W = avg_wait_time + avg_service_time

            per_seed_L.append(L)
            per_seed_W.append(W)
            per_seed_busy_frac.append(busy_frac)
            per_seed_p_loss.append(p_loss)
            per_seed_p_wait.append(p_wait)

            seed_list.append(seed)

    per_seed_L = per_seed_L[25:]
    per_seed_W = per_seed_W[25:]
    per_seed_busy_frac = per_seed_busy_frac[25:]
    per_seed_p_loss = per_seed_p_loss[25:]
    per_seed_p_wait = per_seed_p_wait[25:]

    print(json.dumps({
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': len(per_seed_L),
        'time_unit': time_unit,
        'win': win,
        'arr': sum(per_seed_L) / len(per_seed_L),
        'blk': sum(per_seed_p_loss) / len(per_seed_p_loss),
        'busy_util': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'dep': sum(per_seed_departures) / len(per_seed_departures),
        'dep_rate': sum(per_seed_departures) / horizon,
        'lam_eff': lam,
        'p_loss': sum(per_seed_p_loss) / len(per_seed_p_loss),
        'p_wait': sum(per_seed_p_wait) / len(per_seed_p_wait)
    }))

if __name__ == "__main__":
    main()
