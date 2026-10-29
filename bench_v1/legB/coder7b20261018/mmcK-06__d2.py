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
        lam = 6
        mu = 6 / 60
        capacity = 4
        lanes = 3
        queue = []
        busy = [False] * lanes
        total_time = 0
        total_arr = 0
        total_dep = 0
        total_blk = 0
        total_p_wait = 0
        total_busy = 0

        for t in range(int(args.horizon * 60)):
            if random.expovariate(lam) < 1:
                total_arr += 1
                if len(queue) < capacity:
                    queue.append(t)
                else:
                    total_blk += 1

            for i in range(lanes):
                if busy[i]:
                    if t - queue[i] >= 60 * mu:
                        busy[i] = False
                        total_dep += 1
                        total_busy += 1

            if queue and not any(busy):
                busy[queue.pop(0) % lanes] = True

            total_time += 1

        L = total_arr / args.seeds
        W = total_busy / total_dep if total_dep > 0 else 0
        busy_frac = 1 - math.exp(-lam * args.horizon)
        p_loss = total_blk / total_arr
        p_wait = total_p_wait / total_arr if total_arr > 0 else 0

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        "L": sum(per_seed_L) / args.seeds,
        "W": sum(per_seed_W) / args.seeds,
        "busy_frac": sum(per_seed_busy_frac) / args.seeds,
        "p_loss": sum(per_seed_p_loss) / args.seeds,
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
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
