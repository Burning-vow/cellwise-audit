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
        lam = 7 / 60
        mu = 1 / 6
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        t = 0
        n = 0
        busy = 0
        wait = 0
        loss = 0
        dep = 0
        arr = 0

        while t < args.horizon:
            if n == 0:
                inter_arrival = exponential(lam)
                t += inter_arrival
                if t >= args.horizon:
                    break
                n += 1
                arr += 1
                wait = 0
            else:
                service_time = exponential(mu)
                if t + service_time > args.horizon:
                    loss += 1
                    dep += n
                    n -= 1
                    busy += service_time
                    t += service_time
                    break
                t += service_time
                n -= 1
                dep += 1
                busy += service_time

        per_seed_L.append(n)
        per_seed_W.append(wait / dep if dep > 0 else 0)
        per_seed_busy_frac.append(busy / t)
        per_seed_p_loss.append(loss / arr if arr > 0 else 0)
        per_seed_p_wait.append(wait / dep if dep > 0 else 0)

    per_seed_L = per_seed_L[25:]
    per_seed_W = per_seed_W[25:]
    per_seed_busy_frac = per_seed_busy_frac[25:]
    per_seed_p_loss = per_seed_p_loss[25:]
    per_seed_p_wait = per_seed_p_wait[25:]

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
