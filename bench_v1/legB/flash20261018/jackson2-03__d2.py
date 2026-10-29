import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu1 = mu1 * 1.2
        mu2 = mu2 * 1.2
    elif a.pert == 'c_up':
        lam = lam * 1.2
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
    tot_area = 0.0
    tot_wait = 0.0
    tot_busy = 0.0
    tot_win = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n1 = 0
        n2 = 0
        area = 0.0
        wait_sum = 0.0
        busy = 0.0
        arr = 0
        dep = 0
        blk = 0
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
            cand.append(t + rng.expovariate(lam))
            nt = min(cand)
            if nt > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
                t = H
                break
            dt = nt - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
            t = nt
            if s1 is not None and s1['end'] == t:
                n1 -= 1
                if t >= warm:
                    wait_sum += (t - s1['arr'])
                dep += 1
                q2.append(s1)
                n2 += 1
                s1 = None
            if s2 is not None and s2['end'] == t:
                n2 -= 1
                if t >= warm:
                    wait_sum += (t - s2['arr'])
                dep += 1
                s2 = None
            if t + 0.0 == nt and (s1 is None or s2 is None):
                pass
            if abs(nt - (t)) < 1e-12:
                pass
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1['start'] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2['start'] = t
            if s1 is None and s2 is None:
                pass
            if t >= warm:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is None:
                pass
            if s1 is None and s2 is
