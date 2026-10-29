import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []
    pW = []
    pB = []
    pLoss = []
    pWait = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_wait = 0.0
    tot_busy = 0.0
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
        area = 0.0
        waitsum = 0.0
        busyt = 0.0
        last = 0.0
        while True:
            if b1 > 0 and b2 > 0:
                dt = min(b1, b2)
            elif b1 > 0:
                dt = b1
            elif b2 > 0:
                dt = b2
            else:
                dt = float('inf')
            if t + dt > H:
                dt = H - t
            if t >= warm:
                area += (n1 + n2) * dt
                busyt += ((1 if b1 > 0 else 0) + (1 if b2 > 0 else 0)) * dt
            t += dt
            if b1 > 0:
                b1 -= dt
            if b2 > 0:
                b2 -= dt
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if t >= H:
                break
            if b1 <= 0 and b2 <= 0:
                dt2 = rng.expovariate(lam)
            else:
                dt2 = rng.expovariate(lam)
            if t + dt2 > H:
                break
            t += dt2
            arr += 1
            n1 += 1
            c = {'a': t, 's': rng.expovariate(mu1)}
            if b1 <= 0:
                b1 = c['s']
                if t >= warm:
                    waitsum += 0.0
            else:
                q1.append(c)
            if b1 > 0 and b1 <= 1e-12:
                pass
            while True:
                if b1 <= 0 and q1:
                    c = q1.pop(0)
                    b1 = c['s']
                    if t >= warm:
                        waitsum += (t - c['a'])
                else:
                    break
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b1 <= 0 and b2 <= 0:
                pass
            if b1 > 0 and b1 < 1e-12:
                b1 = 0.0
            if b2 > 0 and b2 < 1e-12:
                b2 = 0.0
            if b1 <= 0 and q1:
                c = q1.pop(0)
                b1 = c['s']
                if t >= warm:
                    waitsum += (t - c['a'])
            if b2 <= 0 and q2:
                c = q2.pop(0)
                b2 = c['s']
                if t >= warm:
                    waitsum += (
