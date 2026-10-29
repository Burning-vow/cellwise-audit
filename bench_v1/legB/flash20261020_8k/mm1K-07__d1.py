import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
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
    tot_util = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_depn = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_cnt = 0
        dep_cnt = 0
        last = 0.0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                area_n += n * (H - t)
                area_busy += busy * (H - t)
                area_util += min(n, 1) * (H - t)
                t = H
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            area_util += min(n, 1) * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                if t >= warm:
                    arr_w += 1
                if n < K:
                    n += 1
                    if n == 1:
                        busy = 1
                    svc = rng.expovariate(mu)
                    if t >= warm:
                        wait_sum += svc
                        wait_cnt += 1
                else:
                    if t >= warm:
                        blk_w += 1
            else:
                n -= 1
                if n == 0:
                    busy = 0
                if t >= warm:
                    dep_w += 1
                    dep_cnt += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_util / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_cnt / arr_w if arr_w > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy += bf
        tot_util += bu
        tot_wait += wait_sum
        tot_waitn += wait_cnt
        tot_depn += dep_cnt
    ns = a.seeds
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
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = tot_util / ns
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
