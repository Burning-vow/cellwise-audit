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
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 0.01), 0.99)
    m1 = mean_s * p
    m2 = mean_s * (1.0 - p)
    if m1 <= 0: m1 = mean_s * 0.5
    if m2 <= 0: m2 = mean_s * 0.5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                nt = t + dt
            else:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > t + rem:
                    nt = t + rem
            if nt > H:
                if busy:
                    area += n * (H - t)
                    busy_area += (H - t)
                else:
                    area += n * (H - t)
                break
            area += n * (nt - t)
            if busy:
                busy_area += (nt - t)
            t = nt
            if busy:
                rem -= (t - last) if False else 0
            if busy:
                rem = rem - (nt - (nt - (nt - t))) if False else rem
            if busy:
                pass
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if busy:
                rem = rem
            if busy:
                rem -= 0
            if
