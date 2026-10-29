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
        mu = 1 / (5 / 60) if args.pert == 'mu_up' else 1 / (5 / 60)
        c = 6
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

        while time < win:
            if not queue and random.expovariate(lam) < win - time:
                queue.append(random.expovariate(mu))
                arr += 1
            if queue and queue[0] <= win - time:
                dep += 1
                dep_rate += 1 / win
                if len(queue) > 1:
                    queue[0] = random.expovariate(mu)
                else:
                    queue = []
            if len(queue) < c:
                if queue:
                    queue[0] += random.expovariate(mu)
                else:
                    busy_util += 1
                    busy_occupied += 1
            else:
                p_loss += 1
                blk += 1
            time += random.expovariate(lam)

        busy_frac = 1 - busy_occupied / win
        p_wait = p_loss / arr if arr else 0
        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    per_seed_L = per_seed_L[len(per_seed_L) // 4:]
    per_seed_W = per_seed_W[len(per_seed_W) // 4:]
    per_seed_busy_frac = per_seed_busy_frac[len(per_seed_busy_frac) // 4:]
    per_seed_p_loss = per_seed_p_loss[len(per_seed_p_loss) // 4:]
    per_seed_p_wait = per_seed_p_wait[len(per_seed_p_wait) // 4:]

    print(json.dumps({
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
        'p_wait': p_wait
    }))

if __name__ == "__main__":
    main()
