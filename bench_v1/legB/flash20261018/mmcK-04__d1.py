import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 10.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    nseeds = a.seeds
    seed_list = [a.seed_start + i for i in range(nseeds)]

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
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    win_total = 0.0

    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_area = 0.0
        util_area = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_cnt_w = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                break
            busy_area += (min(n, c)) * (t_next - t)
            util_area += (min(n, c)) * (t_next - t)
            t = t_next
            if n < cap:
                n += 1
                svc = rng.expovariate(mu)
                cust = {'arr': t, 'svc': svc}
                if busy < c:
                    busy += 1
                    cust['start'] = t
                    servers.append(cust)
                else:
                    queue.append(cust)
                if t >= warm:
                    arr_w += 1
            else:
                if t >= warm:
                    blk_w += 1
            while servers:
                fin = min(x['start'] + x['svc'] for x in servers)
                if fin > t_next:
                    break
                done = [x for x in servers if x['start'] + x['svc'] <= fin + 1e-12]
                for x in done:
                    servers.remove(x)
                    n -= 1
                    busy -= 1
                    if x['arr'] >= warm:
                        dep_w += 1
                        wait_sum += x['start'] - x['arr']
                        waited_cnt += 1
                        dep_cnt_w += 1
                while queue and busy < c:
                    cust = queue.pop(0)
                    cust['start'] = fin
                    servers.append(cust)
                    busy += 1
                t = fin
                busy_area += (min(n, c)) * 0.0
        busy_area += (min(n, c)) * (H - t)
        util_area += (min(n, c)) * (H - t)
        win = H - warm
        L = busy_area / win if win > 0 else 0.0
        W = (wait_sum / waited_cnt) if waited_cnt > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
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
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_w += dep_cnt_w
        win_total += win

    L = tot_busy_area / win_total if win_total > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    busy_frac = tot_busy_area / win_total if win_total > 0 else 0.0
    busy_util = tot_util_area / (c * win_total) if win_total > 0 else 0.0
    p_loss = tot_blk / (tot_arr + tot_blk) if (tot_arr + tot_blk) > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0
    lam_eff = tot_arr / (win_total / 60.0) if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'time_unit': 'minute',
        'win': win_total / nseeds,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
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
