import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
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
    tot_wait = 0.0
    tot_served = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = t + rng.expovariate(lam)
        dep_t = float('inf')
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        area_wait = 0.0
        last = 0.0
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_wait = 0
        w_served = 0
        w_busy = 0.0
        w_util = 0.0
        w_area_n = 0.0
        w_area_wait = 0.0
        while True:
            nxt = min(arr_t, dep_t)
            if nxt > H:
                dt = H - last
                if last >= warm:
                    w_area_n += n * dt
                    w_area_wait += n * dt
                    if busy:
                        w_busy += dt
                        w_util += dt
                break
            dt = nxt - last
            if last >= warm:
                w_area_n += n * dt
                w_area_wait += n * dt
                if busy:
                    w_busy += dt
                    w_util += dt
            last = nxt
            if arr_t <= dep_t:
                t = arr_t
                if last >= warm:
                    w_arr += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        rem = svc
                        dep_t = t + rem
                else:
                    if last >= warm:
                        w_blk += 1
                arr_t = t + rng.expovariate(lam)
            else:
                t = dep_t
                if last >= warm:
                    w_dep += 1
                    w_served += 1
                n -= 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    rem = svc
                    dep_t = t + rem
                else:
                    busy = False
                    dep_t = float('inf')
        win = H - warm
        Ls = w_area_n / win if win > 0 else 0.0
        Ws = (w_area_wait / w_served) if w_served > 0 else 0.0
        bfs = w_busy / win if win > 0 else 0.0
        pls = w_blk / w_arr if w_arr > 0 else 0.0
        pws = w_wait / w_arr if w_arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += w_arr
        tot_dep += w_dep
        tot_blk += w_blk
        tot_busy += w_busy
        tot_util += w_util
        tot_wait += w_wait
        tot_served += w_served
    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = (tot_util / ns) / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
