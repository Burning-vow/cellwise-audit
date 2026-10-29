import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 3
    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4
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
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        wait_win = 0
        arr_all = 0
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
                    area_busy += busy * (H - t)
                    area_q += len(queue) * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            area_q += len(queue) * (nt - t)
            t = nt
            if rng.random() < lam / (lam + busy * mu):
                arr_all += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_win += 1
                if busy < c:
                    busy += 1
                    servers.append((t + svc, svc))
                    if t >= warm:
                        wait_win += 0
                        wait_sum += svc
                        wait_cnt += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        blk_win += 0
                n += 1
            else:
                servers.sort()
                endt, svc = servers.pop(0)
                busy -= 1
                n -= 1
                if t >= warm:
                    dep_win += 1
                if queue:
                    at, qsvc = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        wait_sum += w + qsvc
                        wait_cnt += 1
                    busy += 1
                    servers.append((t + qsvc, qsvc))
                    n += 1
        win = H - warm
        L = area_n / win
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / (c * win)
        pw = 1.0 - (1.0 - lam / (c * mu)) if lam < c * mu else 1.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    win = H - warm
    dep_rate = (tot_dep / ns) / win * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': list(range(a.seed_start, a.seed_start + ns)),
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns,
        'blk': tot_blk / ns,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': tot_dep / ns,
        'dep_rate': dep_rate,
        'lam_eff': lam * 60.0,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
