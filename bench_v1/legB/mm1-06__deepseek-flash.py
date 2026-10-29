import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 7.0
    mu = 12.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c *= 1.2

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_dep_n = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_b = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        dep_count = 0
        # event list: (time, type, payload)
        # type 0 arrival, 1 departure
        next_arr = rng.expovariate(lam)
        server_free = 0.0
        queue = []
        # schedule first arrival
        events = [(next_arr, 0, None)]
        last_t = 0.0
        while True:
            if not events:
                break
            events.sort(key=lambda e: e[0])
            te, typ, payload = events.pop(0)
            if te > H:
                # integrate to H
                dt = H - last_t
                if last_t >= warm:
                    area_n += n * dt
                    area_b += (1 if busy > 0 else 0) * dt
                elif te > warm:
                    dt2 = warm - last_t
                    area_n += n * dt2
                    area_b += (1 if busy > 0 else 0) * dt2
                    dt3 = H - warm
                    area_n += n * dt3
                    area_b += (1 if busy > 0 else 0) * dt3
                last_t = H
                break
            dt = te - last_t
            if dt > 0:
                if last_t >= warm:
                    area_n += n * dt
                    area_b += (1 if busy > 0 else 0) * dt
                elif te > warm:
                    dt2 = warm - last_t
                    area_n += n * dt2
                    area_b += (1 if busy > 0 else 0) * dt2
                    dt3 = te - warm
                    area_n += n * dt3
                    area_b += (1 if busy > 0 else 0) * dt3
            last_t = te
            if typ == 0:
                # arrival
                n += 1
                if te >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu) / c
                cust = {'arr': te, 'svc': svc}
                if busy <= 0:
                    busy = 1
                    dep_t = te + svc
                    events.append((dep_t, 1, cust))
                else:
                    queue.append(cust)
                next_arr = te + rng.expovariate(lam)
                events.append((next_arr, 0, None))
            else:
                # departure
                cust = payload
                n -= 1
                if te >= warm:
                    dep_w += 1
                    wait_sum += te - cust['arr']
                    dep_count += 1
                if queue:
                    nxt = queue.pop(0)
                    dep_t = te + nxt['svc']
                    events.append((dep_t, 1, nxt))
                else:
                    busy = 0
        win = H - warm
        win_total += win
        Ls = area_n / win if win > 0 else 0.0
        Ws = (wait_sum / dep_count) if dep_count > 0 else 0.0
        bs = area_b / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += (arr_w - dep_w)
        tot_dep_n += dep_count

    L = sum(per_L) / len(per_L)
    W = sum(per_W) / len(per_W)
    arr_rate = tot_arr / win_total if win_total > 0 else 0.0
    dep_rate = tot_dep / win_total if win_total > 0 else 0.0
    blk_rate = tot_blk / win_total if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': arr_rate,
        'blk': blk_rate,
        'dep': dep_rate,
        'dep_rate': dep_rate,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': win_total / len(seeds) if seeds else 0.0,
    }
    print(json.dumps(out))

main()
