import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=20000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
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
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_depw = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = t + rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wsum = 0.0
        wcnt = 0
        waited = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        last = 0.0
        while True:
            if not busy:
                nt = arr_t
            else:
                nt = min(arr_t, t + rem)
            if nt > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                t = H
                break
            dt = nt - t
            if t >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep_c += 1
                    if t >= warm:
                        tot_depw += 1
            if abs(t - arr_t) < 1e-12:
                svc = rng.expovariate(mu)
                arr_c += 1
                if t >= warm:
                    tot_arr += 1
                if n >= 1:
                    blk_c += 1
                    if t >= warm:
                        tot_blk += 1
                else:
                    n += 1
                    busy = True
                    rem = svc
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                        waited += 1
                arr_t = t + rng.expovariate(lam)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = wsum / wcnt if wcnt > 0 else 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_c / arr_c if arr_c > 0 else 0.0
        pws = waited / arr_c if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_area += area
        tot_busy += busy_area
        tot_wait += wsum
        tot_waited += wcnt
    ns = len(per_L)
    win = H - warm
    L = sum(per_L) / ns if ns else 0.0
    W = sum(per_W) / ns if ns else 0.0
    busy_frac = sum(per_bf) / ns if ns else 0.0
    p_wait = sum(per_pw) / ns if ns else 0.0
    p_loss = sum(per_pl) / ns if ns else 0.0
    arr = tot_arr / ns if ns else 0.0
    dep = tot_depw / ns if ns else 0.0
    blk = tot_blk / ns if ns else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
