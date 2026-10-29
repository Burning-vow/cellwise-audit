import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    arrs = []
    deps = []
    blks = []
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0
        win_served = 0
        win_area_n = 0.0
        win_area_busy = 0.0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        win_area_n += n * seg
                        win_area_busy += (1 if busy else 0) * seg
                    elif t + seg > warm:
                        seg2 = t + seg - warm
                        win_area_n += n * seg2
                        win_area_busy += (1 if busy else 0) * seg2
                break
            if t >= warm:
                win_area_n += n * dt
                win_area_busy += (1 if busy else 0) * dt
            elif t + dt > warm:
                seg2 = t + dt - warm
                win_area_n += n * seg2
                win_area_busy += (1 if busy else 0) * seg2
            t += dt
            if busy:
                n -= 1
                busy = False
                next_dep = float('inf')
                if t >= warm:
                    win_dep += 1
            else:
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    win_arr += 1
                if n == 1:
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        win_served += 1
                        win_wait += 0
                else:
                    if t >= warm:
                        win_blk += 1
        win_len = H - warm
        L = win_area_n / win_len if win_len > 0 else 0.0
        bf = win_area_busy / win_len if win_len > 0 else 0.0
        W = L / (win_dep / win_len) if win_dep > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        arrs.append(win_arr)
        deps.append(win_dep)
        blks.append(win_blk)
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    win_len = H - warm
    dep_rate = dep / win_len * 60.0
    lam_eff = arr / win_len * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_len,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': bf,
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

if __name__ == "__main__":
    main()
