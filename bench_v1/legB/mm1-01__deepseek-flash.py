import argparse, json, math, random

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
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area_n = 0.0
    tot_area_b = 0.0
    tot_area_w = 0.0
    tot_win = 0.0
    tot_served = 0.0
    tot_waiters = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area_n = 0.0
        area_b = 0.0
        area_w = 0.0
        win = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        served = 0
        waiters = 0
        last = 0.0
        while True:
            tn = min(next_arr, next_dep)
            if tn > H:
                tn = H
            dt = tn - t
            if t >= warm:
                area_n += n * dt
                area_b += (1 if busy else 0) * dt
                area_w += (1 if n > 0 else 0) * dt
                win += dt
            t = tn
            if t >= H:
                break
            if next_arr <= next_dep:
                n += 1
                arr_c += 1
                if t >= warm:
                    pass
                if not busy:
                    busy = True
                    st = rng.expovariate(mu)
                    next_dep = t + st
                next_arr = t + rng.expovariate(lam)
            else:
                n -= 1
                dep_c += 1
                served += 1
                if n > 0:
                    st = rng.expovariate(mu)
                    next_dep = t + st
                else:
                    busy = False
                    next_dep = float('inf')
        Ls = area_n / win if win > 0 else 0.0
        Ws = Ls / (dep_c / win) if dep_c > 0 and win > 0 else 0.0
        bfs = area_b / win if win > 0 else 0.0
        pls = blk_c / arr_c if arr_c > 0 else 0.0
        pws = area_w / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area_n += area_n
        tot_area_b += area_b
        tot_area_w += area_w
        tot_win += win
        tot_served += served
        tot_waiters += waiters
    L = tot_area_n / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    busy_frac = tot_area_b / tot_win if tot_win > 0 else 0.0
    p_wait = tot_area_w / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': len(seed_list),
        'time_unit': 'minute',
        'win': tot_win / a.seeds if a.seeds > 0 else 0.0,
        'arr': tot_arr / a.seeds if a.seeds > 0 else 0.0,
        'dep': tot_dep / a.seeds if a.seeds > 0 else 0.0,
        'blk': tot_blk / a.seeds if a.seeds > 0 else 0.0,
        'dep_rate': dep_rate * 60.0,
        'lam_eff': (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
