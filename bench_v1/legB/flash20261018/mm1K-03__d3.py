import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cap = 5
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
    tot_occ = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_win = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        dep_t = float('inf')
        arr_t = rng.expovariate(lam)
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wsum = 0.0
        wn = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_c = 0
        waitn_c = 0
        last = 0.0
        while True:
            nxt = min(arr_t, dep_t)
            if nxt > H:
                dt = H - last
                if last >= warm:
                    area_n += n * dt
                    area_busy += (1 if busy else 0) * dt
                    area_occ += min(n, cap) * dt
                break
            dt = nxt - last
            if last >= warm:
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
                area_occ += min(n, cap) * dt
            elif nxt > warm:
                dt2 = nxt - warm
                area_n += n * dt2
                area_busy += (1 if busy else 0) * dt2
                area_occ += min(n, cap) * dt2
            t = nxt
            last = t
            if arr_t <= dep_t:
                arr_c += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        dep_t = t + svc
                    else:
                        pass
                    if n > 1:
                        wait_c += 1
                else:
                    blk_c += 1
                arr_t = t + rng.expovariate(lam)
            else:
                dep_c += 1
                n -= 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    dep_t = t + svc
                else:
                    busy = False
                    dep_t = float('inf')
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_occ / (win * cap) if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_c / arr_c if arr_c > 0 else 0.0
        W = L / (dep_c / win) if dep_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += area_busy
        tot_occ += area_occ
        tot_wait += wait_c
        tot_waitn += waitn_c
        tot_win += win
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    busy_util = tot_occ / (tot_win * cap) if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
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
