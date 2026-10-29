import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1.0
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = c * 1.25

    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = a.horizon
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_dep_n = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_b = 0.0
        arr_w = 0.0
        dep_w = 0.0
        blk_w = 0.0
        dep_n_w = 0.0
        sojourn_sum = 0.0
        sojourn_cnt = 0
        last = 0.0
        queue = []
        server_free = 0.0
        next_arr = rng.expovariate(lam)
        while t < H:
            if next_arr <= server_free and next_arr <= t + 1e-12:
                pass
            nxt = next_arr
            if server_free < nxt:
                nxt = server_free
            if nxt > H:
                nxt = H
            dt = nxt - t
            if t >= warm:
                area_n += n * dt
                area_b += (1.0 if busy > 0 else 0.0) * dt
            t = nxt
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                svc = rng.expovariate(mu) / c
                queue.append((t, svc))
                n += 1
                if t >= warm:
                    arr_w += 1
                next_arr = t + rng.expovariate(lam)
                if busy == 0:
                    busy = 1
                    st, sv = queue.pop(0)
                    server_free = t + sv
            elif abs(t - server_free) < 1e-12:
                if queue:
                    st, sv = queue.pop(0)
                    server_free = t + sv
                else:
                    busy = 0
                    server_free = float('inf')
                n -= 1
                if t >= warm:
                    dep_w += 1
                    dep_n_w += 1
                    sojourn_sum += t - st
                    sojourn_cnt += 1
        win = H - warm
        Ls = area_n / win if win > 0 else 0.0
        Ws = sojourn_sum / sojourn_cnt if sojourn_cnt > 0 else 0.0
        bs = area_b / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_dep_n += dep_n_w
        win_total += win

    L = sum(per_L) / len(per_L)
    W = sum(per_W) / len(per_W)
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = tot_dep_n / win_total if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': arr,
        'blk': blk,
        'dep': dep,
        'dep_rate': dep_rate,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': H - warm,
    }
    print(json.dumps(out))

main()
