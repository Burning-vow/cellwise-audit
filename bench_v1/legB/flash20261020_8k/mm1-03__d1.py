import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
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
        area_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait_sum = 0.0
        win_wait_cnt = 0
        win_area_n = 0.0
        win_area_busy = 0.0
        win_time = 0.0
        while True:
            dt_arr = rng.expovariate(lam)
            t_arr = t + dt_arr
            if t_arr >= H:
                if t < H:
                    seg = H - t
                    win_area_n += n * seg
                    win_area_busy += (1 if busy else 0) * seg
                    if t >= warm:
                        win_time += seg
                break
            seg = t_arr - t
            if t >= warm:
                win_area_n += n * seg
                win_area_busy += (1 if busy else 0) * seg
                win_time += seg
            t = t_arr
            svc = rng.expovariate(mu)
            if t >= warm:
                win_arr += 1
            if n == 0:
                n = 1
                busy = True
                next_dep = t + svc
                if t >= warm:
                    win_wait_sum += 0.0
                    win_wait_cnt += 1
            else:
                n += 1
                if t >= warm:
                    win_wait_sum += 0.0
                    win_wait_cnt += 1
            while next_dep <= t_arr and next_dep < H:
                seg2 = next_dep - t
                if t >= warm:
                    win_area_n += n * seg2
                    win_area_busy += (1 if busy else 0) * seg2
                    win_time += seg2
                t = next_dep
                n -= 1
                if t >= warm:
                    win_dep += 1
                if n > 0:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
                else:
                    busy = False
                    next_dep = float('inf')
        if win_time <= 0:
            win_time = 1e-9
        L = win_area_n / win_time
        bf = win_area_busy / win_time
        W = L / (win_dep / win_time) if win_dep > 0 else 0.0
        pw = 1.0 - bf
        pl = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        arrs.append(win_arr)
        deps.append(win_dep)
        blks.append(win_blk)
    ns = len(per_L)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    pl = sum(per_pl) / ns
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    win = warm if False else (H - warm)
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': pw,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
