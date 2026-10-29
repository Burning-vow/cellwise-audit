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
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
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
    tot_busy = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_n = 0.0
    tot_dep_n = 0.0
    tot_wait_n = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_n = 0
        soj_sum = 0.0
        soj_n = 0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                t_next = t + dt
                if t_next > H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                    t = H
                    break
                area += n * (t_next - t)
                busy_area += (1 if busy else 0) * (t_next - t)
                t = t_next
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                        soj_sum += svc
                        soj_n += 1
                else:
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                if t >= warm:
                    pass
            else:
                dt_arr = rng.expovariate(lam)
                t_arr = t + dt_arr
                t_dep = next_dep
                if t_arr < t_dep:
                    if t_arr > H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        t = H
                        break
                    area += n * (t_arr - t)
                    busy_area += (1 if busy else 0) * (t_arr - t)
                    t = t_arr
                    n += 1
                    svc = rng.expovariate(mu)
                    if t >= warm:
                        arr_w += 1
                    if not busy:
                        busy = True
                        next_dep = t + svc
                        if t >= warm:
                            wait_sum += 0.0
                            wait_n += 1
                            soj_sum += svc
                            soj_n += 1
                    else:
                        if t >= warm:
                            wait_sum += 0.0
                            wait_n += 1
                else:
                    if t_dep > H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        t = H
                        break
                    area += n * (t_dep - t)
                    busy_area += (1 if busy else 0) * (t_dep - t)
                    t = t_dep
                    n -= 1
                    if t >= warm:
                        dep_w += 1
                    if n == 0:
                        busy = False
                        next_dep = float('inf')
                    else:
                        svc = rng.expovariate(mu)
                        next_dep = t + svc
                        if t >= warm:
                            soj_sum += svc
                            soj_n += 1
        win = H - warm
        Ls = area / H if H > 0 else 0.0
        bf = busy_area / H if H > 0 else 0.0
        Ws = (soj_sum / soj_n) if soj_n > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_n / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy += bf
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_n += Ls
        tot_dep_n += dep_w
        tot_wait_n += wait_n
    ns = a.seeds
    L = tot_n / ns if ns > 0 else 0.0
    W = (tot_soj / tot_wait_n) if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / ns if ns > 0 else 0.0
    p_wait = (tot_wait_n / tot_arr) if tot_arr > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    win = H - warm
    dep_rate = (tot_dep / ns) / win * 60.0 if win > 0 else 0.0
    lam_eff = (tot_arr / ns) / win * 60.0 if win > 0 else 0.0
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
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns if ns > 0 else 0.0,
        'dep': tot_dep / ns if ns > 0 else 0.0,
        'blk': tot_blk / ns if ns > 0 else 0.0,
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
