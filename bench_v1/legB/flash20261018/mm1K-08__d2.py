import json, random, argparse, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 12.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pPW = []
    t0 = time.time()
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area = 0.0
        area_busy = 0.0
        area_occ = 0.0
        arr = 0; blk = 0; dep = 0; waitc = 0
        wait_sum = 0.0
        soj_sum = 0.0
        soj_cnt = 0
        queue = []
        while True:
            rate = lam + (mu if n > 0 else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    area += n * (H - t)
                    area_busy += (1.0 if n > 0 else 0.0) * (H - t)
                    area_occ += (1.0 if n > 0 else 0.0) * (H - t)
                t = H
                break
            if t >= warm:
                area += n * (nt - t)
                area_busy += (1.0 if n > 0 else 0.0) * (nt - t)
                area_occ += (1.0 if n > 0 else 0.0) * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                if t >= warm:
                    arr += 1
                if n < K:
                    svc = rng.expovariate(mu)
                    if n == 0:
                        n = 1
                        busy = t + svc
                        if t >= warm:
                            wait_sum += 0.0
                            soj_sum += svc
                            soj_cnt += 1
                    else:
                        n += 1
                        queue.append((t, svc))
                else:
                    if t >= warm:
                        blk += 1
            else:
                if n > 0:
                    if queue:
                        at, svc = queue.pop(0)
                        if t >= warm:
                            wait_sum += (t - at)
                            soj_sum += (t - at) + svc
                            soj_cnt += 1
                            waitc += 1
                        busy = t + svc
                    else:
                        n = 0
                        busy = 0.0
                        if t >= warm:
                            dep += 1
        win = H - warm
        Lv = area / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_occ / win if win > 0 else 0.0
        Wv = (soj_sum / soj_cnt) if soj_cnt > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waitc / arr if arr > 0 else 0.0
        pL.append(Lv); pW.append(Wv); pB.append(bf); pP.append(pl); pPW.append(pw)
    rt = time.time() - t0
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pP) / ns
    pw = sum(pPW) / ns
    win = H - warm
    dep_rate = (L * 60.0 / W) if W > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': rt, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': 0.0, 'blk': 0.0, 'busy_util': bf, 'dep': 0.0,
        'dep_rate': dep_rate, 'lam_eff': lam, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
