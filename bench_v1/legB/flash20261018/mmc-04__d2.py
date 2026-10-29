import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0
    mu = 6.0
    c = 2
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    per_bu = []
    per_bo = []
    per_arr = []
    per_dep = []
    per_blk = []

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk_count = 0
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        last_t = 0.0
        events = []
        next_arr = rng.expovariate(lam)
        while True:
            if next_arr <= t:
                pass
            cand = next_arr
            if servers:
                cand = min(cand, min(servers))
            if cand > H:
                break
            dt = cand - t
            if t >= warm:
                area_n += n * dt
                area_busy += busy * dt
                area_q += len(queue) * dt
            t = cand
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                if t >= warm:
                    arr_win += 1
                if busy < c:
                    busy += 1
                    svc = rng.expovariate(mu)
                    servers.append(t + svc)
                    if t >= warm:
                        wait_cnt += 1
                        wait_sum += 0.0
                else:
                    if len(queue) < 100000:
                        svc = rng.expovariate(mu)
                        queue.append((t, svc))
                        if t >= warm:
                            wait_cnt += 1
                    else:
                        if t >= warm:
                            blk_win += 1
                n = busy + len(queue)
                next_arr = t + rng.expovariate(lam)
            else:
                idx = servers.index(min(servers))
                servers.pop(idx)
                busy -= 1
                if t >= warm:
                    dep_win += 1
                if queue:
                    at, svc = queue.pop(0)
                    if t >= warm:
                        wait_sum += (t - at) + svc
                    servers.append(t + svc)
                    busy += 1
                n = busy + len(queue)
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        pl = blk_win / arr_win if arr_win > 0 else 0.0
        pw = 1.0 - (1.0 - pl) * (1.0 - bf) if arr_win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        per_bu.append(bf)
        per_bo.append(bf)
        per_arr.append(arr_win)
        per_dep.append(dep_win)
        per_blk.append(blk_win)

    ns = len(seeds)
    def avg(x):
        return sum(x) / len(x) if x else 0.0

    L = avg(per_L)
    W = avg(per_W)
    bf = avg(per_bf)
    pl = avg(per_pl)
    pw = avg(per_pw)
    arr = avg(per_arr)
    dep = avg(per_dep)
    blk = avg(per_blk)
    win = H - warm
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': avg(per_bo),
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
