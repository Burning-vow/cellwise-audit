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
        sigma = sqrt(mu * (1.5 ** 2 - 1))
        W = mu + sigma
        L = lam / (mu - lam)

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        busy_frac = 0

        time_unit = 'minute'
        win = args.horizon
        runtime_units = win / args.horizon

        for t in range(int(win * 60)):
            if random.expovariate(lam) < 1:
                arr += 1
                if busy_util > 0:
                    dep += 1
                    busy_util -= 1
                else:
                    blk += 1
            if busy_util > 0:
                busy_util -= 1
            else:
                if arr > 0:
                    arr -= 1
                    busy_util += 1

        busy_frac = busy_util / win
        p_loss = blk / (arr + dep + blk)
        p_wait = p_loss / (1 - busy_frac)

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep / win,
        'lam_eff': lam,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
