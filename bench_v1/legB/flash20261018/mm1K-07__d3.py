import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    cap = 6
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        cap = cap + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tArr = 0.0; tDep = 0.0; tBlk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        areaN = 0.0
        areaBusy = 0.0
        areaOcc = 0.0
        arr = 0; dep = 0; blk = 0
        waitSum = 0.0; waitCnt = 0
        queue = []
        server_free = True
        next_arr = rng.expovariate(lam)
        while t < H:
            if server_free and queue:
                cust = queue.pop(0)
                server_free = False
                svc_end = t + cust['svc']
                nxt = min(next_arr, svc_end)
            elif server_free:
                nxt = next_arr
            elif queue:
                nxt = min(next_arr, queue[0].get('end', float('inf')))
            else:
                nxt = next_arr
            if server_free and queue:
                pass
            if not server_free:
                nxt = min(next_arr, svc_end)
            dt = nxt - t
            if t >= warm:
                areaN += n * dt
                areaBusy += (1 if not server_free else 0) * dt
                areaOcc += min(n, cap) * dt
            t = nxt
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                arr += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    cust = {'svc': svc, 'arr': t}
                    if server_free:
                        server_free = False
                        svc_end = t + svc
                        waitSum += 0.0
                        waitCnt += 1
                    else:
                        queue.append(cust)
                    n += 1
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep += 1
                n -= 1
                server_free = True
                if queue:
                    cust = queue.pop(0)
                    server_free = False
                    svc_end = t + cust['svc']
                    waitSum += t - cust['arr']
                    waitCnt += 1
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        bu = areaOcc / (win * cap) if win > 0 else 0.0
        W = (waitSum / waitCnt) if waitCnt > 0 else 0.0
        loss = blk / arr if arr > 0 else 0.0
        pw = waitCnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pLoss.append(loss); pWait.append(pw)
        tArr += arr; tDep += dep; tBlk += blk
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    loss = sum(pLoss) / ns
    pw = sum(pWait) / ns
    win = H - warm
    dep_rate = (tDep / ns) / win if win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': tArr / ns, 'blk': tBlk / ns, 'busy_util': bf,
        'dep': tDep / ns, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss, 'per_seed_p_wait': pWait,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
