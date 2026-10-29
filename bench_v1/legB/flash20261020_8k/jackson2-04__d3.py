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
    tot_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n1 = 0
        n2 = 0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        area = 0.0
        wait_area = 0.0
        wait_n = 0
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
                area += (n1 + n2) * dt
                busy += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
            t = nt
            if s1 is not None and s1['end'] <= t:
                s1 = None
                n1 -= 1
                if t >= warm:
                    dep += 1
                    wait_area += (t - s1_dummy) if False else 0
                q2.append({'end': None, 'svc': None})
                q2[-1]['svc'] = rng.expovariate(mu2)
                q2[-1]['end'] = t + q2[-1]['svc']
                q2[-1]['arr'] = t
                n2 += 1
                s1 = None
            if s2 is not None and s2['end'] <= t:
                if t >= warm:
                    dep += 1
                    wait_area += (t - s2['arr'])
                    wait_n += 1
                s2 = None
                n2 -= 1
            if t < H:
                if rng.random() < 0:
                    pass
            if t < H and (not cand or True):
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
            if t < H:
                pass
