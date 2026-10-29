import json, random, argparse

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
        s1 = None
        s2 = None
        arr = 0
        dep = 0
        blk = 0
        busy1 = 0.0
        busy2 = 0.0
        area1 = 0.0
        area2 = 0.0
        areaW = 0.0
        nwait = 0
        ntot = 0
        last = 0.0
        while t < H:
            if s1 is None and q1:
                c = q1.pop(0)
                s1 = c
                s1['start'] = t
                s1['end'] = t + s1['svc1']
            if s2 is None and q2:
                c = q2.pop(0)
                s2 = c
                s2['start2'] = t
                s2['end2'] = t + s2['svc2']
            cand = []
            if s1 is not None:
                cand.append(s1['end'])
            if s2 is not None:
                cand.append(s2['end2'])
            ta = t + rng.expovariate(lam)
            cand.append(ta)
            tn = min(cand)
            dt = tn - t
            if t >= warm:
                area1 += len(q1) * dt
                area2 += len(q2) * dt
                if s1 is not None:
                    busy1 += dt
                if s2 is not None:
                    busy2 += dt
            t = tn
            if s1 is not None and t >= s1['end']:
                c = s1
                s1 = None
                c['t1'] = t
                q2.append(c)
            if s2 is not None and t >= s2['end2']:
                c = s2
                s2 = None
                dep += 1
                if t >= warm:
                    areaW += (t - c['arr']) 
            if abs(t - ta) < 1e-12:
                arr += 1
                ntot += 1
                c = {'arr': t, 'svc1': rng.expovariate(mu1), 'svc2': rng.expovariate(mu2)}
                if s1 is None and not q1:
                    s1 = c
                    s1['start'] = t
                    s1['end'] = t + s1['svc1']
                else:
                    q1.append(c)
                    if t >= warm:
                        nwait += 1
        win = H - warm
        L = (area1 + area2) / win if win > 0 else 0.0
        W = areaW / dep if dep > 0 else 0.0
        bf = (busy1 + busy2) / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = nwait / ntot if ntot > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    n = len(per_L)
    Lm = sum(per_L) / n if n else 0.0
    Wm = sum(per_W) / n if n else 0.0
    bfm = sum(per_bf) / n if n else 0.0
    plm = sum(per_pl) / n if n else 0.0
    pwm = sum(per_pw) / n if n else 0.0
    win = H - warm
    out = {
        'L': Lm,
        'W': Wm,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': bfm,
        'busy_util': bfm,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam * 60.0,
        'p_loss': plm,
        'p_wait': pwm,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
