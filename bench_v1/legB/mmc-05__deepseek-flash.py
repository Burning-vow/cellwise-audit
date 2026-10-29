import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

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
    tot_waiters = 0
    tot_arrivals = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        nxt = rng.expovariate(lam)
        busy = [0.0] * c
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_wait = 0.0
        area_soj = 0.0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        cnt_waiters = 0
        sum_wait = 0.0
        sum_soj = 0.0
        n = 0
        last = 0.0
        while True:
            if nxt <= H:
                te = nxt
            else:
                te = H
            dt = te - last
            if te > warm:
                lo = max(last, warm)
                d = te - lo
                if d > 0:
                    area_n += n * d
                    area_busy += sum(1 for b in busy if b > 0) * d
            last = te
            if te >= H:
                break
            if nxt <= H and (not queue or nxt <= min(busy)):
                t = nxt
                n += 1
                cnt_arr += 1
                svc = rng.expovariate(mu)
                if any(b <= t for b in busy):
                    idx = min(range(c), key=lambda i: busy[i])
                    busy[idx] = t + svc
                    if t >= warm:
                        area_soj += svc
                        sum_soj += svc
                        cnt_dep += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        cnt_blk += 1
                        cnt_waiters += 1
                nxt = t + rng.expovariate(lam)
            else:
                idx = min(range(c), key=lambda i: busy[i])
                t = busy[idx]
                if queue:
                    at, svc = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        area_wait += w
                        sum_wait += w
                        cnt_waiters += 1
                    busy[idx] = t + svc
                    if t >= warm:
                        area_soj += svc
                        sum_soj += svc
                        cnt_dep += 1
                else:
                    busy[idx] = 0.0
                n -= 1
        win = H - warm
        win_total += win
        L = area_n / win if win > 0 else 0.0
        W = (sum_wait + sum_soj) / cnt_dep if cnt_dep > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        tot_arr += cnt_arr
        tot_dep += cnt_dep
        tot_blk += cnt_blk
        tot_wait += sum_wait
        tot_soj += sum_soj
        tot_n += cnt_dep
        tot_waiters += cnt_waiters
        tot_arrivals += cnt_arr

    L = sum(per_L) / len(per_L)
    W = sum(per_W) / len(per_W)
    p_wait = tot_waiters / tot_arrivals if tot_arrivals > 0 else 0.0
    dep_rate = tot_dep / win_total if win_total > 0 else 0.0
    arr_rate = tot_arr / win_total if win_total > 0 else 0.0
    blk_rate = tot_blk / win_total if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': arr_rate,
        'blk': blk_rate,
        'dep': dep_rate,
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': win_total / len(seeds) if seeds else 0.0,
    }
    print(json.dumps(out))

main()
