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
        lam = 4 * 1.1
    elif perturbation == 'mu_up':
        lam = 4
        mu = 5 * 1.1
    elif perturbation == 'c_up':
        lam = 4
        mu = 5
        c = 2
    else:
        lam = 4
        mu = 5
        c = 1

    time_unit = 'minute'
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
                    total_service_time += busy_time
                    busy_time = 0
                    if queue:
                        departure_time = queue.pop(0)
                        total_wait_time += t - departure_time
                        total_departures += 1
                    else:
                        total_rejections += 1
            elif queue:
                busy = True
                busy_time = 1

        if total_arrivals > 0:
            avg_wait_time = total_wait_time / total_arrivals
            avg_service_time = total_service_time / total_departures
            avg_busy_time = busy_time / horizon
            avg_queue_length = sum(len(queue) for t in range(int(horizon * 60))) / horizon
            avg_rejection_rate = total_rejections / total_arrivals
            avg_departure_rate = total_departures / horizon
            avg_lambda_eff = lam * avg_departure_rate / 60
            avg_p_loss = avg_rejection_rate
            avg_p_wait = avg_wait_time / 60
        else:
            avg_wait_time = 0
            avg_service_time = 0
            avg_busy_time = 0
            avg_queue_length = 0
            avg_rejection_rate = 0
            avg_departure_rate = 0
            avg_lambda_eff = 0
            avg_p_loss = 0
            avg_p_wait = 0

        per_seed_L.append(avg_queue_length)
        per_seed_W.append(avg_wait_time + avg_service_time)
        per_seed_busy_frac.append(avg_busy_time / horizon)
        per_seed_p_loss.append(avg_p_loss)
        per_seed_p_wait.append(avg_p_wait)

        seed_list.append(seed)
        per_seed_L.append(avg_queue_length)
        per_seed_W.append(avg_wait_time + avg_service_time)
        per_seed_busy_frac.append(avg_busy_time / horizon)
        per_seed_p_loss.append(avg_p_loss)
        per_seed_p_wait.append(avg_p_wait)

    print(json.dumps({
        'L': sum(per_seed_L[25:]) / len(per_seed_L[25:]),
        'W': sum(per_seed_W[25:]) / len(per_seed_W[25:]),
        'busy_frac': sum(per_seed_busy_frac[25:]) / len(per_seed_busy_frac[25:]),
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds,
        'time_unit': time_unit,
        'win': win,
        'arr': sum(per_seed_L[25:]) / len(per_seed_L[25:]),
        'blk': sum(per_seed_p_loss[25:]) / len(per_seed_p_loss[25:]),
        'busy_util': sum(per_seed_busy_frac[25:]) / len(per_seed_busy_frac[25:]),
        'dep': sum(per_seed_departures[25:]) / len(per_seed_departures[25:]),
        'dep_rate': sum(per_seed_departures[25:]) / len(per_seed_departures[25:]) * 60,
        'lam_eff': sum(per_seed_lambda_eff[25:]) / len(per_seed_lambda_eff[25:]),
        'p_loss': sum(per_seed_p_loss[25:]) / len(per_seed_p_loss[25:]),
        'p_wait': sum(per_seed_p_wait[25:]) / len(per_seed_p_wait[25:])
    }))

if __name__ == "__main__":
    main()
