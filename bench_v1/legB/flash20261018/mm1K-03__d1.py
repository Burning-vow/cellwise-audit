import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wsum = 0.0
        wcnt = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_time = 0.0
        win_start = warm
        last_t = 0.0
        while t < H:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                nt = H
            if nt > t:
                if nt > win_start:
                    seg_start = max(t, win_start)
                    seg = nt - seg_start
                    if seg > 0:
                        area_n += n * seg
                        area_busy += (1.0 if busy else 0.0) * seg
                        area_occ += (1.0 if n > 0 else 0.0) * seg
                        if busy:
                            busy_time += seg
                t = nt
            if t >= H:
                break
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t > win_start:
                        dep_w += 1
                    if queue:
                        cust = queue.pop(0)
                        cust['start'] = t
                        rem = cust['svc']
                        busy = True
                        n += 1
                        if t > win_start:
                            wsum += t - cust['arr']
                            wcnt += 1
            else:
                if n < K:
                    svc = rng.expovariate(mu)
                    cust = {'arr': t, 'svc': svc}
                    if t > win_start:
                        arr_w += 1
                    if n == 0:
                        busy = True
                        rem = svc
                        n += 1
                        if t > win_start:
                            wsum += 0.0
                            wcnt += 1
                    else:
                        queue.append(cust)
                        n += 1
                else:
                    if t > win_start:
                        arr_w += 1
                        blk_w += 1
        win = H - warm
        if win <= 0:
            win = H
        L = area_n / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_occ / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wcnt / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
    ns = a.seeds
    win = H - warm
    L = sum(per_L) / ns if ns > 0 else 0.0
    W = sum(per_W) / ns if ns > 0 else 0.0
    busy_frac = sum(per_bf) / ns if ns > 0 else 0.0
    p_loss = sum(per_pl) / ns if ns > 0 else 0.0
    p_wait = sum(per_pw) / ns if ns > 0 else 0.0
    arr = tot_arr / ns if ns > 0 else 0.0
    dep = tot_dep / ns if ns > 0 else 0.0
    blk = tot_blk / ns if ns > 0 else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = busy_frac
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
