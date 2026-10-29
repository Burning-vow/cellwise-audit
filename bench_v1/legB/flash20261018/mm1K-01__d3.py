import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        area_n = 0.0
        area_busy = 0.0
        area_wait = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0.0
        wait_cnt = 0
        last = 0.0
        events = []
        while True:
            dt = rng.expovariate(lam)
            t_next = t + dt
            if t_next > H:
                break
            if t < warm and t_next > warm:
                area_n += n * (warm - t)
                area_busy += busy * (warm - t)
                t = warm
            if t >= warm:
                area_n += n * (t_next - t)
                area_busy += busy * (t_next - t)
            t = t_next
            if n < cap:
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if n == 0:
                    busy = 1
                    start = t
                else:
                    start = None
                events.append([t + svc, svc, t, start])
                n += 1
            else:
                if t >= warm:
                    blk_w += 1
        if t < H:
            if t < warm:
                area_n += n * (warm - t)
                area_busy += busy * (warm - t)
                t = warm
            area_n += n * (H - t)
            area_busy += busy * (H - t)
        events.sort(key=lambda e: e[0])
        cur = warm
        for e in events:
            end = e[0]
            if end <= warm:
                continue
            if e[3] is not None:
                st = e[3]
                if st < warm:
                    st = warm
                if end > st:
                    area_wait += (end - st)
                    wait_w += (end - st)
                    wait_cnt += 1
            if end > H:
                end = H
            if end > cur:
                cur = end
            if end >= warm:
                dep_w += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = area_wait / dep_w if dep_w > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        pl = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        pw = wait_cnt / dep_w if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
