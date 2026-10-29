import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=8)
    p.add_argument('--horizon', type=float, default=2000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        mu *= 1.2
    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L, per_W, per_busy = [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_dep_n = 0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        # queue of (arrival_time, service_time)
        q = []
        cur_start = None
        cur_svc = None
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_len = 0.0
        arr_c = dep_c = blk_c = 0
        dep_n = 0
        last_t = 0.0
        # event loop
        while t < H:
            # integrate area up to next event
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam) if False else None
            # generate next arrival time
            ia = rng.expovariate(lam)
            na = t + ia
            if busy:
                nd = next_dep
            else:
                nd = float('inf')
            te = min(na, nd, H)
            dt = te - t
            # integrate area before state change
            if te > warm:
                seg_start = max(t, warm)
                seg = te - seg_start
                if seg > 0:
                    win_area += n * seg
                    win_len += seg
                    if busy:
                        win_busy += seg
            t = te
            if t >= H:
                break
            if na <= nd:
                # arrival
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_c += 1
                if not busy:
                    busy = True
                    cur_svc = svc
                    next_dep = t + svc
                    if t >= warm:
                        pass
                else:
                    q.append((t, svc))
                n += 1
            else:
                # departure
                if t >= warm:
                    dep_c += 1
                    dep_n += 1
                n -= 1
                if q:
                    at, svc = q.pop(0)
                    cur_svc = svc
                    next_dep = t + svc
                else:
                    busy = False
                    next_dep = float('inf')
        # final integration to H
        if t < H:
            seg_start = max(t, warm)
            seg = H - seg_start
            if seg > 0:
                win_area += n * seg
                win_len += seg
                if busy:
                    win_busy += seg
        Ls = win_area / win_len if win_len > 0 else 0.0
        Ws = Ls / (lam) if lam > 0 else 0.0
        bs = win_busy / win_len if win_len > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        tot_area += win_area
        tot_busy += win_busy
        tot_win += win_len
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_dep_n += dep_n
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'arr': tot_arr / len(seeds),
        'blk': tot_blk / len(seeds),
        'dep': tot_dep / len(seeds),
        'dep_rate': dep_rate,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds)
    }
    print(json.dumps(out))

main()
