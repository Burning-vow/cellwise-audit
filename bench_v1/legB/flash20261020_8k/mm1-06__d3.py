import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
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
    arr_tot = 0.0
    dep_tot = 0.0
    blk_tot = 0.0
    win_tot = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_b = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0
        wait_n = 0
        win_start = warm
        win_len = H - warm
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        while t < H:
            if next_arr <= next_dep:
                dt = next_arr - t
                if t >= win_start:
                    area_n += n * dt
                    area_b += (1 if n >= 1 else 0) * dt
                t = next_arr
                if t >= win_start:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    next_dep = t + svc
                else:
                    n += 1
                    queue.append(svc)
                next_arr = t + rng.expovariate(lam)
            else:
                dt = next_dep - t
                if t >= win_start:
                    area_n += n * dt
                    area_b += (1 if n >= 1 else 0) * dt
                t = next_dep
                if t >= win_start:
                    dep_w += 1
                n -= 1
                if n > 0:
                    svc = queue.pop(0)
                    next_dep = t + svc
                else:
                    next_dep = float('inf')
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_b / win_len if win_len > 0 else 0.0
        W = L / (dep_w / win_len) if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(bf)
        arr_tot += arr_w
        dep_tot += dep_w
        blk_tot += blk_w
        win_tot += win_len
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used
    busy_frac = sum(per_bf) / seeds_used
    p_wait = sum(per_pw) / seeds_used
    p_loss = sum(per_pl) / seeds_used
    arr = arr_tot / seeds_used
    dep = dep_tot / seeds_used
    blk = blk_tot / seeds_used
    win = win_tot / seeds_used
    dep_rate = dep / win * 60.0
    lam_eff = arr / win * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(seeds_used)],
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
