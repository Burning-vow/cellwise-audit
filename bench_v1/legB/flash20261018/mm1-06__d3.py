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
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_b = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0
        wait_cnt = 0
        last = 0.0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_b += (1 if busy else 0) * (H - t)
                break
            if t < H:
                area_n += n * (nt - t)
                area_b += (1 if busy else 0) * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                svc = rng.expovariate(mu)
                if n == 0 and not busy:
                    busy = True
                    next_dep = t + svc
                else:
                    n += 1
                if t >= warm:
                    arr_w += 1
            else:
                if n > 0:
                    n -= 1
                    next_dep = t + rng.expovariate(mu)
                else:
                    busy = False
                    next_dep = float('inf')
                if t >= warm:
                    dep_w += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_b / win if win > 0 else 0.0
        W = L / (dep_w / win) if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        arr_tot += arr_w
        dep_tot += dep_w
        blk_tot += blk_w
        win_tot += win
    ns = a.seeds
    Lm = sum(per_L) / ns if ns else 0.0
    Wm = sum(per_W) / ns if ns else 0.0
    bfm = sum(per_bf) / ns if ns else 0.0
    plm = sum(per_pl) / ns if ns else 0.0
    pwm = sum(per_pw) / ns if ns else 0.0
    win_avg = win_tot / ns if ns else 0.0
    dep_rate = (dep_tot / ns) / win_avg if win_avg > 0 else 0.0
    out = {
        'L': Lm,
        'W': Wm,
        'busy_frac': bfm,
        'busy_util': bfm,
        'busy_occupied': bfm,
        'p_wait': pwm,
        'p_loss': plm,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_avg,
        'arr': arr_tot / ns if ns else 0.0,
        'dep': dep_tot / ns if ns else 0.0,
        'blk': blk_tot / ns if ns else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
