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
    parser.add_argument('--horizon', type=float, default=100)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        lam = 6 if args.pert == 'lam_up' else 6
        mu = 12 if args.pert == 'mu_up' else 12
        c = 1
        rho = lam / mu
        if rho >= 1:
            per_seed_L.append('不可比')
            per_seed_W.append('不可比')
            per_seed_busy_frac.append('不可比')
            per_seed_p_loss.append('不可比')
            per_seed_p_wait.append('不可比')
            continue

        L = 0
        W = 0
        busy_frac = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        time_unit = 'minute'
        win = args.horizon
        start_time = 0
        end_time = win
        next_arrival = exponential(lam)
        next_departure = float('inf')
        busy = False

        while next_arrival < end_time:
            if next_arrival < next_departure:
                current_time = next_arrival
                next_arrival += exponential(lam)
                if busy:
                    dep += 1
                    dep_rate += 1
                    busy = False
                L += current_time - start_time
                busy_frac += current_time - start_time if busy else 0
                busy_util += current_time - start_time if busy else 0
                busy_occupied += current_time - start_time if busy else 0
                start_time = current_time
            else:
                current_time = next_departure
                next_departure += exponential(mu)
                L += current_time - start_time
                busy_frac += current_time - start_time if busy else 0
                busy_util += current_time - start_time if busy else 0
                busy_occupied += current_time - start_time if busy else 0
                start_time = current_time
                busy = True

        L /= win
        W = L / rho
        busy_frac /= win
        p_wait = L / (L + dep_rate)
        arr = L
        dep = dep_rate
        blk = 0
        dep_rate /= 60
        lam_eff = lam
        p_loss = 0

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': time_unit,
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
        'p_loss': p_loss,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
