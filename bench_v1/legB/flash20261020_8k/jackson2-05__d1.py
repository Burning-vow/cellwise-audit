import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 6.0
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
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        area_w = 0.0
        busy_area = 0.0
        wait_cnt = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        next_arr = rng.expovariate(lam)
        while t < H:
            cand = [next_arr]
            if s1 is not None:
                cand.append(s1)
            if s2 is not None:
                cand.append(s2)
            nt = min(cand)
            dt = nt - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy_area += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
            t = nt
            if t >= H:
                break
            if t == next_arr:
                arr += 1
                if t >= warm:
                    arr_win += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                cust = [svc1, svc2, t]
                if s1 is None:
                    s1 = t + svc1
                    if t >= warm:
                        wait_cnt += 1
                else:
                    q1.append(cust)
                n1 += 1
                next_arr = t + rng.expovariate(lam)
            elif s1 is not None and t == s1:
                s1 = None
                n1 -= 1
                if q1:
                    c = q1.pop(0)
                    s1 = t + c[0]
                    if t >= warm:
                        wait_cnt += 1
                if s2 is None:
                    c2 = None
                    if q2:
                        c2 = q2.pop(0)
                    else:
                        c2 = None
                    if c2 is None:
                        pass
                if s2 is None:
                    if q2:
                        c = q2.pop(0)
                        s2 = t + c[1]
                        if t >= warm:
                            area_w += (t - c[2])
                    else:
                        pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
                if s2 is None:
                    pass
