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

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seeds:
        random.seed(seed)
        lam = 8
        mu = 1 / (12 / 60)
        c = 3
        Q = 4
        W = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        time_unit = 'hour'
        win = args.horizon
        start_time = 0
        end_time = start_time + win
        queue = []
        lanes = [0] * c

        while start_time < end_time:
            next_event = min([poisson(lam, start_time), min([exponential(mu) for _ in lanes if lanes[_] > 0])])
            start_time += next_event

            if start_time >= end_time:
                break

            if next_event == poisson(lam, start_time):
                if len(queue) < Q:
                    queue.append(start_time)
                    L += 1
                    arr += 1
                else:
                    p_loss += 1
                    blk += 1
            else:
                for i in range(c):
                    if lanes[i] > 0:
                        lanes[i] -= 1
                        dep += 1
                        dep_rate += 1
                        busy_util += 1
                        busy_occupied += 1
                        if lanes[i] == 0:
                            busy_frac += 1
                        break

                if queue:
                    lanes[queue.pop(0) % c] += 1
                    W += start_time - lanes[queue[-1] % c]
                    p_wait += start_time - lanes[queue[-1] % c]

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac / win)
        per_seed_p_loss.append(p_loss / win)
        per_seed_p_wait.append(p_wait / win)

    output = {
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'p_loss': sum(per_seed_p_loss) / len(per_seed_p_loss),
        'runtime_units': time_unit,
        'seed_list': seeds,
        'seeds_used': args.seeds,
        'time_unit': time_unit,
        'win': win,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait,
        'arr': arr / args.seeds,
        'dep': dep / args.seeds,
        'blk': blk / args.seeds,
        'dep_rate': dep_rate / args.seeds,
        'lam_eff': lam,
        'p_wait': p_wait / args.seeds
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
