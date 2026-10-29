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
    tot_occ = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        busy_area = 0.0
        occ_area = 0.0
        wait_area = 0.0
        served = 0
        last = warm
        while t < H:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            ta = t + dt
            td = next_dep
            if ta < td and ta < H:
                if ta > last:
                    seg = ta - last
                    busy_area += seg * (1.0 if busy else 0.0)
                    occ_area += seg * n
                    wait_area += seg * n
                last = ta
                t = ta
                arr_c += 1
                if n >= cap:
                    blk_c += 1
                else:
                    n += 1
                    if n == 1:
                        busy = True
                        st = rng.expovariate(mu)
                        next_dep = t + st
            elif td < H:
                if td > last:
                    seg = td - last
                    busy_area += seg * (1.0 if busy else 0.0)
                    occ_area += seg * n
                    wait_area += seg * n
                last = td
                t = td
                n -= 1
                dep_c += 1
                served += 1
                if n > 0:
                    st = rng.expovariate(mu)
                    next_dep = t + st
                else:
                    busy = False
                    next_dep = float('inf')
            else:
                if H > last:
                    seg = H - last
                    busy_area += seg * (1.0 if busy else 0.0)
                    occ_area += seg * n
                    wait_area += seg * n
                last = H
                t = H
        win = H - warm
        L = occ_area / win if win > 0 else 0.0
        W = wait_area / served if served > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = (arr_c - blk_c - 0) / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += busy_area
        tot_occ += occ_area
        tot_wait += wait_area
        tot_served += served
    ns = len(seeds)
    win = H - warm
    L = (tot_occ / ns) / win if win > 0 else 0.0
    W = (tot_wait / ns) / (tot_served / ns) if tot_served > 0 else 0.0
    busy_frac = (tot_busy / ns) / win if win > 0 else 0.0
    p_loss = (tot_blk / ns) / (tot_arr / ns) if tot_arr > 0 else 0.0
    p_wait = (tot_arr - tot_blk) / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = busy_frac
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
