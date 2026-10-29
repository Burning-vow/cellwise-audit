import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 60.0/6.0
    mu2 = 60.0/5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu1 *= 1.2
        mu2 *= 1.2
    elif a.pert == 'c_up':
        lam *= 1.2
        mu1 *= 1.2
        mu2 *= 1.2
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
        area = 0.0
        area_busy = 0.0
        area_wait = 0.0
        n_wait = 0
        last = 0.0
        while t < H:
            if not busy1:
                dt = rng.expovariate(lam)
                t += dt
                if t >= H:
                    break
                svc = rng.expovariate(mu1)
                q1.append(svc)
                arr += 1
                busy1 = True
                rem1 = q1.pop(0)
            else:
                dt = rng.expovariate(lam)
                t += dt
                if t >= H:
                    break
                svc = rng.expovariate(mu1)
                q1.append(svc)
                arr += 1
            if t > warm:
                area += (t - last) * (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0))
                area_busy += (t - last) * ((1 if busy1 else 0) + (1 if busy2 else 0))
            last = t
            while True:
                if busy1:
                    if rem1 <= 0:
                        busy1 = False
                        if q1:
                            rem1 = q1.pop(0)
                            busy1 = True
                        else:
                            rem1 = 0.0
                    else:
                        break
                else:
                    break
            if busy1:
                step = rem1
                if t + step > H:
                    step = H - t
                t += step
                rem1 -= step
                if t > warm:
                    area += (t - last) * (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0))
                    area_busy += (t - last) * ((1 if busy1 else 0) + (1 if busy2 else 0))
                last = t
                if rem1 <= 0:
                    busy1 = False
                    q2.append(0.0)
                    if not busy2:
                        busy2 = True
                        rem2 = rng.expovariate(mu2)
            else:
                if not busy2 and q2:
                    busy2 = True
                    rem2 = rng.expovariate(mu2)
                if busy2:
                    step = rem2
                    if t + step > H:
                        step = H - t
                    t += step
                    rem2 -= step
                    if t > warm:
                        area += (t - last) * (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0))
                        area_busy += (t - last) * ((1 if busy1 else 0) + (1 if busy2 else 0))
                    last = t
                    if rem2 <= 0:
                        busy2 = False
                        dep += 1
                        if q2:
                            busy2 = True
                            rem2 = rng.expovariate(mu2)
                else:
                    dt = rng.expovariate(lam)
                    t += dt
                    if t >= H:
                        break
                    svc = rng.expovariate(mu1)
                    q1.append(svc)
                    arr += 1
                    if not busy1:
                        busy1 = True
                        rem1 = q1.pop(0)
                    if t > warm:
                        area += (t - last) * (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0))
                        area_busy += (t - last) * ((1 if busy1 else 0) + (1 if busy2 else 0))
                    last = t
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        bf = area_busy / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = n_wait / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    n = len(per_L)
    out = {
        'L': sum(per_L)/n if n else 0.0,
        'W': sum(per_W)/n if n else 0.0,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': sum(per_bf)/n if n else 0.0,
        'busy_util': sum(per_bf)/n if n else 0.0,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam,
        'p_loss': sum(per_pl)/n if n else 0.0,
        'p_wait': sum(per_pw)/n if n else 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
