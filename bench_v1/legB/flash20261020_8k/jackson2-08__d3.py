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
        s1 = None
        s2 = None
        arr = 0
        dep = 0
        blk = 0
        area1 = 0.0
        area2 = 0.0
        areaW = 0.0
        busy1 = 0.0
        busy2 = 0.0
        nwait = 0
        narr = 0
        last = 0.0
        while t < H:
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1['start'] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2['start'] = t
            cand = []
            if s1 is not None:
                cand.append(s1['end'])
            if s2 is not None:
                cand.append(s2['end'])
            cand.append(t + rng.expovariate(lam))
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area1 += len(q1) * dt
                area2 += len(q2) * dt
                if s1 is not None:
                    busy1 += dt
                if s2 is not None:
                    busy2 += dt
            t = nt
            if s1 is not None and s1['end'] <= t:
                d = s1
                s1 = None
                d['t2'] = t
                q2.append(d)
                if t >= warm:
                    dep += 1
                    areaW += t - d['arr']
            if s2 is not None and s2['end'] <= t:
                s2 = None
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t >= H:
                break
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and s2 is None and not q1 and not q2:
                pass
            if s1 is None and
