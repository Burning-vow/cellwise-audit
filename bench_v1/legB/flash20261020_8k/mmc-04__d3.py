import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 10.0 / 60.0
    mu = 1.0 / 10.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3
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
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        pw_cnt = 0
        arr_cnt = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if servers:
                tdep = min(servers)
            else:
                tdep = float('inf')
            if next_arr < tdep:
                tnext = next_arr
                ev = 'a'
            else:
                tnext = tdep
                ev = 'd'
            if tnext > H:
                dt = H - last
                if last >= warm:
                    area_n += n * dt
                    area_busy += busy * dt
                    area_q += len(queue) * dt
                break
            dt = tnext - last
            if last >= warm:
                area_n += n * dt
                area_busy += busy * dt
                area_q += len(queue) * dt
            last = tnext
            if ev == 'a':
                n += 1
                svc = rng.expovariate(mu)
                if last >= warm:
                    arr_win += 1
                    arr_cnt += 1
                if busy < c:
                    busy += 1
                    servers.append(last + svc)
                    if last >= warm:
                        wait_sum += svc
                        wait_cnt += 1
                else:
                    queue.append((last, svc))
                    if last >= warm:
                        pw_cnt += 1
                next_arr = last + rng.expovariate(lam)
            else:
                tdone = min(servers)
                servers.remove(tdone)
                busy -= 1
                if last >= warm:
                    dep_win += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(last + svc)
                    if last >= warm:
                        wait_sum += (last - at) + svc
                        wait_cnt += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        pl = blk_win / arr_win if arr_win > 0 else 0.0
        pw = pw_cnt / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
    ns = len(per_L)
    L = sum(per_L) / ns if ns else 0.0
    W = sum(per_W) / ns if ns else 0.0
    bf = sum(per_bf) / ns if ns else 0.0
    pl = sum(per_pl) / ns if ns else 0.0
    pw = sum(per_pw) / ns if ns else 0.0
    win = H - warm
    arr = tot_arr / ns if ns else 0.0
    dep = tot_dep / ns if ns else 0.0
    blk = tot_blk / ns if ns else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': dep,
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
