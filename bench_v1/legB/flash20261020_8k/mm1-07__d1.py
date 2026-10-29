import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
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
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        area_n = 0.0
        area_b = 0.0
        win_area_n = 0.0
        win_area_b = 0.0
        win_time = 0.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_wait_cnt = 0
        last = 0.0
        queue = []
        server_busy = False
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        while t < H:
            dt = min(next_arr, next_dep) - t
            if dt > 0:
                if t >= warm:
                    win_area_n += n * dt
                    win_area_b += (1 if server_busy else 0) * dt
                    win_time += dt
                area_n += n * dt
                area_b += (1 if server_busy else 0) * dt
                t += dt
            if next_arr <= next_dep:
                n_arr += 1
                if t >= warm:
                    win_arr += 1
                n += 1
                svc = rng.expovariate(mu)
                queue.append(svc)
                next_arr = t + rng.expovariate(lam)
                if not server_busy:
                    server_busy = True
                    svc0 = queue.pop(0)
                    next_dep = t + svc0
                    if t >= warm:
                        win_wait += 0.0
                        win_wait_cnt += 1
            else:
                n_dep += 1
                if t >= warm:
                    win_dep += 1
                n -= 1
                if queue:
                    svc0 = queue.pop(0)
                    next_dep = t + svc0
                    if t >= warm:
                        win_wait += 0.0
                        win_wait_cnt += 1
                else:
                    server_busy = False
                    next_dep = float('inf')
        if win_time <= 0:
            win_time = 1e-9
        L = win_area_n / win_time
        bf = win_area_b / win_time
        W = L / (win_dep / win_time) if win_dep > 0 else 0.0
        pw = 1.0 if win_wait_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        arrs.append(win_arr)
        deps.append(win_dep)
        blks.append(win_blk)
    ns = len(per_L)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    win = warm if False else (H - warm)
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = lam
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
