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
        mu = 6 * 1.1
    elif perturbation == 'c_up':
        lam = 8
        mu = 6
        c = 2
    else:
        lam = 8
        mu = 6
        c = 1

    time_unit = 'hour'
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
                    queue[0]['arrival_time'] = total_time
                else:
                    next_departure = total_time + 6
                    busy_time += 6
                if len(queue) < c:
                    queue.append({'arrival_time': total_time})
                else:
                    blk += 1
            else:
                total_time = next_departure
                dep += 1
                queue.pop(0)
                if queue:
                    next_departure = total_time + 6
                    busy_time += 6
                else:
                    next_departure = float('inf')

            next_arrival += random.expovariate(lam)

        L = arr / win
        W = busy_time / dep
        busy_frac = busy_time / win
        p_loss = blk / arr
        p_wait = (busy_time - dep * 6) / busy_time

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
        'dep': sum(per_seed_W) / len(per_seed_W),
        'blk': sum(per_seed_p_loss) / len(per_seed_p_loss),
        'dep_rate': sum(per_seed_W) / len(per_seed_W) * 60,
        'lam_eff': lam,
        'p_loss': sum(per_seed_p_loss) / len(per_seed_p_loss),
        'p_wait': sum(per_seed_p_wait) / len(per_seed_p_wait),
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
