import sys
import json
import random
from math import exp, factorial

def poisson(lam, k):
    return (lam ** k * exp(-lam)) / factorial(k)

def main():
    args = sys.argv[1:]
    seeds = int(next((arg.split('=')[1] for arg in args if arg.startswith('--seeds=')), 100))
    horizon = float(next((arg.split('=')[1] for arg in args if arg.startswith('--horizon=')), 1000))
    seed_start = int(next((arg.split('=')[1] for arg in args if arg.startswith('--seed-start=')), 0))
    perturbation = next((arg.split('=')[1] for arg in args if arg.startswith('--pert=')), 'none')

    if perturbation == 'lam_up':
        lam = 4 * 1.1
    elif perturbation == 'mu_up':
        mu = 6 / 1.1
    elif perturbation == 'c_up':
        c = 1.1
    else:
        lam = 4
        mu = 6
        c = 1

    time_unit = 'minute'
    win = horizon
    runtime_units = horizon

    seed_list = list(range(seed_start, seed_start + seeds))
    seeds_used = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        arr = 0
        dep = 0
        blk = 0
        busy_time = 0
        total_time = 0
        queue = []
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while total_time < horizon:
            if next_arrival < next_departure:
                total_time = next_arrival
                arr += 1
                if queue:
                    next_departure = total_time + 6
                    busy_time += 6
                else:
                    next_departure = float('inf')
                queue.append(total_time)
            else:
                total_time = next_departure
                dep += 1
                if queue:
                    next_arrival = total_time + random.expovariate(lam)
                    next_departure = total_time + 6
                    busy_time += 6
                    queue.pop(0)
                else:
                    next_arrival = float('inf')
                    next_departure = float('inf')

        L = sum(queue) / total_time
        W = busy_time / dep
        busy_frac = busy_time / total_time
        p_loss = blk / arr
        p_wait = sum(queue) / arr

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

        seeds_used += 1

    per_seed_L = per_seed_L[seeds_used // 4:]
    per_seed_W = per_seed_W[seeds_used // 4:]
    per_seed_busy_frac = per_seed_busy_frac[seeds_used // 4:]
    per_seed_p_loss = per_seed_p_loss[seeds_used // 4:]
    per_seed_p_wait = per_seed_p_wait[seeds_used // 4:]

    print(json.dumps({
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': sum(per_seed_L) / len(per_seed_L),
        'dep': sum(per_seed_L) / len(per_seed_L),
        'blk': sum(per_seed_L) / len(per_seed_L),
        'dep_rate': sum(per_seed_L) / len(per_seed_L),
        'lam_eff': sum(per_seed_L) / len(per_seed_L),
        'p_loss': sum(per_seed_L) / len(per_seed_L),
        'p_wait': sum(per_seed_L) / len(per_seed_L),
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
