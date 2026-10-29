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
        mu = 1 / 12
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 3
        Q = []
        S = [0] * N
        t = 0
        L = 0
        W = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0

        while t < args.horizon:
            if not Q and random.expovariate(lam) < args.horizon - t:
                Q.append(random.expovariate(mu))
                p_wait += 1
            if Q and all(S[i] <= t for i in range(N)):
                S[Q.index(min(Q))], Q = t + Q.pop(Q.index(min(Q))), Q[1:]
                dep += 1
                dep_rate += 1 / args.horizon
            if Q and any(S[i] <= t for i in range(N)):
                p_loss += 1
                blk += 1
            if Q:
                W += min(Q) * (min(S[i] for i in range(N)) - t if any(S[i] <= t for i in range(N)) else args.horizon - t)
            L += len(Q)
            busy_frac += sum(1 for i in range(N) if S[i] > t)
            arr += len(Q)
            t += min(random.expovariate(lam), min(Q) if Q else args.horizon - t)

        per_seed_L.append(L / args.horizon)
        per_seed_W.append(W / arr)
        per_seed_busy_frac.append(busy_frac / (N * args.horizon))
        per_seed_p_loss.append(p_loss / arr)
        per_seed_p_wait.append(p_wait / arr)

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': args.seeds,
        'time_unit': 'hour',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
