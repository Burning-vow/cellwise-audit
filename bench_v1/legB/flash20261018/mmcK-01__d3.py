import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_waited = 0.0
    tot_dep_w = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_cnt = 0
        last = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t < H:
                        if t < warm:
                            seg = max(0.0, min(H, warm) - t)
                            areaN += seg * n
                            areaB += seg * busy
                        else:
                            areaN += dt * n
                            areaB += dt * busy
                    t = H
                    break
                dt = next_arr - t
                if t < warm:
                    seg = max(0.0, min(next_arr, warm) - t)
                    areaN += seg * n
                    areaB += seg * busy
                if next_arr > warm:
                    areaN += (next_arr - max(t, warm)) * n
                    areaB += (next_arr - max(t, warm)) * busy
                t = next_arr
                if t >= warm:
                    arr_w += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if busy < c:
                        busy += 1
                        st, sd = queue.pop(0)
                        queue.insert(0, (st, sd))
                        queue = queue[1:]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
                        queue.append((t, svc))
                        queue = queue[:-1]
