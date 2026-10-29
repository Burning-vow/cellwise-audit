import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 14.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_L = tot_W = tot_busy = tot_pw = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr_times = []
        svc = {}
        area_n = 0.0
        area_q = 0.0
        area_busy = 0.0
        wsum = 0.0
        wcnt = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        pw_cnt = 0
        arr_win = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                nt = t + dt
            else:
                dt = rng.expovariate(lam + busy * mu)
                nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_q += len(queue) * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_q += len(queue) * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / (lam + busy * mu):
                arr_c += 1
                if t >= warm:
                    arr_win += 1
                st = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    svc[t] = st
                    if t >= warm:
                        wsum += st
                        wcnt += 1
                else:
                    queue.append((t, st))
                    if t >= warm:
                        pw_cnt += 1
            else:
                busy -= 1
                if t >= warm:
                    dep_c += 1
                if queue:
                    at, st = queue.pop(0)
                    busy += 1
                    svc[t] = st
                    if t >= warm:
                        wsum += (t - at) + st
                        wcnt += 1
        win = H - warm
        L = area_n / win
        W = wsum / wcnt if wcnt else 0.0
        bf = area_busy / win / c
        pw = pw_cnt / arr_win if arr_win else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(0.0); pPW.append(pw)
        tot_arr += arr_win
        tot_dep += dep_c
        tot_blk += 0
        tot_L += L
        tot_W += W
        tot_busy += bf
        tot_pw += pw
    ns = len(seeds)
    out = {
        'L': tot_L / ns,
        'W': tot_W / ns,
        'busy_frac': tot_busy / ns,
        'busy_util': tot_busy / ns,
        'busy_occupied': tot_busy / ns,
        'p_wait': tot_pw / ns,
        'p_loss': 0.0,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns,
        'dep': tot_dep / ns,
        'blk': tot_blk / ns,
        'dep_rate': (tot_dep / ns) / win * 60.0,
        'lam_eff': lam * 60.0,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
