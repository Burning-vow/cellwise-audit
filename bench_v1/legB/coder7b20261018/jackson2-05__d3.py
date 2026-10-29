import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1000)
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

        lam1 = 6 / 60  # arrival rate for process 1
        mu1 = 1 / 7.5  # service rate for process 1
        mu2 = 1 / 6  # service rate for process 2

        if args.pert == 'lam_up':
            lam1 *= 1.1
        elif args.pert == 'mu_up':
            mu1 *= 1.1
            mu2 *= 1.1
        elif args.pert == 'c_up':
            mu1 *= 1.1
            mu2 *= 1.1

        Q1 = 0  # queue length for process 1
        Q2 = 0  # queue length for process 2
        S1 = 0  # service start time for process 1
        S2 = 0  # service start time for process 2
        L = 0  # total number of items in the system
        W = 0  # total waiting time for all items
        busy_frac = 0  # total busy fraction
        p_loss = 0  # total loss probability
        p_wait = 0  # total waiting probability

        for t in range(int(args.horizon * 60)):
            if Q1 > 0:
                if t >= S1:
                    Q1 -= 1
                    S1 = 0
                    W += t - S1
                    L -= 1
                    p_wait += 1
            if Q2 > 0:
                if t >= S2:
                    Q2 -= 1
                    S2 = 0
                    L -= 1
                    p_wait += 1

            if Q1 == 0 and Q2 == 0 and S1 == 0 and S2 == 0:
                if random.expovariate(lam1) < 60:
                    Q1 += 1
                    L += 1
                    if Q1 == 1:
                        S1 = t + random.expovariate(mu1)
                    p_loss += 1

            if Q1 == 1 and S1 == 0:
                S1 = t + random.expovariate(mu1)
                Q1 -= 1
                L -= 1
                p_loss += 1

            if Q2 == 1 and S2 == 0:
                S2 = t + random.expovariate(mu2)
                Q2 -= 1
                L -= 1
                p_loss += 1

            busy_frac += max(S1 > 0, S2 > 0)
            L += Q1 + Q2

        arr = L / args.horizon
        dep = L / args.horizon
        blk = p_loss / args.horizon
        dep_rate = dep / args.horizon
        lam_eff = lam1 * (1 - p_loss)
        p_wait /= args.horizon
        busy_util = busy_frac / args.horizon
        win = args.horizon

        per_seed_L.append(L / args.horizon)
        per_seed_W.append(W / args.horizon)
        per_seed_busy_frac.append(busy_frac / args.horizon)
        per_seed_p_loss.append(p_loss / args.horizon)
        per_seed_p_wait.append(p_wait / args.horizon)

    L = sum(per_seed_L[25:]) / (seeds_used - 25)
    W = sum(per_seed_W[25:]) / (seeds_used - 25)
    busy_frac = sum(per_seed_busy_frac[25:]) / (seeds_used - 25)
    p_loss = sum(per_seed_p_loss[25:]) / (seeds_used - 25)
    p_wait = sum(per_seed_p_wait[25:]) / (seeds_used - 25)

    print(json.dumps({
        "L": L,
        "W": W,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": win,
        "arr": arr,
        "blk": blk,
        "busy_frac": busy_frac,
        "busy_util": busy_util,
        "dep": dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
