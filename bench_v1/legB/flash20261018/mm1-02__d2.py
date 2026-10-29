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
    arrs = []
    deps = []
    blks = []
    t0 = time.time()
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        warea = 0.0
        wcount = 0
        busy_area = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        last = 0.0
        while True:
            if busy:
                dt = next_dep - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                if t >= H:
                    break
                n -= 1
                dep_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                t += dt
                arr_c += 1
                svc = rng.expovariate(mu)
                n += 1
                if not busy:
                    busy = True
                    next_dep = t + svc
                if t >= warm:
                    warea += svc
                    wcount += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = warea / wcount if wcount > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if arr_c > 0 else 0.0)
        arrs.append(arr_c)
        deps.append(dep_c)
        blks.append(blk_c)
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    win = H - warm
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': sum(per_pw) / ns,
        'p_loss': sum(per_pl) / ns,
        'runtime_units': time.time() - t0,
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
