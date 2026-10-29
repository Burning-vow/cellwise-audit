import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu1 *= 1.25
        mu2 *= 1.25
    elif a.pert == 'c_up':
        c *= 1.25
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
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_area = 0.0
    tot_win = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        busy1 = False
        busy2 = False
        rem1 = 0.0
        rem2 = 0.0
        nxt_arr = rng.expovariate(lam)
        area = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        busy_t = 0.0
        wait_sum = 0.0
        served = 0
        last_t = 0.0
        while t < H:
            cand = [nxt_arr]
            if busy1:
                cand.append(t + rem1)
            if busy2:
                cand.append(t + rem2)
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            n = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
            if t >= warm:
                area += n * dt
                if busy1 or busy2:
                    busy_t += dt
            t = nt
            if t >= H:
                break
            if abs(t - nxt_arr) < 1e-12:
                if rng.random() < c:
                    svc = rng.expovariate(mu1)
                    q1.append(svc)
                    arr_c += 1
                else:
                    blk_c += 1
                nxt_arr = t + rng.expovariate(lam)
            if busy1 and abs(t - (last_t + rem1)) < 1e-12:
                pass
            if busy1:
                rem1 -= dt
                if rem1 <= 1e-12:
                    busy1 = False
                    svc2 = rng.expovariate(mu2)
                    q2.append(svc2)
            if busy2:
                rem2 -= dt
                if rem2 <= 1e-12:
                    busy2 = False
                    dep_c += 1
            if not busy1 and q1:
                svc = q1.pop(0)
                busy1 = True
                rem1 = svc
            if not busy2 and q2:
                svc = q2.pop(0)
                busy2 = True
                rem2 = svc
            last_t = t
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (lam * c) * 60.0 if lam * c > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        pl = blk_c / (arr_c + blk_c) if (arr_c + blk_c) > 0 else 0.0
        pw = 1.0 if (arr_c > 0 and bf > 0) else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += busy_t
        tot_area += area
        tot_win += win
        tot_served += served
    n = a.seeds
    L = sum(per_L) / n if n else 0.0
    W = sum(per_W) / n if n else 0.0
    bf = sum(per_bf) / n if n else 0.0
    pl = sum(per_pl) / n if n else 0.0
    pw = sum(per_pw) / n if n else 0.0
    win = tot_win / n if n else 0.0
    arr = tot_arr / n if n else 0.0
    dep = tot_dep / n if n else 0.0
    blk = tot_blk / n if n else 0.0
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = lam * c
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
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
