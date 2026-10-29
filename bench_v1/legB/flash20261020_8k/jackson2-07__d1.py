import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 12.0
    elif a.pert == 'c_up':
        mu1 = 10.0
        mu2 = 10.0
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
    tot_served = 0
    tot_waiters = 0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n1 = 0
        n2 = 0
        area = 0.0
        wait_sum = 0.0
        busy = 0.0
        arr = 0
        dep = 0
        blk = 0
        served = 0
        waiters = 0
        last = 0.0
        while True:
            if s1 is None:
                t1 = float('inf')
            else:
                t1 = s1
            if s2 is None:
                t2 = float('inf')
            else:
                t2 = s2
            tn = t + rng.expovariate(lam)
            te = min(t1, t2, tn)
            if te > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += (1 if s1 is not None else 0) * dt + (1 if s2 is not None else 0) * dt
                t = H
                break
            dt = te - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += (1 if s1 is not None else 0) * dt + (1 if s2 is not None else 0) * dt
            t = te
            if te == tn:
                arr += 1
                svc = rng.expovariate(mu1)
                if s1 is None:
                    s1 = t + svc
                    n1 += 1
                    if t >= warm:
                        wait_sum += 0.0
                        served += 1
                else:
                    q1.append((t, svc))
                    n1 += 1
            elif te == t1:
                s1 = None
                n1 -= 1
                if q1:
                    at, svc = q1.pop(0)
                    s1 = t + svc
                    if t >= warm:
                        wait_sum += (t - at)
                        served += 1
                        waiters += 1
                if s2 is None:
                    svc2 = rng.expovariate(mu2)
                    s2 = t + svc2
                    n2 += 1
                else:
                    q2.append((t, rng.expovariate(mu2)))
                    n2 += 1
            else:
                s2 = None
                n2 -= 1
                dep += 1
                if q2:
                    at, svc = q2.pop(0)
                    s2 = t + svc
                    if t >= warm:
                        wait_sum += (t - at)
                        served += 1
                        waiters += 1
        win = H - warm
        if win <= 0:
            win = H
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
    if win <= 0:
        win = H
    L = tot_area / (n * win) if n > 0 and win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    arr_avg = tot_arr / n if n > 0 else 0.0
    dep_avg = tot_dep / n if n > 0 else 0.0
    blk_avg = tot_blk / n if n > 0 else 0.0
    busy_frac = tot_busy / (2.0 * n * win) if n > 0 and win > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
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
        'busy_util': busy_frac,
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
