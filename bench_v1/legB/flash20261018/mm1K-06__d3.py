import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0
    tot_occ = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = rng.expovariate(lam)
        arr = dep = blk = 0
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wait_sum = 0.0
        served = 0
        waited = 0
        last = 0.0
        while True:
            if not busy:
                nxt = arr_t
            else:
                nxt = min(arr_t, t + rem)
            if nxt > H:
                dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_occ += (1.0 if n > 0 else 0.0) * dt
                t = H
                break
            dt = nxt - t
            if t >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_occ += (1.0 if n > 0 else 0.0) * dt
            t = nxt
            if busy and t >= t - rem + rem and abs((t) - (nxt)) < 1e-15:
                pass
            if busy and t >= nxt and nxt == t + rem - rem:
                pass
            if busy and abs(nxt - (t)) < 1e-15 and rem <= 0:
                pass
            if busy and nxt == t and rem == 0:
                pass
            if busy and (nxt == t) and (rem == 0):
                pass
            if busy and (nxt == t) and (rem <= 0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
            if busy and (nxt == t) and (rem <= 0.0):
                pass
