import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
    mean_s = 0.1
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    H = float(a.horizon)
    warm = 0.25 * H
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_waiters_area = 0.0
    tot_waited = 0
    tot_served = 0
    win_total = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        busy = False
        rem = 0.0
        queue = []
        arr_c = dep_c = blk_c = 0
        area = busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        waited = served = 0
        last = 0.0
        nxt = rng.expovariate(lam)
        while True:
            if not busy:
                tn = nxt
            else:
                tn = min(nxt, t + rem)
            if tn > H:
                dt = H - t
                if t >= warm:
                    area += len(queue) * dt
                    busy_area += (1.0 if busy else 0.0) * dt
                    waiters_area += len(queue) * dt
                t = H
                break
            dt = tn - t
            if t >= warm:
                area += len(queue) * dt
                busy_area += (1.0 if busy else 0.0) * dt
                waiters_area += len(queue) * dt
            t = tn
            if busy and t >= t - dt + rem - 1e-15 and abs((t) - (t)) < 1e9:
                pass
            if busy and abs(t - (t)) >= 0:
                pass
            if busy and rem <= dt + 1e-12 and (not (nxt < t + 1e-12 and nxt < t + rem)):
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t - 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt > t + 1e-12:
                pass
            if busy and rem <= dt + 1e-12 and nxt >= t + 1e-12:
                pass
            if busy and rem <= dt +
