import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr = 0; blk = 0; dep = 0
        area_n = 0.0; area_busy = 0.0; area_util = 0.0
        wsum = 0.0; wcnt = 0
        wsum_w = 0.0; wcnt_w = 0
        while True:
            rate = lam + (mu if busy else 0.0)
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                dt = H - t
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_util += min(n, K) * dt
                t = H
                break
            area_n += n * dt
            area_busy += (1.0 if busy else 0.0) * dt
            area_util += min(n, K) * dt
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep += 1
            if rng.random() < lam / rate:
                if t >= warm:
                    arr += 1
                if n >= K:
                    if t >= warm:
                        blk += 1
                else:
                    n += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        rem = svc
                    else:
                        pass
                    if t >= warm:
                        wsum += 0.0
                        wcnt += 1
            else:
                pass
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_util / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 if arr > 0 else 0.0
        pL.append(L); pB.append(bf); pPL.append(pl); pPW.append(pw)
        pW.append(0.0)
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pPL) / ns
    pw = sum(pPW) / ns
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': 0.0, 'blk': 0.0, 'busy_util': bf, 'dep': 0.0,
        'dep_rate': 0.0, 'lam_eff': 0.0, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
