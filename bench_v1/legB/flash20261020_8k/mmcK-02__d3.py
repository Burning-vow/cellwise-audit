import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 3
        cap = 5

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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait_n = 0.0
    tot_wait_sum = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            t_next = t + dt
            if t_next > H:
                break
            if t < warm:
                if t_next > warm:
                    area_n += n * (warm - t)
                    area_busy += (1 if busy > 0 else 0) * (warm - t)
                    area_util += min(n, c) * (warm - t)
                else:
                    area_n += n * dt
                    area_busy += (1 if busy > 0 else 0) * dt
                    area_util += min(n, c) * dt
            else:
                area_n += n * dt
                area_busy += (1 if busy > 0 else 0) * dt
                area_util += min(n, c) * dt
            t = t_next
            if n < cap:
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                queue.append((t, svc))
                if busy < c:
                    busy += 1
                    st, sv = queue.pop(0)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                    dep_t = t + sv
                    queue.append((dep_t, -1))
            else:
                if t >= warm:
                    blk_w += 1
            while queue and queue[0][1] == -1 and queue[0][0] <= t:
                queue.pop(0)
                n -= 1
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    st, sv = queue.pop(0)
                    if st >= warm:
                        wait_sum += t - st
                        wait_n += 1
                    busy += 1
                    queue.append((t + sv, -1))
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        util = area_util / (c * win) if win > 0 else 0.0
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
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
        tot_busy += bf
        tot_util += util
        tot_wait_n += wait_n
        tot_wait_sum += wait_sum
        tot_win += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = tot_util / ns

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': bf,
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
