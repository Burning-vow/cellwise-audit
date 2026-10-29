import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 10.0
    mu = 10.0
    if a.pert == 'lam_up':
        lam = 12.0
    elif a.pert == 'mu_up':
        mu = 12.0
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    per_bu = []
    per_bo = []
    per_arr = []
    per_dep = []
    per_blk = []
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr_times = []
        dep_times = []
        blk_count = 0
        area_L = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                t_next = t + dt
            else:
                dt = rng.expovariate(lam + busy * mu)
                t_next = t + dt
            if t_next > H:
                if t < H:
                    area_L += n * (H - t)
                    area_busy += busy * (H - t)
                    area_occ += (1.0 if n > 0 else 0.0) * (H - t)
                break
            area_L += n * (t_next - t)
            area_busy += busy * (t_next - t)
            area_occ += (1.0 if n > 0 else 0.0) * (t_next - t)
            t = t_next
            if rng.random() < lam / (lam + busy * mu):
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_win += 1
                if n < c:
                    n += 1
                    busy += 1
                    dep_t = t + svc
                    queue.append((dep_t, svc, t))
                    if t >= warm:
                        wait_sum += svc
                        wait_cnt += 1
                else:
                    if t >= warm:
                        blk_win += 1
                    blk_count += 1
            else:
                busy -= 1
                n -= 1
                if queue:
                    queue.pop(0)
                if t >= warm:
                    dep_win += 1
                if n > 0 and busy < c:
                    busy += 1
                    svc = rng.expovariate(mu)
                    dep_t = t + svc
                    queue.append((dep_t, svc, t))
                    if t >= warm:
                        wait_sum += svc
                        wait_cnt += 1
        win = H - warm
        L = area_L / H
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / H / c
        bu = area_busy / H / c
        bo = area_occ / H
        pl = blk_win / arr_win if arr_win > 0 else 0.0
        pw = pl
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        per_bu.append(bu)
        per_bo.append(bo)
        per_arr.append(arr_win)
        per_dep.append(dep_win)
        per_blk.append(blk_win)
    nseeds = len(per_L)
    L = sum(per_L) / nseeds
    W = sum(per_W) / nseeds
    bf = sum(per_bf) / nseeds
    pl = sum(per_pl) / nseeds
    pw = sum(per_pw) / nseeds
    bu = sum(per_bu) / nseeds
    bo = sum(per_bo) / nseeds
    arr = sum(per_arr) / nseeds
    dep = sum(per_dep) / nseeds
    blk = sum(per_blk) / nseeds
    win = H - warm
    dep_rate = dep / win
    lam_eff = arr / win
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bu,
        'busy_occupied': bo,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
