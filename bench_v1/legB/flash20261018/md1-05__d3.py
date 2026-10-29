import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_waitn = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        arr = dep = blk = 0
        area = busy_area = 0.0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            rate = lam + (mu * busy)
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                nt = H
            area += n * (nt - t)
            busy_area += busy * (nt - t)
            t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                cust = [t, svc]
                if busy < c:
                    busy += 1
                    servers[busy - 1] = cust
                    cust.append(t)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                else:
                    queue.append(cust)
                n += 1
            else:
                busy -= 1
                done = None
                for i in range(c):
                    if servers[i] is not None:
                        done = servers[i]
                        servers[i] = None
                        break
                if done is not None:
                    dep += 1
                    if t >= warm:
                        wait_sum += (t - done[0])
                        wait_n += 1
                if queue:
                    cust = queue.pop(0)
                    busy += 1
                    servers[busy - 1] = cust
                    cust.append(t)
                    if t >= warm:
                        wait_sum += (t - cust[0])
                        wait_n += 1
                n -= 1
        win = H - warm
        L = area / H
        W = (area / max(dep, 1)) if dep > 0 else 0.0
        bf = busy_area / H
        pl = blk / max(arr, 1)
        pw = wait_n / max(arr, 1)
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waitn += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_area / (H * ns)
    W = (tot_wait / tot_waitn) if tot_waitn > 0 else 0.0
    busy_frac = tot_busy / (H * ns)
    busy_util = busy_frac / c
    busy_occupied = busy_frac
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = (tot_dep / ns) / (H / 60.0)
    lam_eff = (tot_arr / ns) / (H / 60.0)
    p_loss = tot_blk / max(tot_arr, 1)
    p_wait = tot_waitn / max(tot_arr, 1)

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'busy_occupied': busy_occupied, 'dep': dep_avg,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
