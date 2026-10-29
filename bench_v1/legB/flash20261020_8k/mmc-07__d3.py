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
        wait_win_cnt = 0
        last = 0.0
        while True:
            if busy < c:
                dt = rng.expovariate(lam)
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            if nt > warm:
                area_n += n * (nt - t)
                area_busy += busy * (nt - t)
                area_q += len(queue) * (nt - t)
            t = nt
            n += 1
            svc = rng.expovariate(mu)
            if t > warm:
                arr_win += 1
            if busy < c:
                busy += 1
                servers.append((t + svc, svc))
                if t > warm:
                    wait_win += 0.0
                    wait_win_cnt += 1
            else:
                queue.append((t, svc))
                if t > warm:
                    wait_win_cnt += 1
            while servers and servers[0][0] <= t:
                servers.pop(0)
                busy -= 1
                if t > warm:
                    dep_win += 1
                if queue:
                    at, sv = queue.pop(0)
                    w = t - at
                    if t > warm:
                        wait_win += w
                    busy += 1
                    servers.append((t + sv, sv))
                    servers.sort()
        if t > warm:
            area_n += n * (t - warm)
            area_busy += busy * (t - warm)
            area_q += len(queue) * (t - warm)
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        W = (area_n / max(1, arr_win)) * 60.0 if arr_win > 0 else 0.0
        pw = (wait_win_cnt - wait_win_cnt + (wait_win_cnt - (arr_win - wait_win_cnt))) / max(1, arr_win)
        pw = (wait_win_cnt - (arr_win - wait_win_cnt)) / max(1, arr_win)
        pw = max(0.0, min(1.0, pw))
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
    dep_rate = (tot_dep / ns) / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': pw,
        'p_loss': 0.0,
        'runtime_units': H,
        'seed_list': list(range(a.seed_start, a.seed_start + ns)),
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns,
        'dep': tot_dep / ns,
        'blk': tot_blk / ns,
        'dep_rate': dep_rate,
        'lam_eff': lam * 60.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
