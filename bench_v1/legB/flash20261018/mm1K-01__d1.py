import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_areaN = 0.0
    tot_areaBusy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        arr_w = 0
        dep_w = 0
        blk_w = 0
        areaN = 0.0
        areaBusy = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_w_cnt = 0
        while True:
            t_next = min(next_arr, next_dep)
            if t_next > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy else 0) * dt
                t = H
                break
            dt = t_next - t
            if t >= warm:
                areaN += n * dt
                areaBusy += (1 if busy else 0) * dt
            t = t_next
            if next_arr <= next_dep:
                arr_w += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        next_dep = t + svc
                    else:
                        pass
                    if n == 1 and busy:
                        pass
                else:
                    blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep_w += 1
                n -= 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(0.0)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaBusy += areaBusy
    ns = len(seeds)
    win = H - warm
    L = tot_areaN / (ns * win) if win > 0 else 0.0
    bf = tot_areaBusy / (ns * win) if win > 0 else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    W = L / lam_eff if lam_eff > 0 else 0.0
    busy_util = bf
    busy_occupied = bf
    p_wait = 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
