import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0
    tot_serv = 0.0
    tot_serv_n = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        in_service = []
        area = 0.0
        busy_area = 0.0
        w_area = 0.0
        w_n = 0
        arr_c = dep_c = blk_c = 0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last_t
                if t > win_start:
                    seg = min(t, H) - max(last_t, win_start)
                    if seg > 0:
                        area += n * seg
                        busy_area += min(n, c) * seg
                last_t = t
                t = next_arr
                if t >= H:
                    break
                if t >= win_start:
                    arr_c += 1
                if n < c:
                    n += 1
                    st = rng.expovariate(mu)
                    in_service.append((t + st, t))
                else:
                    queue.append(t)
                next_arr = t + rng.expovariate(lam)
            else:
                if t > win_start:
                    seg = min(t, H) - max(last_t, win_start)
                    if seg > 0:
                        area += n * seg
                        busy_area += min(n, c) * seg
                last_t = t
                t = next_arr
        if last_t < H:
            seg = H - max(last_t, win_start)
            if seg > 0:
                area += n * seg
                busy_area += min(n, c) * seg

        L = area / win_len if win_len > 0 else 0.0
        bf = busy_area / (win_len * c) if win_len > 0 else 0.0
        per_L.append(L)
        per_bf.append(bf)
        per_W.append(L / lam if lam > 0 else 0.0)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr_c
        tot_area += area
        tot_busy += busy_area
        tot_win += win_len

    L = tot_area / tot_win if tot_win > 0 else 0.0
    bf = tot_busy / (tot_win * c) if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    dep_rate = lam * (1.0 - 0.0)
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'dep': tot_arr / len(seeds) if seeds else 0.0,
        'blk': 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': 0.0,
        'p_wait': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
