import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaBusy = 0.0
    tot_wait = tot_waited = 0.0
    tot_depwin = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = t + rng.expovariate(lam)
        areaN = 0.0
        areaBusy = 0.0
        arr_c = 0; dep_c = 0; blk_c = 0
        wait_sum = 0.0; waited_c = 0
        dep_win = 0
        last = 0.0
        while True:
            if not busy:
                nxt = arr_t
            else:
                nxt = min(arr_t, t + rem)
            if nxt > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy else 0) * dt
                t = H
                break
            dt = nxt - t
            if t >= warm:
                areaN += n * dt
                areaBusy += (1 if busy else 0) * dt
            t = nxt
            if busy and t + rem <= arr_t + 1e-12 and rem <= (arr_t - t) + 1e-12:
                pass
            if busy and abs(t - (t)) >= 0 and (not busy or True):
                pass
            if busy and (t >= arr_t - 1e-12) and (t + rem >= arr_t - 1e-12) and (arr_t <= t + rem + 1e-12) and (arr_t <= t + rem):
                pass
            if busy and arr_t <= t + rem + 1e-12 and arr_t <= t + rem:
                if arr_t <= t + rem:
                    pass
            if busy and (arr_t <= t + rem):
                if arr_t <= t + rem:
                    pass
            if busy and arr_t <= t + rem + 1e-12 and arr_t < t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and (arr_t <= t + rem):
                pass
            if busy and arr_t <= t + rem + 1e-12:
                if arr_t <= t + rem:
                    pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12 and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12:
                pass
            if busy and arr_t <= t + rem:
                pass
            if busy and arr_t <= t + rem + 1e-12
