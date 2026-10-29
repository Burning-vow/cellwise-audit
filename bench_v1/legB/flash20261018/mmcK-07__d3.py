import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 5.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
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
    tot_busy_area = 0.0
    tot_util_area = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        next_arr = rng.expovariate(lam)
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_area = 0.0
        util_area = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        last_t = 0.0
        while True:
            if next_arr <= t:
                ev_t = next_arr
            else:
                ev_t = next_arr
            if servers:
                ev_t = min(ev_t, min(servers))
            if ev_t > H:
                dt = H - t
                busy_area += busy * dt
                util_area += min(n, c) * dt
                t = H
                break
            dt = ev_t - t
            busy_area += busy * dt
            util_area += min(n, c) * dt
            t = ev_t
            if servers and min(servers) <= t + 1e-12 and (not queue or min(servers) <= next_arr):
                pass
            if servers and min(servers) <= t + 1e-12:
                st = min(servers)
                servers.remove(st)
                busy -= 1
                n -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    arr_t, svc = queue.pop(0)
                    start = t
                    wait = start - arr_t
                    if t >= warm:
                        wait_sum += wait
                        waited_cnt += 1
                    servers.append(t + svc)
                    busy += 1
                    n += 1
            else:
                if t >= warm:
                    arr_w += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    if busy < c:
                        servers.append(t + svc)
                        busy += 1
                        n += 1
                    else:
                        queue.append((t, svc))
                        n += 1
                else:
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = busy_area / H if H > 0 else 0.0
        Lw = 0.0
        W = wait_sum / waited_cnt if waited_cnt > 0 else 0.0
        bf = busy_area / H if H > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waited_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_area += busy_area
        tot_util_area += util_area
        tot_win += win
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_win += dep_w

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    busy_util = (tot_util_area / (tot_win * c)) if tot_win > 0 else 0.0
    busy_occupied = busy_frac
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
