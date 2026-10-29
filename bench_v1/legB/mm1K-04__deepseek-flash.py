import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 12.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1

    H = a.horizon
    warm = 0.25 * H
    win = H - warm

    per_L = []
    per_W = []
    per_busy = []
    seed_list = []
    tot_arr = 0.0
    tot_blk = 0.0
    tot_dep = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = False
        cur_dep = 0.0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        arr_w = 0
        blk_w = 0
        dep_w = 0
        wsum = 0.0
        wcnt = 0
        last = 0.0
        while True:
            if busy:
                dt = cur_dep - t
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_n += n * seg
                        area_busy += (1 if busy else 0) * seg
                    elif nt > warm:
                        seg2 = H - warm
                        area_n += n * seg2
                        area_busy += (1 if busy else 0) * seg2
                break
            if t >= warm:
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
            elif nt > warm:
                seg = nt - warm
                area_n += n * seg
                area_busy += (1 if busy else 0) * seg
            t = nt
            if busy:
                busy = False
                n -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    q = queue.pop(0)
                    q[1] = t
                    busy = True
                    n += 1
                    cur_dep = t + q[2]
                    if t >= warm:
                        wsum += (t - q[0])
                        wcnt += 1
            else:
                if t >= warm:
                    arr_w += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    if n == 0:
                        busy = True
                        n += 1
                        cur_dep = t + svc
                        if t >= warm:
                            wsum += 0.0
                            wcnt += 1
                    else:
                        queue.append([t, t, svc])
                        n += 1
                else:
                    if t >= warm:
                        blk_w += 1
        Ls = area_n / win if win > 0 else 0.0
        Ws = (wsum / wcnt) if wcnt > 0 else 0.0
        Bs = area_busy / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(Bs)
        tot_arr += arr_w
        tot_blk += blk_w
        tot_dep += dep_w

    seeds_used = len(seed_list)
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    arr = tot_arr / seeds_used
    blk = tot_blk / seeds_used
    dep = tot_dep / seeds_used
    dep_rate = (tot_dep / seeds_used) / win if win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': arr,
        'blk': blk,
        'dep': dep,
        'dep_rate': dep_rate,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': win
    }
    print(json.dumps(out))

main()
