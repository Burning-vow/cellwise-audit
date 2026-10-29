import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
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
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        arr = 0
        dep = 0
        blk = 0
        area_n = 0.0
        area_busy = 0.0
        area_wait = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        win_start = warm
        win_len = H - warm
        # event list: (time, type, payload)
        # type 0 arrival, 1 departure
        next_arr = rng.expovariate(lam)
        events = [(next_arr, 0, None)]
        # queue of (arrival_time, service_time)
        q = []
        # schedule departures as they start service
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, payload = events.pop(0)
            if te > H:
                break
            # integrate areas up to te
            dt = te - t
            if t >= win_start or te > win_start:
                lo = max(t, win_start)
                hi = min(te, H)
                if hi > lo:
                    d = hi - lo
                    area_n += n * d
                    area_busy += (1 if busy else 0) * d
                    area_wait += len(q) * d
            t = te
            if typ == 0:
                arr += 1
                st = rng.expovariate(mu)
                if n < cap:
                    n += 1
                    if busy == 0:
                        busy = 1
                        events.append((t + st, 1, None))
                    else:
                        q.append((t, st))
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
                events.append((next_arr, 0, None))
            else:
                dep += 1
                n -= 1
                if q:
                    at, st = q.pop(0)
                    wait_sum += t - at
                    wait_cnt += 1
                    events.append((t + st, 1, None))
                else:
                    busy = 0
        # final integration to H
        if t < H:
            lo = max(t, win_start)
            hi = H
            if hi > lo:
                d = hi - lo
                area_n += n * d
                area_busy += (1 if busy else 0) * d
                area_wait += len(q) * d
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_busy / win_len if win_len > 0 else 0.0
        W = (area_wait / win_len) / (lam * (1 - blk / arr)) if arr > 0 and blk < arr else 0.0
        # W via Little: L = lam_eff * W -> W = L / lam_eff
        lam_eff = (arr - blk) / win_len if win_len > 0 else 0.0
        W = L / lam_eff if lam_eff > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = wait_cnt / (arr - blk) if arr > blk else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    win_len = H - warm
    dep_rate = dep_avg / win_len if win_len > 0 else 0.0
    busy_util = L / cap if cap > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win_len,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': (arr_avg - blk_avg) / win_len if win_len > 0 else 0.0,
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
