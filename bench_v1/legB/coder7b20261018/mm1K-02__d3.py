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
        lam = 6 if args.pert == 'lam_up' else 6
        mu = 5 if args.pert == 'mu_up' else 5
        c = 4
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
        doctor_free = True
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while next_arrival < win:
            if next_arrival < next_departure:
                current_time = next_arrival
                next_arrival = random.expovariate(lam)
                if len(queue) < c:
                    if doctor_free:
                        doctor_free = False
                        next_departure = current_time + random.expovariate(mu)
                        W += next_departure - current_time
                        dep += 1
                    else:
                        queue.append(current_time)
                        p_wait += next_departure - current_time
                        dep += 1
                else:
                    p_loss += 1
                    dep += 1
            else:
                current_time = next_departure
                next_departure = float('inf')
                if queue:
                    next_departure = current_time + random.expovariate(mu)
                    W += next_departure - current_time
                    dep += 1
                else:
                    doctor_free = True

            arr += 1
            busy_frac += doctor_free
            busy_util += len(queue) / c
            busy_occupied += doctor_free

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac / win)
        per_seed_p_loss.append(p_loss / dep)
        per_seed_p_wait.append(p_wait / dep)

    L = sum(per_seed_L[25:]) / len(per_seed_L[25:])
    W = sum(per_seed_W[25:]) / len(per_seed_W[25:])
    busy_frac = sum(per_seed_busy_frac[25:]) / len(per_seed_busy_frac[25:])
    p_loss = sum(per_seed_p_loss[25:]) / len(per_seed_p_loss[25:])
    p_wait = sum(per_seed_p_wait[25:]) / len(per_seed_p_wait[25:])

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': time_unit,
        'seed_list': seeds,
        'seeds_used': args.seeds,
        'time_unit': time_unit,
        'win': win,
        'arr': arr / args.seeds,
        'dep': dep / args.seeds,
        'blk': blk / args.seeds,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
