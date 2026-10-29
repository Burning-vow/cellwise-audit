import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 4
        cap = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    tot_busy = 0.0; tot_util = 0.0; tot_L = 0.0; tot_W = 0.0
    tot_loss = 0.0; tot_wait = 0.0; tot_win = 0.0
    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr = 0; dep = 0; blk = 0
        areaN = 0.0; areaBusy = 0.0; areaUtil = 0.0
        areaW = 0.0; nWait = 0; nServed = 0
        win_arr = 0; win_dep = 0; win_blk = 0
        win_areaN = 0.0; win_areaBusy = 0.0; win_areaUtil = 0.0
        win_areaW = 0.0; win_nWait = 0; win_nServed = 0
        win_start = warm
        win_len = H - warm
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                if t < H:
                    d = H - t
                    areaN += n * d; areaBusy += (1 if busy > 0 else 0) * d
                    areaUtil += min(busy, c) * d
                    if t >= win_start:
                        wd = H - max(t, win_start)
                        win_areaN += n * wd
                        win_areaBusy += (1 if busy > 0 else 0) * wd
                        win_areaUtil += min(busy, c) * wd
                break
            d = t_next - t
            areaN += n * d; areaBusy += (1 if busy > 0 else 0) * d
            areaUtil += min(busy, c) * d
            if t >= win_start:
                wd = t_next - max(t, win_start)
                win_areaN += n * wd
                win_areaBusy += (1 if busy > 0 else 0) * wd
                win_areaUtil += min(busy, c) * wd
            t = t_next
            arr += 1
            if t >= win_start:
                win_arr += 1
            if n < cap:
                svc = rng.expovariate(mu)
                n += 1
                queue.append((t, svc))
                if busy < c:
                    busy += 1
                    st, s = queue.pop(0)
                    dep_t = t + s
                    if t >= win_start:
                        win_areaW += (dep_t - st)
                        win_nWait += 1
                        win_nServed += 1
                    areaW += (dep_t - st)
                    nWait += 1; nServed += 1
                    queue.append(('dep', dep_t, st))
                else:
                    queue.append(('wait', t, svc))
            else:
                blk += 1
                if t >= win_start:
                    win_blk += 1
            while queue and queue[0][0] == 'dep' and queue[0][1] <= t:
                _, dep_t, st = queue.pop(0)
                dep += 1
                if dep_t >= win_start:
                    win_dep += 1
                n -= 1
                busy -= 1
                if queue and queue[0][0] == 'wait':
                    _, wt, s = queue.pop(0)
                    busy += 1
                    nd = t + s
                    if t >= win_start:
                        win_areaW += (nd - wt)
                        win_nWait += 1
                        win_nServed += 1
                    areaW += (nd - wt)
                    nWait += 1; nServed += 1
                    queue.append(('dep', nd, wt))
        L = win_areaN / win_len if win_len > 0 else 0.0
        W = win_areaW / win_nServed if win_nServed > 0 else 0.0
        bf = win_areaBusy / win_len if win_len > 0 else 0.0
        bu = win_areaUtil / (c * win_len) if win_len > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_nWait / win_arr if win_arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pLoss.append(pl); pWait.append(pw)
        tot_arr += win_arr; tot_dep += win_dep; tot_blk += win_blk
        tot_busy += win_areaBusy; tot_util += win_areaUtil
        tot_L += win_areaN; tot_W += win_areaW
        tot_loss += win_blk; tot_wait += win_nWait
        tot_win += win_len
    ns = len(seeds)
    L = tot_L / tot_win if tot_win > 0 else 0.0
    W = tot_W / (tot_wait if tot_wait > 0 else 1)
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    busy_util = tot_util / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr_avg / (tot_win / ns) if tot_win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': tot_win / ns,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss, 'per_seed_p_wait': pWait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
