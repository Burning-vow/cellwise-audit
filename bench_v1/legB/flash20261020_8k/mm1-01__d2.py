import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=str, default='2000')
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    H = float(a.horizon)
    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        pass
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_n = 0.0
    tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        warm = 0.25 * H
        area_n = 0.0
        area_busy = 0.0
        arr = 0
        dep = 0
        blk = 0
        waiters = 0
        soj = 0.0
        last = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_n += n * seg
                        area_busy += (1 if busy else 0) * seg
                    elif t + seg > warm:
                        seg2 = t + seg - warm
                        area_n += n * seg2
                        area_busy += (1 if busy else 0) * seg2
                break
            if t >= warm:
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
            elif t + dt > warm:
                seg2 = t + dt - warm
                area_n += n * seg2
                area_busy += (1 if busy else 0) * seg2
            t += dt
            if busy:
                n -= 1
                dep += 1
                busy = False
                next_dep = float('inf')
                if n > 0:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
            else:
                arr += 1
                if n == 0:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
                n += 1
        win = H - warm
        L = area_n / win
        bf = area_busy / win
        W = L / (lam * (1 - 0)) if lam > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += area_busy
        tot_n += area_n
        tot_win += win
    ns = len(seeds)
    L = tot_n / tot_win
    busy_frac = tot_busy / tot_win
    W = L / lam if lam > 0 else 0.0
    dep_rate = (tot_dep / tot_win) * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': 0.0,
        'p_loss': 0.0,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'win': tot_win / ns,
        'arr': tot_arr / ns,
        'dep': tot_dep / ns,
        'blk': tot_blk / ns,
        'dep_rate': dep_rate,
        'lam_eff': lam * 60.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
