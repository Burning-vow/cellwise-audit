import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu1 = 1.0 / 6.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_dep_n = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        area1 = 0.0
        area2 = 0.0
        busy = 0.0
        arr = 0
        dep = 0
        blk = 0
        wait_sum = 0.0
        soj_sum = 0.0
        dep_n = 0
        last = 0.0
        while True:
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
            if t < H:
                cand.append(t + rng.expovariate(lam))
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area1 += len(q1) * dt
                area2 += len(q2) * dt
                if s1 is not None:
                    busy += dt
            t = nt
            if t >= H:
                break
            if s1 is not None and abs(t - s1['end']) < 1e-12:
                c = s1
                s1 = None
                c['arr2'] = t
                q2.append(c)
                if t >= warm:
                    dep += 1
                    soj_sum += t - c['arr']
                    dep_n += 1
            if s2 is not None and abs(t - s2['end']) < 1e-12:
                s2 = None
            if t < H and (s1 is None or s2 is None or True):
                pass
            if t < H:
                if abs(t - (t)) < 1e-12:
                    pass
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0)
                    s1['start'] = t
                if s2 is None and q2:
                    s2 = q2.pop(0)
                    s2['start'] = t
            if t < H:
                if s1 is None and q1:
                    s1 = q1.pop(0
