import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_busy = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_area = 0.0
        wait_cnt = 0
        served = 0
        t_next = rng.expovariate(lam)
        t_dep = float('inf')
        while t < H:
            if t_next < t_dep:
                dt = t_next - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += (1 if n > 0 else 0) * dt
                    wait_area += n * dt
                t = t_next
                if t >= H:
                    break
                if t >= warm:
                    arr_w += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    if n == 1:
                        t_dep = t + svc
                else:
                    if t >= warm:
                        blk_w += 1
                t_next = t + rng.expovariate(lam)
            else:
                dt = t_dep - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += (1 if n > 0 else 0) * dt
                    wait_area += n * dt
                t = t_dep
                if t >= H:
                    break
                n -= 1
                if t >= warm:
                    dep_w += 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    t_dep = t + svc
                else:
                    t_dep = float('inf')
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        W = wait_area / dep_w if dep_w > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = (arr_w - blk_w) / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_win += win
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = L / K
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
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
