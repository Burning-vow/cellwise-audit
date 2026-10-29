import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 3
    cap = 4
    lam = 6.0
    mu = 5.0
    if a.pert == 'lam_up':
        lam = 6.0 * 1.25
    elif a.pert == 'mu_up':
        mu = 5.0 * 1.25
    elif a.pert == 'c_up':
        c = 4
        cap = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        win_start = warm
        win_len = H - warm
        arr_w = 0; dep_w = 0; blk_w = 0
        wait_sum = 0.0; wait_cnt = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                break
            area_n += n * (t_next - t)
            area_busy += busy * (t_next - t)
            area_occ += (1 if n > 0 else 0) * (t_next - t)
            t = t_next
            if t >= win_start:
                arr_w += 1
            if n < cap:
                svc = rng.expovariate(mu)
                cust = {'arr': t, 'svc': svc}
                n += 1
                if busy < c:
                    busy += 1
                    servers.append((t + svc, cust))
                else:
                    queue.append(cust)
            else:
                if t >= win_start:
                    blk_w += 1
            while servers and servers[0][0] <= t:
                _, cu = servers.pop(0)
                busy -= 1
                if t >= win_start:
                    dep_w += 1
                    wait_sum += (t - cu['arr'] - cu['svc'])
                    wait_cnt += 1
                if queue:
                    nxt = queue.pop(0)
                    busy += 1
                    servers.append((t + nxt['svc'], nxt))
                    servers.sort(key=lambda x: x[0])
        area_n += n * (H - t)
        area_busy += busy * (H - t)
        area_occ += (1 if n > 0 else 0) * (H - t)
        L = area_n / win_len
        W = (area_n / max(dep_w, 1e-9)) * 60.0 if dep_w > 0 else 0.0
        bf = area_occ / win_len
        pl = blk_w / max(arr_w, 1e-9)
        pw = wait_cnt / max(dep_w, 1e-9)
        pL.append(L); pW.append(W); pB.append(bf); pLoss.append(pl); pWait.append(pw)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pLoss) / ns
    pw = sum(pWait) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = H - warm
    dep_rate = dep / win
    lam_eff = arr / win
    busy_util = min(L, c) / c
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'busy_occupied': bf, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss, 'per_seed_p_wait': pWait
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
