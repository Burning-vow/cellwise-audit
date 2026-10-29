import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 14.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_L = tot_W = tot_bf = tot_pl = tot_pw = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk = 0
        area_n = 0.0
        area_q = 0.0
        area_busy = 0.0
        wsum = 0.0
        wcnt = 0
        waitcnt = 0
        arrcnt = 0
        last = 0.0
        while True:
            if servers:
                nxt_dep = min(servers)
            else:
                nxt_dep = float('inf')
            if n == 0:
                nxt_arr = t + rng.expovariate(lam)
            else:
                nxt_arr = arr_times[-1] if False else t + rng.expovariate(lam)
            if nxt_arr < nxt_dep:
                dt = nxt_arr - t
                if t >= warm:
                    area_n += n * dt
                    area_q += len(queue) * dt
                    area_busy += busy * dt
                t = nxt_arr
                if t > H:
                    break
                svc = rng.expovariate(mu)
                arrcnt += 1
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        waitcnt += 1
                arr_times.append(t)
            else:
                dt = nxt_dep - t
                if t >= warm:
                    area_n += n * dt
                    area_q += len(queue) * dt
                    area_busy += busy * dt
                t = nxt_dep
                if t > H:
                    break
                servers.remove(nxt_dep)
                busy -= 1
                if queue:
                    at, svc = queue.pop(0)
                    servers.append(t + svc)
                    busy += 1
                    if t >= warm:
                        wsum += (t - at) + svc
                        wcnt += 1
                dep_times.append(t)
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        pw = waitcnt / arrcnt if arrcnt > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(0.0); pPW.append(pw)
        tot_L += L; tot_W += W; tot_bf += bf; tot_pl += 0.0; tot_pw += pw
        tot_arr += arrcnt; tot_dep += len(dep_times); tot_blk += blk
    ns = len(seeds)
    out = {
        'L': tot_L / ns,
        'W': tot_W / ns,
        'busy_frac': tot_bf / ns,
        'busy_util': tot_bf / ns,
        'busy_occupied': tot_bf / ns,
        'p_wait': tot_pw / ns,
        'p_loss': tot_pl / ns,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': tot_arr / ns,
        'dep': tot_dep / ns,
        'blk': tot_blk / ns,
        'dep_rate': (tot_dep / ns) / ((H - warm) / 60.0) if H > warm else 0.0,
        'lam_eff': lam * 60.0,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
