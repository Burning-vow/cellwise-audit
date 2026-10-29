import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100)
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
        lam = 6 / 60  # arrival rate in jobs per minute
        mu = 6 / 60  # service rate in jobs per minute
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            lam *= 1.1
            mu *= 1.1

        Q1 = []  # queue 1
        Q2 = []  # queue 2
        S1 = None  # server 1
        S2 = None  # server 2
        t = 0  # current time
        W = 0  # total waiting time
        L = 0  # total number of jobs in the system
        arr = 0  # number of arrivals
        dep = 0  # number of departures
        blk = 0  # number of blocked jobs
        dep_rate = 0  # effective departure rate
        busy_frac = 0  # busy fraction
        busy_util = 0  # busy utilization
        p_loss = 0  # probability of loss
        p_wait = 0  # probability of waiting

        while t < args.horizon:
            if S1 is None and Q1:
                S1 = Q1.pop(0)
                S1['start'] = t
            if S2 is None and Q2:
                S2 = Q2.pop(0)
                S2['start'] = t

            if S1 and S2:
                if S1['start'] < S2['start']:
                    t = S1['start']
                    S1['end'] = t + S1['service']
                    W += S1['end'] - S1['arrival']
                    L -= 1
                    dep += 1
                    S1 = None
                else:
                    t = S2['start']
                    S2['end'] = t + S2['service']
                    W += S2['end'] - S2['arrival']
                    L -= 1
                    dep += 1
                    S2 = None
            elif S1:
                t = S1['start']
                S1['end'] = t + S1['service']
                W += S1['end'] - S1['arrival']
                L -= 1
                dep += 1
                S1 = None
            elif S2:
                t = S2['start']
                S2['end'] = t + S2['service']
                W += S2['end'] - S2['arrival']
                L -= 1
                dep += 1
                S2 = None
            else:
                t = random.expovariate(lam)

            if t >= args.horizon:
                break

            if S1 is None and S2 is None:
                arr += 1
                L += 1
                if Q1:
                    Q1[-1]['end'] = t
                Q1.append({'arrival': t, 'service': random.expovariate(mu), 'end': t})

            if S1 is None and S2 is not None:
                arr += 1
                L += 1
                if Q2:
                    Q2[-1]['end'] = t
                Q2.append({'arrival': t, 'service': random.expovariate(mu), 'end': t})

            if S1 is not None and S2 is None:
                arr += 1
                L += 1
                if Q1:
                    Q1[-1]['end'] = t
                Q1.append({'arrival': t, 'service': random.expovariate(mu), 'end': t})

            if S1 is not None and S2 is not None:
                arr += 1
                L += 1
                if Q1:
                    Q1[-1]['end'] = t
                Q1.append({'arrival': t, 'service': random.expovariate(mu), 'end': t})

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    L = sum(per_seed_L[25:]) / len(per_seed_L[25:])
    W = sum(per_seed_W[25:]) / len(per_seed_W[25:])
    busy_frac = sum(per_seed_busy_frac[25:]) / len(per_seed_busy_frac[25:])
    p_loss = sum(per_seed_p_loss[25:]) / len(per_seed_p_loss[25:])
    p_wait = sum(per_seed_p_wait[25:]) / len(per_seed_p_wait[25:])

    print(json.dumps({
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
