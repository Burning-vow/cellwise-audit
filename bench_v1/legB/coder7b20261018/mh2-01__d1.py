import sys
import json
import random
from math import exp, sqrt, pi

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
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
        lam = 3
        mu = 6 / (1.5 ** 2)
        sigma = sqrt(6 / (1.5 ** 2))
        W = 6 / (1.5 ** 2)
        L = lam / mu

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0

        time = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = False

        while time < args.horizon:
            if next_arrival < next_departure:
                time = next_arrival
                if not busy:
                    busy = True
                    next_departure = time + random.expovariate(mu)
                    dep += 1
                    busy_util += 1
                else:
                    blk += 1
                    p_loss += 1
            else:
                time = next_departure
                busy = False
                next_arrival = time + random.expovariate(lam)
                arr += 1

            if time >= args.horizon * 0.25:
                arr -= per_seed_L[-1] if per_seed_L else 0
                dep -= per_seed_W[-1] if per_seed_W else 0
                blk -= per_seed_busy_frac[-1] if per_seed_busy_frac else 0
                p_loss -= per_seed_p_loss[-1] if per_seed_p_loss else 0
                p_wait -= per_seed_p_wait[-1] if per_seed_p_wait else 0

                per_seed_L.append(arr / (time - args.horizon * 0.25))
                per_seed_W.append(dep / (time - args.horizon * 0.25))
                per_seed_busy_frac.append(busy_util / (time - args.horizon * 0.25))
                per_seed_p_loss.append(p_loss / (time - args.horizon * 0.25))
                per_seed_p_wait.append(p_wait / (time - args.horizon * 0.25))

        busy_frac = busy_util / args.horizon
        dep_rate = dep / args.horizon

        per_seed_L = per_seed_L[1:]
        per_seed_W = per_seed_W[1:]
        per_seed_busy_frac = per_seed_busy_frac[1:]
        per_seed_p_loss = per_seed_p_loss[1:]
        per_seed_p_wait = per_seed_p_wait[1:]

        print(json.dumps({
            'L': L,
            'W': W,
            'busy_frac': busy_frac,
            'runtime_units': 'hour',
            'seed_list': seed_list,
            'seeds_used': seeds_used,
            'time_unit': 'hour',
            'win': args.horizon,
            'arr': arr,
            'dep': dep,
            'blk': blk,
            'dep_rate': dep_rate,
            'lam_eff': lam,
            'p_loss': p_loss / args.horizon,
            'p_wait': p_wait / args.horizon,
            'per_seed_L': per_seed_L,
            'per_seed_W': per_seed_W,
            'per_seed_busy_frac': per_seed_busy_frac,
            'per_seed_p_loss': per_seed_p_loss,
            'per_seed_p_wait': per_seed_p_wait
        }))

if __name__ == "__main__":
    main()
