import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 5.0
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
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        b1 = False
        b2 = False
        t1 = 0.0
        t2 = 0.0
        n1 = 0
        n2 = 0
        area1 = 0.0
        area2 = 0.0
        last = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        waiters = 0
        waited = 0
        while True:
            if b1:
                dt = t1 - t
            else:
                dt = math.inf
            if b2:
                dt = min(dt, t2 - t)
            if q1:
                dt = min(dt, q1[0][0] - t)
            if q2:
                dt = min(dt, q2[0][0] - t)
            if dt == math.inf:
                dt = H - t
            if t + dt > H:
                dt = H - t
            if dt > 0:
                if t >= warm:
                    area1 += n1 * dt
                    area2 += n2 * dt
                    if b1 or b2:
                        busy += dt
                t += dt
            if t >= H:
                break
            if b1 and abs(t - t1) < 1e-12:
                b1 = False
                n1 -= 1
                if t >= warm:
                    dep += 1
                q2.append((t, q2[-1][1] if False else None))
                q2[-1] = (t, q2[-1][1])
                if not b2:
                    b2 = True
                    t2 = t + q2[0][1]
                    q2.pop(0)
                    n2 += 1
                continue
            if b2 and abs(t - t2) < 1e-12:
                b2 = False
                n2 -= 1
                if q2:
                    b2 = True
                    t2 = t + q2[0][1]
                    q2.pop(0)
                    n2 += 1
                continue
            if q1 and abs(t - q1[0][0]) < 1e-12:
                svc = q1[0][1]
                q1.pop(0)
                if not b1:
                    b1 = True
                    t1 = t + svc
                    n1 += 1
                else:
                    q1.insert(0, (t, svc))
                continue
            if q2 and abs(t - q2[0][0]) < 1e-12:
                svc = q2[0][1]
                q2.pop(0)
                if not b2:
                    b2 = True
                    t2 = t + svc
                    n2 += 1
                else:
                    q2.insert(0, (t, svc))
                continue
            arr += 1
            svc1 = rng.expovariate(mu1)
            svc2 = rng.expovariate(mu2)
            if not b1:
                b1 = True
                t1 = t + svc1
                n1 += 1
            else:
                q1.append((t, svc1))
            q2.append((t, svc2))
        win = H - warm
        L = (area1 + area2) / win if win > 0 else 0.0
        W = L / (lam * 60.0) if lam > 0 else 0.0
        bf = busy / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / waiters if waiters > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    n = a.seeds
    L = sum(per_L) / n if n else 0.0
    W = sum(per_W) / n if n else 0.0
    bf = sum(per_bf) / n if n else 0.0
    pl = sum(per_pl) / n if n else 0.0
    pw = sum(per_pw) / n if n else 0.0
    win = H - warm
    dep_rate = (tot_dep / n) / win * 60.0 if win > 0 else 0.0
    lam_eff = (tot_arr / n) / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / n if n else 0.0,
        'blk': tot_blk / n if n else 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tot_dep / n if n else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
