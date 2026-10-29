import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 5.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = c + 1
        cap = cap + 1

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy_area = 0.0
    tot_util_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        area_wait = 0.0
        wait_n = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        last = 0.0
        while True:
            if next_arr <= t:
                dt = next_arr - last
                if next_arr > warm:
                    area_n += n * dt
                    area_busy += (1 if n > 0 else 0) * dt
                    area_util += min(n, c) * dt
                last = next_arr
                t = next_arr
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if t > warm:
                        arr_w += 1
                    if busy < c:
                        busy += 1
                        st, sv = queue.pop(0)
                        if t > warm:
                            area_wait += (t - st)
                            wait_n += 1
                        queue.insert(0, (st, sv))
                        queue.pop(0)
                        queue.append(('busy', t + sv))
                else:
                    if t > warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue:
                    item = queue[0]
                    if item[0] == 'busy':
                        end = item[1]
                        if end <= next_arr:
                            dt = end - last
                            if end > warm:
                                area_n += n * dt
                                area_busy += (1 if n > 0 else 0) * dt
                                area_util += min(n, c) * dt
                            last = end
                            t = end
                            queue.pop(0)
                            n -= 1
                            busy -= 1
                            if t > warm:
                                dep_w += 1
                            if queue and busy < c:
                                st, sv = queue.pop(0)
                                busy += 1
                                if t > warm:
                                    area_wait += (t - st)
                                    wait_n += 1
                                queue.append(('busy', t + sv))
                            continue
                if next_arr > H:
                    dt = H - last
                    if H > warm:
                        area_n += n * dt
                        area_busy += (1 if n > 0 else 0) * dt
                        area_util += min(n, c) * dt
                    break
                dt = next_arr - last
                if next_arr > warm:
                    area_n += n * dt
                    area_busy += (1 if n > 0 else 0) * dt
                    area_util += min(n, c) * dt
                last = next_arr
                t = next_arr
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if t > warm:
                        arr_w += 1
                    if busy < c:
                        busy += 1
                        st, sv = queue.pop(0)
                        if t > warm:
                            area_wait += (t - st)
                            wait_n += 1
                        queue.append(('busy', t + sv))
                else:
                    if t > warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)

        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = (area_wait / wait_n) if wait_n > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        pl = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        pw = wait_n / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_area += area_busy
        tot_util_area += area_util
        tot_wait_area += area_wait
        tot_wait_n += wait_n
        tot_win += win

    L = sum(per_L) / len(per_L)
    W = sum(per_W) / len(per_W)
    bf = sum(per_bf) / len(per_bf)
    pl = sum(per_pl) / len(per_pl)
    pw = sum(per_pw) / len(per_pw)
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    busy_util = (tot_util_area / tot_win) / c if tot_win > 0 else 0.0
    dep_rate = dep / (tot_win / len(seeds)) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / len(seeds)) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': tot_win / len(seeds),
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
