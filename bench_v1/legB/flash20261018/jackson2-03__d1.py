import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    c = 1.0
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu1 = mu1 * 1.2
        mu2 = mu2 * 1.2
    elif a.pert == 'c_up':
        c = c * 1.2
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_wait = 0.0
    tot_busy = 0.0
    tot_served = 0.0
    tot_waiters = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        n1 = 0
        n2 = 0
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        wait_sum = 0.0
        busy = 0.0
        served = 0
        waiters = 0
        last = 0.0
        while True:
            if b1 > 0:
                t1 = b1
            else:
                t1 = float('inf')
            if b2 > 0:
                t2 = b2
            else:
                t2 = float('inf')
            dt = rng.expovariate(lam)
            tn = t + dt
            te = min(t1, t2)
            if te < tn:
                if te > H:
                    break
                if te > warm:
                    area += (n1 + n2) * (te - last)
                    busy += (1 if b1 > 0 else 0) * (te - last) + (1 if b2 > 0 else 0) * (te - last)
                last = te
                if t1 <= t2:
                    b1 = 0.0
                    n1 -= 1
                    if q1:
                        cust = q1.pop(0)
                        b1 = cust[1]
                        if te > warm:
                            wait_sum += te - cust[0]
                            served += 1
                            waiters += 1 if (te - cust[0]) > 0 else 0
                    if te > warm:
                        dep += 1
                    n2 += 1
                    q2.append((te, rng.expovariate(mu2)))
                    if b2 == 0.0:
                        cust = q2.pop(0)
                        b2 = cust[1]
                else:
                    b2 = 0.0
                    n2 -= 1
                    if q2:
                        cust = q2.pop(0)
                        b2 = cust[1]
                        if te > warm:
                            wait_sum += te - cust[0]
                            served += 1
                            waiters += 1 if (te - cust[0]) > 0 else 0
                t = te
            else:
                if tn > H:
                    if H > warm:
                        area += (n1 + n2) * (H - last)
                        busy += (1 if b1 > 0 else 0) * (H - last) + (1 if b2 > 0 else 0) * (H - last)
                    break
                if tn > warm:
                    area += (n1 + n2) * (tn - last)
                    busy += (1 if b1 > 0 else 0) * (tn - last) + (1 if b2 > 0 else 0) * (tn - last)
                last = tn
                t = tn
                if tn > warm:
                    arr += 1
                if rng.random() < c:
                    if tn > warm:
                        blk += 1
                else:
                    n1 += 1
                    q1.append((tn, rng.expovariate(mu1)))
                    if b1 == 0.0:
                        cust = q1.pop(0)
                        b1 = cust[1]
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = wait_sum / served if served > 0 else 0.0
        bfs = busy / (2.0 * win) if win > 0 else 0.0
        pls = blk / arr if arr > 0 else 0.0
        pws = waiters / served if served > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_wait += wait_sum
        tot_busy += busy
        tot_served += served
        tot_waiters += waiters
    n = a.seeds
    win = H - warm
    L = tot_area / (n * win) if win > 0 and n > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    arr_avg = tot_arr / n if n > 0 else 0.0
    dep_avg = tot_dep / n if n > 0 else 0.0
    blk_avg = tot_blk / n if n > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    busy_frac = tot_busy / (2.0 * n * win) if win > 0 and n > 0 else 0.0
    busy_util = busy_frac
    lam_eff = arr_avg / win if win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waiters / tot_served if tot_served > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': busy_frac,
        'busy_util': busy_util,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
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
