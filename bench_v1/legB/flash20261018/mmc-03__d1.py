import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wsum = 0.0
        wcnt = 0
        arr = 0
        dep = 0
        blk = 0
        waiters = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            tnext = t + dt
            if servers:
                tdep = min(servers)
            else:
                tdep = float('inf')
            if tnext < tdep:
                if tnext > H:
                    break
                area_n += n * (tnext - t)
                area_busy += busy * (tnext - t)
                area_q += len(queue) * (tnext - t)
                t = tnext
                arr += 1
                n += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    wsum += svc
                    wcnt += 1
                else:
                    queue.append((t, svc))
                    waiters += 1
            else:
                if tdep > H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                    area_q += len(queue) * (H - t)
                    t = H
                    break
                area_n += n * (tdep - t)
                area_busy += busy * (tdep - t)
                area_q += len(queue) * (tdep - t)
                t = tdep
                servers.remove(tdep)
                busy -= 1
                dep += 1
                n -= 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    wsum += (t - at) + svc
                    wcnt += 1
        win = H - warm
        if win <= 0:
            win = H
        L = area_n / H if H > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_busy / (c * H) if H > 0 else 0.0
        pw = waiters / arr if arr > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    pl = sum(per_pl) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / H if H > 0 else 0.0
    lam_eff = arr_avg / H if H > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
