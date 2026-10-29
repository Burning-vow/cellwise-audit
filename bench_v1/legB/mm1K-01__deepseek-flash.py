import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    cap = 4
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu = 12.0
    elif a.pert == 'c_up':
        cap = 5

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_blk = 0.0
    tot_dep = 0.0
    tot_wait = 0.0
    tot_n = 0
    tot_busy_area = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        cur_dep = 0.0
        queue = []
        arr_w = 0
        blk_w = 0
        dep_w = 0
        wait_sum = 0.0
        n_dep = 0
        busy_area = 0.0
        last_t = warm
        area_L = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    if t < warm:
                        seg = H - warm
                    else:
                        seg = H - t
                    if seg > 0:
                        area_L += n * seg
                        busy_area += (1 if busy else 0) * seg
                break
            if nt > warm and t < warm:
                area_L += n * (warm - t)
                busy_area += (1 if busy else 0) * (warm - t)
            elif t >= warm:
                area_L += n * (nt - t)
                busy_area += (1 if busy else 0) * (nt - t)
            t = nt
            if t >= warm:
                arr_w += 1
            if n < cap:
                svc = rng.expovariate(mu)
                cust = {'arr': t, 'svc': svc}
                n += 1
                if not busy:
                    busy = True
                    cur_dep = t + svc
                    cust['start'] = t
                else:
                    queue.append(cust)
            else:
                if t >= warm:
                    blk_w += 1
            while busy and cur_dep <= t:
                if t >= warm:
                    dep_w += 1
                    wait_sum += (cur_dep - cust_dep_arr)
                    n_dep += 1
                n -= 1
                if queue:
                    c2 = queue.pop(0)
                    c2['start'] = cur_dep
                    cust_dep_arr = c2['arr']
                    cur_dep = cur_dep + c2['svc']
                else:
                    busy = False
                    cur_dep = float('inf')
                    break
            if busy and 'cust_dep_arr' not in dir():
                pass
        per_L.append(area_L / (H - warm) if H > warm else 0.0)
        per_W.append((wait_sum / n_dep) if n_dep > 0 else 0.0)
        per_busy.append(busy_area / (H - warm) if H > warm else 0.0)
        tot_arr += arr_w
        tot_blk += blk_w
        tot_dep += dep_w
        tot_wait += wait_sum
        tot_n += n_dep
        tot_busy_area += busy_area
        tot_win += (H - warm)

    L = sum(per_L) / len(per_L) if per_L else 0.0
    W = (tot_wait / tot_n) if tot_n > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'arr': tot_arr / len(seeds),
        'blk': tot_blk / len(seeds),
        'dep': tot_dep / len(seeds),
        'dep_rate': dep_rate,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': H - warm,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
