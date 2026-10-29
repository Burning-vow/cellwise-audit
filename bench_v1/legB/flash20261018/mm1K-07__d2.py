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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_occ = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr = 0
        dep = 0
        blk = 0
        wait_sum = 0.0
        served = 0
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        while t < H:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                nt = H
            if nt > win_start:
                seg_start = max(t, win_start)
                seg = nt - seg_start
                if seg > 0:
                    area_n += n * seg
                    area_busy += (1.0 if busy else 0.0) * seg
                    area_occ += (1.0 if n > 0 else 0.0) * seg
            t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                arr += 1
                if n < K:
                    st = rng.expovariate(mu)
                    queue.append(st)
                    n += 1
                    if not busy:
                        busy = True
                        rem = queue.pop(0)
                else:
                    blk += 1
            else:
                rem -= dt
                if rem <= 1e-12:
                    dep += 1
                    served += 1
                    n -= 1
                    if queue:
                        rem = queue.pop(0)
                    else:
                        busy = False
                        rem = 0.0
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_busy / win_len if win_len > 0 else 0.0
        occ = area_occ / win_len if win_len > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 if served > 0 else 0.0
        W = L / (dep / win_len) if dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += bf
        tot_win += win_len
        tot_occ += occ
        tot_served += served
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep_avg / win if win > 0 else 0.0
    busy_util = tot_occ / ns
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': arr_avg / win if win > 0 else 0.0,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': bf,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
