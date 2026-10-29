import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
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
    tot_area = tot_busy_area = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        served = 0
        waited = 0
        last = 0.0
        while True:
            if busy < c:
                dt = rng.expovariate(lam)
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    if t < warm:
                        seg = H - warm
                    else:
                        seg = H - t
                    if seg > 0:
                        area += n * seg
                        busy_area += busy * seg
                        win_area += seg
                break
            if t < warm and nt > warm:
                seg = warm - t
                area += n * seg
                busy_area += busy * seg
                t = warm
            else:
                seg = nt - t
                if t >= warm:
                    area += n * seg
                    busy_area += busy * seg
                    win_area += seg
                t = nt
            if t >= warm:
                arr += 1
            st = rng.expovariate(mu)
            cust = {'arr': t, 'st': st}
            if busy < c:
                busy += 1
                n += 1
                servers.append((t + st, cust))
            else:
                queue.append(cust)
                n += 1
            while servers and servers[0][0] <= t:
                servers.pop(0)
                busy -= 1
                n -= 1
                if t >= warm:
                    dep += 1
                    served += 1
                    wait_sum += 0
                if queue:
                    q = queue.pop(0)
                    busy += 1
                    n += 1
                    servers.append((t + q['st'], q))
                    if t >= warm:
                        waited += 1
            servers.sort()
        w = win_area if win_area > 0 else 1.0
        L = area / w
        bf = busy_area / w
        per_L.append(L)
        per_W.append(L / (lam if lam > 0 else 1.0) * 60.0 if False else L / max(lam, 1e-9))
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(waited / served if served > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy_area += busy_area
        tot_win += win_area
        tot_wait += wait_sum
        tot_served += served
        tot_waited += waited

    W_win = tot_win if tot_win > 0 else 1.0
    L = tot_area / W_win
    busy_frac = tot_busy_area / W_win
    lam_eff = tot_arr / W_win
    dep_rate = tot_dep / W_win
    W = L / lam_eff if lam_eff > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac / c,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': W_win,
        'arr': tot_arr / len(seeds),
        'dep': tot_dep / len(seeds),
        'blk': tot_blk / len(seeds),
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
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
