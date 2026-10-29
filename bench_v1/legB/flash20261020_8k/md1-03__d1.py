import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    svc = 60.0 / mu
    H = float(a.horizon)
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        in_service = None
        svc_end = None
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_w = dep_w = blk_w = 0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        while t < H:
            if in_service is None and queue:
                cust = queue.pop(0)
                in_service = cust
                svc_end = t + cust['svc']
                busy = 1
                wait_area += (t - cust['arr']) * 0
                wait_n += 1
                wait_area += 0
            nxt = next_arr
            if svc_end is not None and svc_end < nxt:
                nxt = svc_end
            if nxt > H:
                dt = H - t
                if t >= win_start or nxt > win_start:
                    lo = max(t, win_start)
                    hi = H
                    if hi > lo:
                        area += n * (hi - lo)
                        busy_area += busy * (hi - lo)
                t = H
                break
            dt = nxt - t
            if dt > 0:
                lo = max(t, win_start)
                hi = min(nxt, H)
                if hi > lo:
                    area += n * (hi - lo)
                    busy_area += busy * (hi - lo)
            t = nxt
            if t == next_arr:
                cust = {'arr': t, 'svc': svc}
                if n < c:
                    n += 1
                    if in_service is None:
                        in_service = cust
                        svc_end = t + cust['svc']
                        busy = 1
                        if t >= win_start:
                            wait_n += 1
                    else:
                        queue.append(cust)
                        if t >= win_start:
                            wait_n += 1
                else:
                    if t >= win_start:
                        blk_w += 1
                if t >= win_start:
                    arr_w += 1
                next_arr = t + rng.expovariate(lam)
            elif svc_end is not None and t == svc_end:
                if t >= win_start:
                    dep_w += 1
                n -= 1
                in_service = None
                svc_end = None
                busy = 0
                if queue:
                    cust = queue.pop(0)
                    in_service = cust
                    svc_end = t + cust['svc']
                    busy = 1
        Ls = area / win_len if win_len > 0 else 0.0
        bf = busy_area / win_len if win_len > 0 else 0.0
        Ws = Ls / (dep_w / win_len) if dep_w > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_n / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_win += win_len

    L = tot_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    W = L / (tot_dep / tot_win) if tot_dep > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    lam_eff = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac / c,
        'busy_occupied': busy_frac,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'seed_list': seed_list,
        'seeds_used': len(seed_list),
        'win': tot_win / len(seed_list) if seed_list else 0.0,
        'arr': tot_arr / len(seed_list) if seed_list else 0.0,
        'dep': tot_dep / len(seed_list) if seed_list else 0.0,
        'blk': tot_blk / len(seed_list) if seed_list else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': sum(per_pw) / len(per_pw) if per_pw else 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
