import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
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

    per_L, per_W, per_busy = [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area_n = tot_area_b = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        area_n = area_b = 0.0
        wait_sum = soj_sum = 0.0
        arr_w = dep_w = blk_w = 0.0
        last = 0.0
        win_start = warm
        win_len = H - warm

        def integrate(upto):
            nonlocal area_n, area_b, last
            dt = upto - last
            if dt > 0 and last >= win_start:
                area_n += n * dt
                area_b += busy * dt
            elif dt > 0 and upto > win_start:
                dt2 = upto - win_start
                area_n += n * dt2
                area_b += busy * dt2
            last = upto

        while True:
            if queue:
                nxt_arr = t + rng.expovariate(lam)
            else:
                nxt_arr = t + rng.expovariate(lam)
            nxt_dep = min([x[0] for x in servers if x is not None], default=math.inf)
            tn = min(nxt_arr, nxt_dep)
            if tn > H:
                integrate(H)
                break
            integrate(tn)
            t = tn
            if nxt_arr <= nxt_dep:
                n += 1
                svc = rng.expovariate(mu)
                if t >= win_start:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    servers[busy - 1] = (t + svc, t, svc)
                else:
                    queue.append((t, svc))
                    if t >= win_start:
                        blk_w += 1
            else:
                idx = None
                for i in range(c):
                    if servers[i] is not None and servers[i][0] == t:
                        idx = i
                        break
                _, at, svc = servers[idx]
                servers[idx] = None
                busy -= 1
                n -= 1
                if t >= win_start:
                    dep_w += 1
                    wait_sum += (t - svc - at)
                    soj_sum += (t - at)
                if queue:
                    at2, svc2 = queue.pop(0)
                    busy += 1
                    servers[idx] = (t + svc2, at2, svc2)

        per_L.append(area_n / win_len)
        per_W.append((wait_sum + soj_sum) / dep_w if dep_w > 0 else 0.0)
        per_busy.append(area_b / (win_len * c))
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area_n += area_n
        tot_area_b += area_b
        tot_wait += wait_sum
        tot_soj += soj_sum
        win_total += win_len

    ns = len(seeds)
    L = tot_area_n / win_total
    W = (tot_wait + tot_soj) / tot_dep if tot_dep > 0 else 0.0
    p_wait = tot_blk / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (win_total / 60.0)
    out = {
        'L': L,
        'W': W,
        'arr': tot_arr / ns,
        'blk': tot_blk / ns,
        'dep': tot_dep / ns,
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_total / ns,
    }
    print(json.dumps(out))

main()
