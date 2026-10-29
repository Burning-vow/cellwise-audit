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
        lam = 9 / 60
        mu = 1 / 5
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            pass  # Capacity remains 4

        W = 0
        L = 0
        p_loss = 0
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

        queue = []
        time = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while time < win:
            if next_arrival < next_departure:
                time = next_arrival
                if len(queue) < 4:
                    queue.append(time)
                    next_arrival = time + random.expovariate(lam)
                    if len(queue) == 1:
                        next_departure = time + random.expovariate(mu)
                else:
                    p_loss += 1
                    next_arrival = time + random.expovariate(lam)
            else:
                time = next_departure
                dep += 1
                queue.pop(0)
                if queue:
                    next_departure = time + random.expovariate(mu)
                else:
                    next_departure = float('inf')

            if queue:
                W += len(queue) * (time - max(queue[0], 0))
                busy_frac += len(queue) * (time - max(queue[0], 0))
                p_wait += len(queue) * (time - max(queue[0], 0))
                arr += len(queue)
                dep_rate = dep / win
                busy_util = sum(min(len(queue), 4) for t in queue) / win
                busy_occupied = 1 - math.exp(-mu * win)

        if len(queue) > 0:
            W += len(queue) * (win - max(queue[0], 0))
            busy_frac += len(queue) * (win - max(queue[0], 0))
            p_wait += len(queue) * (win - max(queue[0], 0))
            arr += len(queue)
            dep_rate = dep / win
            busy_util = sum(min(len(queue), 4) for t in queue) / win
            busy_occupied = 1 - math.exp(-mu * win)

        per_seed_L.append(arr / args.seeds)
        per_seed_W.append(W / args.seeds)
        per_seed_busy_frac.append(busy_frac / args.seeds)
        per_seed_p_loss.append(p_loss / args.seeds)
        per_seed_p_wait.append(p_wait / args.seeds)

    print(json.dumps({
        'L': sum(per_seed_L) / args.seeds,
        'W': sum(per_seed_W) / args.seeds,
        'busy_frac': sum(per_seed_busy_frac) / args.seeds,
        'p_loss': sum(per_seed_p_loss) / args.seeds,
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
        'blk': p_loss / args.seeds,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait / args.seeds,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied
    }))

if __name__ == "__main__":
    main()
