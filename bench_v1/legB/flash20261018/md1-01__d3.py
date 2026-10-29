import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = tot_wait_n = 0.0
    tot_serv = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_dep = None
        queue = []
        arr = dep = blk = 0
        area = 0.0
        busy_area = 0.0
        wait_sum = 0.0
        wait_n = 0
        serv_sum = 0.0
        last = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait = 0.0
        win_wait_n = 0
        win_serv = 0.0
        while True:
            if next_dep is not None:
                dt = next_dep - t
            else:
                dt = float('inf')
            if dt == float('inf'):
                nxt = t + rng.expovariate(lam)
            else:
                nxt = min(next_dep, t + rng.expovariate(lam))
            if nxt > H:
                if t < H:
                    d = H - t
                    if t >= warm:
                        win_area += n * d
                        win_busy += (1 if busy else 0) * d
                    area += n * d
                    busy_area += (1 if busy else 0) * d
                break
            d = nxt - t
            if t >= warm:
                win_area += n * d
                win_busy += (1 if busy else 0) * d
            area += n * d
            busy_area += (1 if busy else 0) * d
            t = nxt
            if next_dep is not None and abs(t - next_dep) < 1e-12:
                n -= 1
                busy = 0
                dep += 1
                if t >= warm:
                    win_dep += 1
                if queue:
                    cust = queue.pop(0)
                    w = t - cust['arr']
                    wait_sum += w
                    wait_n += 1
                    serv_sum += cust['svc']
                    if t >= warm:
                        win_wait += w
                        win_wait_n += 1
                        win_serv += cust['svc']
                    busy = 1
                    n += 1
                    next_dep = t + cust['svc']
                else:
                    next_dep = None
            else:
                arr += 1
                if t >= warm:
                    win_arr += 1
                svc = rng.expovariate(mu)
                if busy == 0 and next_dep is None:
                    busy = 1
                    n += 1
                    serv_sum += svc
                    if t >= warm:
                        win_serv += svc
                    next_dep = t + svc
                else:
                    queue.append({'arr': t, 'svc': svc})
                    n += 1
        w = H - warm
        L = win_area / w if w > 0 else 0.0
        W = (win_wait / win_wait_n) if win_wait_n > 0 else 0.0
        bf = win_busy / w if w > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_wait_n / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_win += w
        tot_wait += win_wait
        tot_wait_n += win_wait_n
        tot_serv += win_serv

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_wait_n if tot_wait_n > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / len(seeds)
    dep_avg = tot_dep / len(seeds)
    blk_avg = tot_blk / len(seeds)
    dep_rate = dep_avg / (tot_win / len(seeds)) if tot_win > 0 else 0.0
    lam_eff = arr_avg / (tot_win / len(seeds)) if tot_win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': bf,
        'busy_util': bf, 'busy_occupied': bf,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': tot_win / len(seeds),
        'arr': arr_avg, 'dep': dep_avg, 'blk': blk_avg,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
