import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
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
        lam = 8 / 60
        mu = 1 / 10
        c = 3
        N = 0
        W = 0
        L = 0
        busy_time = 0
        total_time = 0
        queue = []
        busy = [False] * c
        p_wait = 0
        p_loss = 0

        for t in range(int(args.horizon * 60)):
            if random.random() < lam:
                N += 1
                if N > c:
                    p_loss += 1
                else:
                    if not any(busy):
                        busy[0] = True
                        busy_time += 1
                    else:
                        queue.append(t)

            if queue and not any(busy):
                busy[queue.pop(0)] = True
                busy_time += 1

            for i in range(c):
                if busy[i]:
                    busy_time += 1
                    if random.random() < mu:
                        busy[i] = False
                        N -= 1
                        W += t - total_time
                        total_time = t

            L += N
            busy_frac = sum(busy) / c
            p_wait = p_loss / N if N > 0 else 0

            per_seed_L.append(L)
            per_seed_W.append(W)
            per_seed_busy_frac.append(busy_frac)
            per_seed_p_loss.append(p_loss)
            per_seed_p_wait.append(p_wait)

        L /= args.horizon * 60
        W /= args.horizon * 60
        busy_frac = sum(busy) / c
        p_wait = p_loss / N if N > 0 else 0

        print(json.dumps({
            "L": L,
            "W": W,
            "busy_frac": busy_frac,
            "p_wait": p_wait,
            "runtime_units": "minute",
            "seed_list": seeds,
            "seeds_used": args.seeds,
            "time_unit": "minute",
            "win": args.horizon,
            "per_seed_L": per_seed_L,
            "per_seed_W": per_seed_W,
            "per_seed_busy_frac": per_seed_busy_frac,
            "per_seed_p_loss": per_seed_p_loss,
            "per_seed_p_wait": per_seed_p_wait
        }))

if __name__ == "__main__":
    main()
