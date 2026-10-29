import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 6.0
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
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_busy = 0.0
        arr = 0; dep = 0; blk = 0
        wait_sum = 0.0; wait_cnt = 0
        # event list: (time, type, payload)
        # type 0 arrival, 1 departure
        events = []
        t_next_arr = rng.expovariate(lam)
        events.append((t_next_arr, 0, None))
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, payload = events.pop(0)
            if te > H:
                # integrate remaining
                dt = H - t
                area_n += n * dt
                area_busy += (1 if n > 0 else 0) * dt
                t = H
                break
            dt = te - t
            area_n += n * dt
            area_busy += (1 if n > 0 else 0) * dt
            t = te
            if typ == 0:
                arr += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    events.append((t + svc, 1, svc))
                else:
                    blk += 1
                t_next_arr = t + rng.expovariate(lam)
                events.append((t_next_arr, 0, None))
            else:
                n -= 1
                dep += 1
        # window stats
        win = H - warm
        # recompute window integrals by re-simulating? Instead approximate: we integrated whole horizon.
        # Better: track window separately. Redo with window tracking.
        # We'll do a second pass properly.
        rng = random.Random(s)
        t = 0.0; n = 0
        area_n_w = 0.0; area_busy_w = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0
        wait_sum_w = 0.0; wait_cnt_w = 0
        events = [(rng.expovariate(lam), 0, None)]
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, payload = events.pop(0)
            if te > H:
                if t < H:
                    dt = H - max(t, warm)
                    if dt > 0:
                        area_n_w += n * dt
                        area_busy_w += (1 if n > 0 else 0) * dt
                t = H
                break
            # integrate from t to te, but only window part
            lo = max(t, warm); hi = te
            if hi > lo:
                dt = hi - lo
                area_n_w += n * dt
                area_busy_w += (1 if n > 0 else 0) * dt
            t = te
            in_win = (t >= warm)
            if typ == 0:
                if in_win: arr_w += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    events.append((t + svc, 1, svc))
                else:
                    if in_win: blk_w += 1
                events.append((t + rng.expovariate(lam), 0, None))
            else:
                n -= 1
                if in_win: dep_w += 1
        L = area_n_w / win if win > 0 else 0.0
        bf = area_busy_w / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 1.0 - (dep_w / arr_w) if arr_w > 0 else 0.0
        # W via Little: L = lam_eff * W, lam_eff = dep_w/win (per minute)
        lam_eff = dep_w / win if win > 0 else 0.0
        W = L / lam_eff if lam_eff > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf); per_pl.append(pl); per_pw.append(pw)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = H - warm
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = dep_rate
    busy_util = bf  # approximation: E[min(N,c)]/c; for single server equals busy_frac
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
