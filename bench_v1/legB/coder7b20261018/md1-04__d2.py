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
        lam = 6 * 1.1
    elif perturbation == 'mu_up':
        lam = 6
        mu = 5 * 1.1
    elif perturbation == 'c_up':
        lam = 6
        mu = 5
        c = 2
    else:
        lam = 6
        mu = 5
        c = 1

    time_unit = 'minute'
    win = horizon
    runtime_units = win

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
                    next_departure = total_time + 5
                else:
                    next_departure = float('inf')
                queue.append(total_time)
            else:
                total_time = next_departure
                dep += 1
                if queue:
                    next_arrival = total_time + random.expovariate(lam)
                    next_departure = total_time + 5
                    queue.pop(0)
                else:
                    next_arrival = float('inf')
                    next_departure = float('inf')

            if total_time > horizon / 4:
                busy_time += len(queue) * min(5, total_time - next_departure) if next_departure < total_time else len(queue) * 5
                arr -= 1 if next_departure < total_time else 0

        L = arr / win
        W = busy_time / dep if dep > 0 else 0
        busy_frac = busy_time / win
        p_loss = blk / arr if arr > 0 else 0
        p_wait = W / 5 if W > 0 else 0

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

        seeds_used += 1

    print(json.dumps({
        'L': sum(per_seed_L) / seeds_used,
        'W': sum(per_seed_W) / seeds_used,
        'busy_frac': sum(per_seed_busy_frac) / seeds_used,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': sum(per_seed_L) / seeds_used,
        'dep': sum(per_seed_W) / seeds_used,
        'blk': sum(per_seed_p_loss) / seeds_used,
        'dep_rate': sum(per_seed_W) / seeds_used * 60,
        'lam_eff': lam,
        'p_loss': sum(per_seed_p_loss) / seeds_used,
        'p_wait': sum(per_seed_p_wait) / seeds_used,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
