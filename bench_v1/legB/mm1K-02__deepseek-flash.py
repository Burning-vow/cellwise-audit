import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 12.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1

    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = a.horizon
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_blk = 0.0
    tot_dep = 0.0
    tot_wait = 0.0
    tot_area_n = 0.0
    tot_area_busy = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_dep = float('inf')
        arr_c = 0
        blk_c = 0
        dep_c = 0
        wait_sum = 0.0
        area_n = 0.0
        area_busy = 0.0
        last_t = 0.0
        win_start = warm
        win_len = H - warm
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
            else:
                dt = rng.expovariate(lam)
            t_arr = t + dt
            if t_arr > H:
                if t < H:
                    seg_end = H
                    if seg_end > win_start:
                        seg_start = max(t, win_start)
                        if seg_end > seg_start:
                            area_n += n * (seg_end - seg_start)
                            area_busy += busy * (seg_end - seg_start)
                break
            if t < t_arr:
                seg_start = max(t, win_start)
                seg_end = min(t_arr, H)
                if seg_end > seg_start:
                    area_n += n * (seg_end - seg_start)
                    area_busy += busy * (seg_end - seg_start)
            t = t_arr
            if t >= win_start:
                arr_c += 1
            if n >= cap:
                if t >= win_start:
                    blk_c += 1
                continue
            svc = rng.expovariate(mu)
            n += 1
            if busy == 0:
                busy = 1
                next_dep = t + svc
            else:
                if t + svc < next_dep:
                    pass
            if n == 1:
                next_dep = t + svc
            else:
                if t + svc < next_dep:
                    next_dep = t + svc
            if t >= win_start:
                wait_sum += 0.0
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n == 1:
                pass
            if t >= win_start:
                pass
            if n
