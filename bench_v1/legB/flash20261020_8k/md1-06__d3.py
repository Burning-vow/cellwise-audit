import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait_n = 0
    tot_wait_sum = 0.0
    tot_dep_n = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        server_free = 0.0
        area = 0.0
        busy_area = 0.0
        arr_c = dep_c = blk_c = 0
        wait_sum = 0.0
        wait_n = 0
        dep_n = 0
        last_t = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait_sum = 0.0
        win_wait_n = 0
        win_dep_n = 0
        win_start = warm
        win_len = H - warm

        events = []
        while True:
            if next_arr <= server_free and next_arr <= H:
                nt = next_arr
            elif server_free <= H:
                nt = server_free
            else:
                nt = H
            if nt > H:
                nt = H
            dt = nt - t
            if dt > 0:
                if t >= win_start:
                    win_area += n * dt
                    win_busy += (1 if busy > 0 else 0) * dt
                elif nt > win_start:
                    frac = nt - win_start
                    win_area += n * frac
                    win_busy += (1 if busy > 0 else 0) * frac
                area += n * dt
                busy_area += (1 if busy > 0 else 0) * dt
            t = nt
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12 and next_arr <= H:
                arr_c += 1
                if t >= win_start:
                    win_arr += 1
                svc = 1.0 / mu
                cust = {'arr': t, 'svc': svc}
                if busy < c:
                    busy += 1
                    server_free = t + svc
                    cust['start'] = t
                    cust['dep'] = t + svc
                    queue.append(cust)
                else:
                    blk_c += 1
                    if t >= win_start:
                        win_blk += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue:
                    done = [q for q in queue if abs(q.get('dep', -1) - t) < 1e-12]
                    for q in done:
                        queue.remove(q)
                        dep_c += 1
                        dep_n += 1
                        w = q['dep'] - q['arr']
                        wait_sum += w
                        wait_n += 1
                        if t >= win_start:
                            win_dep += 1
                            win_dep_n += 1
                            win_wait_sum += w
                            win_wait_n += 1
                        busy -= 1
                        n -= 1
                    if busy > 0 and queue:
                        nxt = min(queue, key=lambda q: q['dep'])
                        server_free = nxt['dep']
                    else:
                        server_free = float('inf')
                else:
                    server_free = float('inf')

        Ls = win_area / win_len if win_len > 0 else 0.0
        Ws = (win_wait_sum / win_wait_n) if win_wait_n > 0 else 0.0
        bfs = win_busy / win_len if win_len > 0 else 0.0
        pls = win_blk / win_arr if win_arr > 0 else 0.0
        pws = (win_wait_n / win_dep_n) if win_dep_n > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_win += win_len
        tot_wait_sum += win_wait_sum
        tot_wait_n += win_wait_n
        tot_dep_n += win_dep_n

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_sum / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac / c
    busy_occupied = busy_frac
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_dep_n if tot_dep_n > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'hour', 'win': tot_win / len(seeds),
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'busy_occupied': busy_occupied, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
