import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_waitn = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        servers = []
        queue = []
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        wait_n = 0
        win_start = warm
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait = 0.0
        win_waitn = 0
        last_t = 0.0
        next_arr = rng.expovariate(lam)
        while t < H:
            dt = next_arr - t
            if dt > 0:
                if t >= win_start:
                    win_area += n * dt
                    win_busy += busy * dt
                elif t + dt > win_start:
                    frac = (t + dt - win_start)
                    win_area += n * frac
                    win_busy += busy * frac
                t = next_arr
            if t >= H:
                break
            arr += 1
            if t >= win_start:
                win_arr += 1
            svc = rng.expovariate(mu)
            cust = {'arr': t, 'svc': svc}
            if busy < c:
                busy += 1
                servers.append(cust)
                if t >= win_start:
                    win_wait += 0.0
                    win_waitn += 1
            else:
                blk += 1
                if t >= win_start:
                    win_blk += 1
            next_arr = t + rng.expovariate(lam)
            while servers:
                fin = min(x['arr'] + x['svc'] for x in servers)
                if fin <= next_arr and fin <= H:
                    if fin >= win_start:
                        win_area += n * (fin - t)
                        win_busy += busy * (fin - t)
                    t = fin
                    done = [x for x in servers if x['arr'] + x['svc'] <= fin + 1e-12]
                    for d in done:
                        servers.remove(d)
                        busy -= 1
                        dep += 1
                        if fin >= win_start:
                            win_dep += 1
                            win_wait += fin - d['arr']
                            win_waitn += 1
                    if queue and busy < c:
                        q = queue.pop(0)
                        busy += 1
                        servers.append(q)
                else:
                    break
        per_L.append(win_area / max(1e-9, H - win_start))
        per_W.append(win_wait / max(1, win_waitn))
        per_bf.append(win_busy / max(1e-9, H - win_start) / c)
        per_pl.append(win_blk / max(1, win_arr))
        per_pw.append(win_waitn / max(1, win_arr))
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_wait += win_wait
        tot_waitn += win_waitn
        tot_win += (H - win_start)

    L = tot_area / max(1e-9, tot_win)
    W = tot_wait / max(1, tot_waitn)
    busy_frac = tot_busy / max(1e-9, tot_win) / c
    win_len = tot_win / len(seeds)
    dep_rate = tot_dep / max(1e-9, tot_win) * 60.0
    lam_eff = tot_arr / max(1e-9, tot_win) * 60.0
    p_loss = tot_blk / max(1, tot_arr)
    p_wait = tot_waitn / max(1, tot_arr)

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_len,
        'arr': tot_arr / len(seeds), 'blk': tot_blk / len(seeds),
        'busy_util': busy_frac, 'busy_occupied': busy_frac,
        'dep': tot_dep / len(seeds), 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
