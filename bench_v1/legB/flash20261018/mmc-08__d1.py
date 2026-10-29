import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 3
    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0; tbusy = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_w = 0.0
        area_busy = 0.0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        cnt_wait = 0
        cnt_adm = 0
        last = 0.0
        while True:
            if servers:
                nxt_dep = min(servers)
            else:
                nxt_dep = float('inf')
            if n == 0:
                nxt_arr = t + rng.expovariate(lam)
            else:
                nxt_arr = tarr
            if nxt_dep <= nxt_arr:
                ev = nxt_dep
            else:
                ev = nxt_arr
            if ev > H:
                dt = H - last
                if last >= warm:
                    area_n += n * dt
                    area_busy += busy * dt
                break
            dt = ev - last
            if last >= warm:
                area_n += n * dt
                area_busy += busy * dt
            last = ev
            if nxt_dep <= nxt_arr:
                t = nxt_dep
                servers.remove(t)
                busy -= 1
                n -= 1
                if last >= warm:
                    cnt_dep += 1
                if queue:
                    arr_t, svc = queue.pop(0)
                    start = t
                    if last >= warm:
                        area_w += (start - arr_t)
                    servers.append(t + svc)
                    busy += 1
                    n += 1
            else:
                t = nxt_arr
                svc = rng.expovariate(mu)
                if last >= warm:
                    cnt_arr += 1
                if busy < c:
                    if last >= warm:
                        cnt_adm += 1
                    servers.append(t + svc)
                    busy += 1
                    n += 1
                else:
                    if last >= warm:
                        cnt_blk += 1
                        cnt_wait += 1
                    queue.append((t, svc))
                    n += 1
                if n == 0:
                    pass
                tarr = t + rng.expovariate(lam)
                n = n
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = area_w / cnt_adm if cnt_adm > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        pw = cnt_wait / cnt_arr if cnt_arr > 0 else 0.0
        pl = cnt_blk / cnt_arr if cnt_arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(pl); pPW.append(pw)
        tarr += cnt_arr; tdep += cnt_dep; tblk += cnt_blk; tbusy += area_busy
    ns = len(seeds)
    win = H - warm
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pw = sum(pPW) / ns
    pl = sum(pPL) / ns
    arr = tarr / ns
    dep = tdep / ns
    blk = tblk / ns
    dep_rate = dep / win if win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_wait': pw,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': bf,
        'busy_occupied': bf, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_loss': pl,
        'per_seed_L': pL, 'per_seed_W': pW,
        'per_seed_busy_frac': pB, 'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
