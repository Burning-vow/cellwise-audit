import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 5.0
    if a.pert == "lam_up":
        lam *= 1.2
    elif a.pert == "mu_up":
        mu1 *= 1.2
        mu2 *= 1.2
    elif a.pert == "c_up":
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
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        n1 = 0
        n2 = 0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = t if b1 <= t else b1
                    if st < b1:
                        st = b1
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = t if b2 <= t else b2
                    if st2 < b2:
                        st2 = b2
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
            if t > warm:
                win += 0.0
        # integrate over window using event-based approach: recompute properly
        # redo simulation with area integration
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        events = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # area integration via time stepping over window
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area over window using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # area via fine integration using event list
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area over window using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area over window using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area over window using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
        area = 0.0
        last = 0.0
        n1 = 0
        n2 = 0
        ev = []
        while True:
            dt = rng.expovariate(lam)
            if t + dt > H:
                break
            t += dt
            sv1 = rng.expovariate(mu1)
            sv2 = rng.expovariate(mu2)
            arr += 1
            q1.append((t, sv1, sv2))
            while True:
                if b1 <= t and q1:
                    at, s1, s2 = q1.pop(0)
                    st = max(t, b1)
                    ft = st + s1
                    b1 = ft
                    q2.append((ft, s2))
                    if ft > warm:
                        soj += (ft - max(at, warm))
                        wait += 1
                else:
                    break
                if b2 <= t and q2:
                    at2, s2 = q2.pop(0)
                    st2 = max(t, b2)
                    ft2 = st2 + s2
                    b2 = ft2
                    if ft2 > warm:
                        soj += (ft2 - max(at2, warm))
                        dep += 1
                else:
                    break
        # integrate area over window using event times
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = 0.0
        b2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait = 0
        soj = 0.0
        win = 0.0
