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
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            pass  # Capacity remains 4

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
        time_unit = 'minute'
        win = args.horizon

        queue = []
        time = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while time < win:
            if next_arrival < next_departure:
                time = next_arrival
                if len(queue) < 4:
                    if len(queue) == 0:
                        busy_occupied += 1
                    queue.append(time + random.expovariate(mu))
                    dep += 1
                else:
                    p_loss += 1
                    blk += 1
                next_arrival = time + random.expovariate(lam)
            else:
                time = next_departure
                if queue:
                    dep_rate += 1
                    busy_occupied += 1
                    next_departure = queue.pop(0) + random.expovariate(mu)
                else:
                    next_departure = float('inf')

            if time > win / 4:
                arr += len(queue)
                busy_frac += busy_occupied
                p_wait += sum(max(0, time - q) for q in queue)

        per_seed_L.append(arr / args.seeds)
        per_seed_W.append(p_wait / dep_rate)
        per_seed_busy_frac.append(busy_frac / win)
        per_seed_p_loss.append(p_loss / dep_rate)
        per_seed_p_wait.append(p_wait / dep_rate)

    output = {
        "L": sum(per_seed_L) / args.seeds,
        "W": sum(per_seed_W) / args.seeds,
        "busy_frac": sum(per_seed_busy_frac) / args.seeds,
        "p_loss": sum(per_seed_p_loss) / args.seeds,
        "runtime_units": time_unit,
        "seed_list": seeds,
        "seeds_used": args.seeds,
        "time_unit": time_unit,
        "win": win,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
