import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
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
    arrs = []
    deps = []
    blks = []
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_b = 0.0
        area_q = 0.0
        wsum = 0.0
        wcnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        wait_events = 0
        arr_events = 0
        last = 0.0
        while True:
            if servers:
                nxt_dep = min(servers)
            else:
                nxt_dep = float('inf')
            if n == 0:
                nxt_arr = t + rng.expovariate(lam)
            else:
                nxt_arr = t + rng.expovariate(lam)
            if nxt_arr < nxt_dep:
                dt = nxt_arr - t
                if t >= warm:
                    area_n += n * dt
                    area_b += busy * dt
                    area_q += len(queue) * dt
                t = nxt_arr
                if t > H:
                    break
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_win += 1
                    arr_events += 1
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        wait_events += 1
            else:
                dt = nxt_dep - t
                if t >= warm:
                    area_n += n * dt
                    area_b += busy * dt
                    area_q += len(queue) * dt
                t = nxt_dep
                if t > H:
                    break
                servers.remove(nxt_dep)
                n -= 1
                busy -= 1
                if t >= warm:
                    dep_win += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wsum += (t - at) + svc
                        wcnt += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_b / (c * win) if win > 0 else 0.0
        pw = wait_events / arr_events if arr_events > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        arrs.append(arr_win)
        deps.append(dep_win)
        blks.append(blk_win)
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    win = H - warm
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
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
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
