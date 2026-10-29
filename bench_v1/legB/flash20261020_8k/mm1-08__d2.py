import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        dep_wait_sum = 0.0
        while True:
            if busy:
                dt = next_dep - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                if t >= H:
                    break
                n -= 1
                dep_w += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                    t = H
                    break
                t += dt
                if t >= warm:
                    area += n * 0
                arr_w += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        busy_area += 0
                else:
                    pass
                n += 1
                if n == 1 and not busy:
                    busy = True
                    next_dep = t + svc
                if t >= warm:
                    pass
                if n > 1:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n > 0:
                    pass
                if t >= warm:
                    pass
                if n >= 1:
                    pass
                if t >= warm:
                    pass
                if n >
