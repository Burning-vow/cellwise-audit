import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = 4.8
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 12.0
    elif a.pert == 'c_up':
        lam = 4.0
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        q1 = []
        q2 = []
        busy1 = False
        busy2 = False
        rem1 = 0.0
        rem2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        area1 = 0.0
        area2 = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_cnt = 0
        last = 0.0
        while t < H:
            if not busy1:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    area1 += len(q1) * (H - t)
                    area2 += len(q2) * (H - t)
                    busy_area += (1.0 if busy1 else 0.0) * (H - t)
                    busy_area += (1.0 if busy2 else 0.0) * (H - t)
                    t = H
                    break
                area1 += len(q1) * (nt - t)
                area2 += len(q2) * (nt - t)
                busy_area += (1.0 if busy1 else 0.0) * (nt - t)
                busy_area += (1.0 if busy2 else 0.0) * (nt - t)
                t = nt
                arr += 1
                svc = rng.expovariate(mu1)
                q1.append(svc)
                busy1 = True
                rem1 = q1.pop(0)
            else:
                dt = rem1
                nt = t + dt
                if nt > H:
                    area1 += len(q1) * (H - t)
                    area2 += len(q2) * (H - t)
                    busy_area += (1.0 if busy1 else 0.0) * (H - t)
                    busy_area += (1.0 if busy2 else 0.0) * (H - t)
                    t = H
                    break
                area1 += len(q1) * (nt - t)
                area2 += len(q2) * (nt - t)
                busy_area += (1.0 if busy1 else 0.0) * (nt - t)
                busy_area += (1.0 if busy2 else 0.0) * (nt - t)
                t = nt
                busy1 = False
                svc2 = rng.expovariate(mu2)
                q2.append(svc2)
                if not busy2:
                    busy2 = True
                    rem2 = q2.pop(0)
            if busy2:
                dt = rem2
                nt = t + dt
                if nt > H:
                    area1 += len(q1) * (H - t)
                    area2 += len(q2) * (H - t)
                    busy_area += (1.0 if busy1 else 0.0) * (H - t)
                    busy_area += (1.0 if busy2 else 0.0) * (H - t)
                    t = H
                    break
                area1 += len(q1) * (nt - t)
                area2 += len(q2) * (nt - t)
                busy_area += (1.0 if busy1 else 0.0) * (nt - t)
                busy_area += (1.0 if busy2 else 0.0) * (nt - t)
                t = nt
                busy2 = False
                dep += 1
                if not q2:
                    pass
                else:
                    rem2 = q2.pop(0)
                    busy2 = True
        win = H - warm
        L = (area1 + area2) / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        bf = busy_area / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    n = len(per_L)
    L = sum(per_L) / n if n else 0.0
    W = sum(per_W) / n if n else 0.0
    bf = sum(per_bf) / n if n else 0.0
    pl = sum(per_pl) / n if n else 0.0
    pw = sum(per_pw) / n if n else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam,
        'p_loss': pl,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
