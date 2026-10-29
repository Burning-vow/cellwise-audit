import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0
    mean_s = 0.1
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p2 = min(max(p2, 1e-9), 1.0 - 1e-9)
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (1.0 - p2) / p2))) if p2 < 1 else mean_s
    m1 = max(m1, 1e-12)
    m2 = (mean_s - p2 * m1) / (1.0 - p2)
    m2 = max(m2, 1e-12)

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_n = 0.0
    win_total = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        svc = []
        while True:
            if busy:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    break
                t += dt
                arr_times.append(t)
                u = rng.random()
                s = m1 if u < p2 else m2
                svc.append(s)
                n += 1
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    break
                t += dt
                arr_times.append(t)
                u = rng.random()
                s = m1 if u < p2 else m2
                svc.append(s)
                n += 1
                busy = True
                rem = s
                start = t
                if t >= warm:
                    tot_wait_area += 0.0
                while True:
                    nxt = rng.expovariate(lam)
                    if t + nxt > H:
                        t = H
                        if t > start and t >= warm:
                            pass
                        break
                    if nxt < rem:
                        t += nxt
                        rem -= nxt
                        arr_times.append(t)
                        u = rng.random()
                        s = m1 if u < p2 else m2
                        svc.append(s)
                        n += 1
                    else:
                        t += rem
                        rem = 0.0
                        busy = False
                        break
                if not busy:
                    continue
                break

        # simple event simulation
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr_c = dep_c = blk_c = 0
        area = busy_area = wait_area = 0.0
        wait_n = 0
        last = 0.0
        while t < H:
            if busy:
                dt = rng.expovariate(lam)
                if t + dt >= H:
                    dt = H - t
                    if t >= warm:
                        area += n * dt
                        busy_area += dt
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                arr_c += 1
                u = rng.random()
                s = m1 if u < p2 else m2
                if busy:
                    queue.append((t, s))
                else:
                    busy = True
                    rem = s
                    if t >= warm:
                        wait_n += 1
            else:
                dt = rng.expovariate(lam)
                if t + dt >= H:
                    dt = H - t
                    if t >= warm:
                        area += n * dt
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                t += dt
                arr_c += 1
                u = rng.random()
                s = m1 if u < p2 else m2
                busy = True
                rem = s
                if t >= warm:
                    wait_n += 1
            while busy and rem > 0:
                if queue:
                    nxt = queue[0][0]
                else:
                    nxt = H
                dt = min(rem, nxt - t if nxt > t else 0.0)
                if dt <= 0:
                    break
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    dep_c += 1
                    if queue:
                        at, s = queue.pop(0)
                        busy = True
                        rem = s
                        if t >= warm:
                            wait_area += (t - at)
                            wait_n += 1
                    break
                if queue and abs(t - queue[0][0]) < 1e-12:
                    at, s = queue.pop(0)
                    if t >= warm:
                        wait_area += (t - at)
                        wait_n += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (wait_area / wait_n) if wait_n > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_n += arr_c
        win_total += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = win_total / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = bf
    busy_occupied = bf

    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'runtime_units': H,
        'seed_list': seeds, 'seeds_used': ns, 'time_unit': 'hour', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util, 'dep': dep,
        'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_loss': pl, 'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W, 'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
