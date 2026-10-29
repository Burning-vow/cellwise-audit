import sys
import json
import random
import math

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
        mu = 1 / 6
        c = 3
        Q = 4
        W = 0
        L = 0
        p_loss = 0
        p_wait = 0
        busy_time = 0
        total_time = 0
        queue = []
        lanes = [0] * c

        for t in range(int(args.horizon * 60)):
            if random.random() < lam:
                if len(queue) < Q:
                    queue.append(t)
                else:
                    p_loss += 1

            for i in range(c):
                if lanes[i] > 0:
                    lanes[i] -= 1
                    if lanes[i] == 0:
                        busy_time += 1

            if queue and lanes[0] == 0:
                lanes[0] = random.expovariate(mu)
                W += t - queue.pop(0)
                L += 1
                p_wait += 1

            total_time += 1

        per_seed_L.append(L)
        per_seed_W.append(W / L if L > 0 else 0)
        per_seed_busy_frac.append(busy_time / total_time)
        per_seed_p_loss.append(p_loss / total_time)
        per_seed_p_wait.append(p_wait / total_time)

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_loss": p_loss,
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
