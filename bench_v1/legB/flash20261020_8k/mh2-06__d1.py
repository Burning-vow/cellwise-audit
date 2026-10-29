import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0 / 60.0
    mean_s = 6.0
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        pass

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    r1 = 2.0 * p * mean_s
    r2 = 2.0 * (1.0 - p) * mean_s

    def draw():
        if random.random() < p:
            return random.expovariate(1.0 / r1)
        return random.expovariate(1.0 / r2)

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_n = tot_wait_sum = 0.0
    tot_win = 0.0

    for s in seeds:
        random.seed(s)
        t = 0.0
        busy = False
        rem = 0.0
        q = []
        area = 0.0
        busy_t = 0.0
        arr = dep = blk = 0.0
        wait_n = 0.0
        wait_sum = 0.0
        last = 0.0
        while True:
            if busy:
                dt = rem
                nxt = t + dt
            else:
                dt = random.expovariate(lam)
                nxt = t + dt
            if nxt > H:
                if busy:
                    seg = H - t
                    if t >= warm:
                        area += seg
                        busy_t += seg
                    else:
                        if H > warm:
                            area += H - warm
                            busy_t += H - warm
                else:
                    if t < warm and H > warm:
                        pass
                break
            if t >= warm:
                area += (nxt - t) * (1 if busy else 0)
                busy_t += (nxt - t) if busy else 0.0
            t = nxt
            if busy:
                busy = False
                rem = 0.0
                if q:
                    svc, at = q.pop(0)
                    if t >= warm:
                        wait_sum += t - at
                        wait_n += 1
                    busy = True
                    rem = svc
            else:
                arr += 1
                svc = draw()
                if t >= warm:
                    pass
                if busy:
                    q.append((svc, t))
                else:
                    busy = True
                    rem = svc
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if wait_n > 0 else 0.0)
        tot_arr += arr
        tot_dep += arr
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_wait_n += wait_n
        tot_wait_sum += wait_sum
        tot_win += win

    n = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_sum / tot_wait_n if tot_wait_n > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / n
    dep_avg = tot_dep / n
    blk_avg = tot_blk / n
    dep_rate = dep_avg / (tot_win / n) if tot_win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = tot_wait_n / tot_dep if tot_dep > 0 else 0.0
    lam_eff = lam * (1.0 - p_loss)

    out = {
        'L': L, 'W': W, 'busy_frac': bf,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': n,
        'time_unit': 'minute', 'win': tot_win / n if n else 0.0,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': bf,
        'busy_occupied': bf, 'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
