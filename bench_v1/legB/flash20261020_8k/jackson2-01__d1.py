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
    mu2 = 1.0 / 6.0
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
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
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
        busy1 = 0.0
        busy2 = 0.0
        wait_cnt = 0
        wait_sum = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_area1 = 0.0
        win_area2 = 0.0
        win_busy1 = 0.0
        win_busy2 = 0.0
        win_wait_cnt = 0
        win_wait_sum = 0.0
        last = 0.0
        while t < H:
            if s1 is None:
                dt1 = float('inf')
            else:
                dt1 = s1
            if s2 is None:
                dt2 = float('inf')
            else:
                dt2 = s2
            dt = min(dt1, dt2)
            if dt == float('inf'):
                dt = H - t
            if t + dt > H:
                dt = H - t
            if dt > 0:
                if t >= warm:
                    area1 += len(q1) * dt
                    area2 += len(q2) * dt
                    if s1 is not None:
                        busy1 += dt
                    if s2 is not None:
                        busy2 += dt
                t += dt
                if s1 is not None:
                    s1 -= dt
                if s2 is not None:
                    s2 -= dt
            if t >= H:
                break
            if s1 is not None and s1 <= 1e-12:
                s1 = None
                dep += 1
                if t >= warm:
                    win_dep += 1
                q2.append(0.0)
                if s2 is None:
                    s2 = q2.pop(0)
                    if s2 is None:
                        s2 = 0.0
            if s2 is not None and s2 <= 1e-12:
                s2 = None
            if s1 is None and q1:
                s1 = q1.pop(0)
            if s2 is None and q2:
                s2 = q2.pop(0)
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
            if s1 is None and s2 is None
