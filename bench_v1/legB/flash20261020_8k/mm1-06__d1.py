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
        if win_len <= 0:
            win_len = H
            win_start = 0.0
        queue = []
        next_arr = rng.expovariate(lam)
        while t < H:
            if n == 0:
                dt = next_arr - t
                if t + dt > H:
                    dt = H - t
                area_n += n * dt
                area_b += (1 if n >= 1 else 0) * dt
                t += dt
                if t >= H:
                    break
                n += 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
                if t >= win_start:
                    arr_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t_dep = queue[0][0] + queue[0][1]
                dt = min(next_arr, t_dep) - t
                if t + dt > H:
                    dt = H - t
                area_n += n * dt
                area_b += 1 * dt
                t += dt
                if t >= H:
                    break
                if next_arr <= t_dep:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if t >= win_start:
                        arr_w += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    at, sv = queue.pop(0)
                    n -= 1
                    if t >= win_start:
                        dep_w += 1
                        wait_w += (t - at)
                        wait_n += 1
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_b / win_len if win_len > 0 else 0.0
        W = (wait_w / wait_n) if wait_n > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_n / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        arr_tot += arr_w
        dep_tot += dep_w
        blk_tot += blk_w
        win_tot += win_len
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = arr_tot / ns
    dep = dep_tot / ns
    blk = blk_tot / ns
    win = win_tot / ns
    dep_rate = (dep / win) * 60.0 if win > 0 else 0.0
    lam_eff = (arr / win) * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
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
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
