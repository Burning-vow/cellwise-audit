import json, random, argparse, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 4

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_n = 0
    tot_busy_area = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        events = []
        heapq.heapify(events)
        next_arr = rng.expovariate(lam)
        heapq.heappush(events, (next_arr, 0, None))
        area_n = 0.0
        area_busy = 0.0
        last_t = 0.0
        wsum = 0.0
        wcount = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        win_start = warm
        win_end = H
        win_len = win_end - win_start
        while events:
            tt, typ, payload = heapq.heappop(events)
            if tt > H:
                break
            dt = tt - last_t
            if tt > win_start:
                seg = min(tt, win_end) - max(last_t, win_start)
                if seg > 0:
                    area_n += n * seg
                    area_busy += busy * seg
            last_t = tt
            if typ == 0:
                n += 1
                if tt >= win_start:
                    arr_c += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    heapq.heappush(events, (tt + svc, 1, svc))
                else:
                    queue.append(svc)
                    if tt >= win_start:
                        blk_c += 1
                na = tt + rng.expovariate(lam)
                heapq.heappush(events, (na, 0, None))
            else:
                n -= 1
                if tt >= win_start:
                    dep_c += 1
                if queue:
                    svc = queue.pop(0)
                    heapq.heappush(events, (tt + svc, 1, svc))
                else:
                    busy -= 1
        if win_len > 0:
            Ls = area_n / win_len
            bf = area_busy / (win_len * c)
        else:
            Ls = 0.0
            bf = 0.0
        Ws = (Ls / (lam * 60.0)) if lam > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bf)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_soj += area_n
        tot_busy_area += area_busy
        win_total += win_len

    ns = len(seeds)
    L = sum(per_L) / ns if ns else 0.0
    W = sum(per_W) / ns if ns else 0.0
    p_wait = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    arr_avg = tot_arr / ns if ns else 0.0
    dep_avg = tot_dep / ns if ns else 0.0
    blk_avg = tot_blk / ns if ns else 0.0
    dep_rate = (tot_dep / win_total * 60.0) if win_total > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'arr': arr_avg,
        'blk': blk_avg,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_total / ns if ns else 0.0,
    }
    print(json.dumps(out))

main()
