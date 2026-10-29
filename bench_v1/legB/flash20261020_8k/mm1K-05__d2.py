import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0
    mu = 10.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        queue = []
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                area_n += n * (H - t)
                area_busy += (1.0 if busy else 0.0) * (H - t)
                area_util += (1.0 if busy else 0.0) * (H - t)
                t = H
                break
            area_n += n * (nt - t)
            area_busy += (1.0 if busy else 0.0) * (nt - t)
            area_util += (1.0 if busy else 0.0) * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr_c += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    n += 1
                    if not busy:
                        busy = True
                        st, sv = queue.pop(0)
                        wait_sum += t - st
                        wait_n += 1
                        endt = t + sv
                else:
                    blk_c += 1
            else:
                dep_c += 1
                n -= 1
                if queue:
                    st, sv = queue.pop(0)
                    wait_sum += t - st
                    wait_n += 1
                    endt = t + sv
                else:
                    busy = False
                    endt = float('inf')
            while busy and endt <= t:
                dep_c += 1
                n -= 1
                if queue:
                    st, sv = queue.pop(0)
                    wait_sum += t - st
                    wait_n += 1
                    endt = t + sv
                else:
                    busy = False
                    endt = float('inf')
        win = H - warm
        if win <= 0:
            win = H
            warm = 0.0
        L = area_n / H
        bf = area_busy / H
        util = area_util / H
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += bf
        tot_util += util
        tot_wait += wait_sum
        tot_waitn += wait_n
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / H
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
        'win': H,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
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
