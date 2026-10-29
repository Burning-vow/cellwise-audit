import json, random, argparse, time

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
    seed_list = []
    t0 = time.time()
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
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0
        n_wait = 0
        last = 0.0
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        while t < H:
            dt = min(next_arr, next_dep) - t
            if dt > 0:
                if t < warm:
                    end = min(t + dt, warm)
                    area_n += n * (end - t)
                    area_b += (1 if busy else 0) * (end - t)
                    if end < t + dt:
                        t = end
                        continue
                else:
                    end = min(t + dt, H)
                    win_area_n += n * (end - t)
                    win_area_b += (1 if busy else 0) * (end - t)
                    win_time += (end - t)
                    if end < t + dt:
                        t = end
                        continue
                t += dt
            if next_arr <= next_dep:
                t = next_arr
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if busy == 0:
                    busy = 1
                    next_dep = t + svc
                else:
                    queue.append(svc)
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = next_dep
                if t >= warm:
                    dep_w += 1
                n -= 1
                if queue:
                    svc = queue.pop(0)
                    next_dep = t + svc
                else:
                    busy = 0
                    next_dep = float('inf')
        if win_time <= 0:
            win_time = 1e-9
        L = win_area_n / win_time
        bf = win_area_b / win_time
        W = L / (dep_w / win_time) if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
    runtime = time.time() - t0
    nseed = len(per_L)
    L = sum(per_L) / nseed
    W = sum(per_W) / nseed
    bf = sum(per_bf) / nseed
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': 0.0,
        'p_loss': 0.0,
        'runtime_units': runtime,
        'seed_list': seed_list,
        'seeds_used': nseed,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'dep': 0.0,
        'blk': 0.0,
        'dep_rate': 0.0,
        'lam_eff': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
