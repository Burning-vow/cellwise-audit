import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
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
        area_b = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_wait_n = 0
        win_busy = 0.0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_n += n * seg
                        area_b += (1 if busy else 0) * seg
                        win_busy += (1 if busy else 0) * seg
                    elif nt > warm:
                        seg2 = H - warm
                        area_n += n * seg2
                        area_b += (1 if busy else 0) * seg2
                        win_busy += (1 if busy else 0) * seg2
                break
            if t >= warm:
                area_n += n * dt
                area_b += (1 if busy else 0) * dt
                win_busy += (1 if busy else 0) * dt
            elif nt > warm:
                seg = nt - warm
                area_n += n * seg
                area_b += (1 if busy else 0) * seg
                win_busy += (1 if busy else 0) * seg
            t = nt
            if busy and t >= next_dep - 1e-12:
                n -= 1
                if t >= warm:
                    win_dep += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
            else:
                if t >= warm:
                    win_arr += 1
                if n == 0:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                    busy = True
                    n = 1
                else:
                    n += 1
        win_len = H - warm
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_b / win_len if win_len > 0 else 0.0
        W = L / (win_dep / win_len) if win_dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(bf)
        arrs.append(win_arr)
        deps.append(win_dep)
        blks.append(win_blk)
    ns = len(per_L)
    Lm = sum(per_L) / ns
    Wm = sum(per_W) / ns
    bfm = sum(per_bf) / ns
    depm = sum(deps) / ns
    win_len = H - warm
    dep_rate = depm / win_len * 60.0 if win_len > 0 else 0.0
    out = {
        'L': Lm,
        'W': Wm,
        'busy_frac': bfm,
        'p_wait': bfm,
        'runtime_units': 'minute',
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_len,
        'arr': sum(arrs) / ns,
        'blk': sum(blks) / ns,
        'busy_util': bfm,
        'busy_occupied': bfm,
        'dep': depm,
        'dep_rate': dep_rate,
        'lam_eff': dep_rate / 60.0,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
