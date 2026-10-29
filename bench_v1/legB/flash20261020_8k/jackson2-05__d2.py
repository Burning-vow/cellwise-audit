import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 60.0 / 7.5
    mu2 = 60.0 / 6.0
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
        b1 = None
        b2 = None
        arr = 0
        dep = 0
        blk = 0
        area1 = 0.0
        area2 = 0.0
        areaW = 0.0
        busy1 = 0.0
        busy2 = 0.0
        waitc = 0
        arrc = 0
        last = 0.0
        while True:
            if b1 is None and q1:
                b1 = q1.pop(0)
                b1['start'] = t
            if b2 is None and q2:
                b2 = q2.pop(0)
                b2['start2'] = t
            cand = []
            if b1 is not None:
                cand.append(b1['end'])
            if b2 is not None:
                cand.append(b2['end2'])
            cand.append(t + rng.expovariate(lam))
            nt = min(cand)
            if nt > H:
                dt = H - t
                if t < H:
                    if t >= warm:
                        area1 += len(q1) * dt
                        area2 += len(q2) * dt
                        if b1 is not None:
                            busy1 += dt
                        if b2 is not None:
                            busy2 += dt
                break
            dt = nt - t
            if t >= warm:
                area1 += len(q1) * dt
                area2 += len(q2) * dt
                if b1 is not None:
                    busy1 += dt
                if b2 is not None:
                    busy2 += dt
            t = nt
            if b1 is not None and b1['end'] == t:
                b1 = None
                dep += 1
                if t >= warm:
                    areaW += t - b1_dummy if False else 0.0
            if b2 is not None and b2['end2'] == t:
                b2 = None
            if b1 is None and q1:
                b1 = q1.pop(0)
                b1['start'] = t
            if b2 is None and q2:
                b2 = q2.pop(0)
                b2['start2'] = t
            if t + 0.0 == nt and False:
                pass
            if abs(nt - (t)) < 1e-15:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['end'] == t:
                pass
            if b2 is not None and b2['end2'] == t:
                pass
            if b1 is not None and b1['
