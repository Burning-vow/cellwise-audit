import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 5.0
    c = 3
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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait_n = 0.0
    tot_wait_t = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        win_n = 0.0
        win_busy = 0.0
        win_util = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait_n = 0
        win_wait_t = 0.0
        last = 0.0
        while t < H:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                nt = H
            if nt > t:
                if t >= warm:
                    seg = nt - t
                    area_n += n * seg
                    area_busy += (1 if n > 0 else 0) * seg
                    area_util += min(n, c) * seg
                t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append(svc)
                    if t >= warm:
                        win_arr += 1
                else:
                    if t >= warm:
                        win_arr += 1
                        win_blk += 1
            else:
                if busy > 0:
                    busy -= 1
                    if queue:
                        svc = queue.pop(0)
                        if t >= warm:
                            win_dep += 1
                            win_wait_n += 1
                            win_wait_t += svc
                        busy += 1
                        n -= 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        util = area_util / win if win > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_wait_n / win_arr if win_arr > 0 else 0.0
        W = win_wait_t / win_wait_n if win_wait_n > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_busy += area_busy
        tot_util += area_util
        tot_wait_n += win_wait_n
        tot_wait_t += win_wait_t
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
    busy_util = (tot_util / tot_win) / c if tot_win > 0 else 0.0
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': tot_win / ns,
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
