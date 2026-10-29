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
            if s1 is None:
                dt1 = float('inf')
            else:
                dt1 = s1 - t
            if s2 is None:
                dt2 = float('inf')
            else:
                dt2 = s2 - t
            dt = min(dt1, dt2)
            if dt > 0 and dt != float('inf'):
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
            if s1 is not None and s1 <= 1e-12:
                s1 = None
                if q1:
                    job = q1.pop(0)
                    s1 = job[1]
                    if t >= warm:
                        areaW += (t - job[0])
                else:
                    s1 = None
            if s2 is not None and s2 <= 1e-12:
                s2 = None
                dep += 1
                if q2:
                    job = q2.pop(0)
                    s2 = job[1]
                    if t >= warm:
                        areaW += (t - job[0])
            if s1 is None and q1:
                job = q1.pop(0)
                s1 = job[1]
                if t >= warm:
                    areaW += (t - job[0])
            if s2 is None and q2:
                job = q2.pop(0)
                s2 = job[1]
                if t >= warm:
                    areaW += (t - job[0])
            dt_next = rng.expovariate(lam)
            t_arr = t + dt_next
            if t_arr >= H:
                break
            if t >= warm:
                area1 += len(q1) * dt_next
                area2 += len(q2) * dt_next
                if s1 is not None:
                    busy1 += dt_next
                if s2 is not None:
                    busy2 += dt_next
            t = t_arr
            if s1 is not None:
                s1 -= dt_next
            if s2 is not None:
                s2 -= dt_next
            if s1 is not None and s1 <= 1e-12:
                s1 = None
                if q1:
                    job = q1.pop(0)
                    s1 = job[1]
                    if t >= warm:
                        areaW += (t - job[0])
            if s2 is not None and s2 <= 1e-12:
                s2 = None
                dep += 1
                if q2:
                    job = q2.pop(0)
                    s2 = job[1]
                    if t >= warm:
                        areaW += (t - job[0])
            if s1 is None and q1:
                job = q1.pop(0)
                s1 = job[1]
                if t >= warm:
                    areaW += (t - job[0])
            if s2 is None and q2:
                job = q2.pop(0)
                s2 = job[1]
                if t >= warm:
                    areaW += (t - job[0])
            arr += 1
            ntot += 1
            svc1 = rng.expovariate(mu1)
            svc2 = rng.expovariate(mu2)
            job = (t, svc1, svc2)
            if s1 is None:
                s1 = svc1
            else:
                q1.append((t, svc1, svc2))
                nwait += 1
        win = H - warm
        L = (area1 + area2) / win if win > 0 else 0.0
        W = areaW / dep if dep > 0 else 0.0
        bf = (busy1 + busy2) / (2.0 * win) if win > 0 else 0.0
        pl = blk / ntot if ntot > 0 else 0.0
        pw = nwait / ntot if ntot > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    n = len(per_L)
    L = sum(per_L) / n if n else 0.0
    W = sum(per_W) / n if n else 0.0
    bf = sum(per_bf) / n if n else 0.0
    pl = sum(per_pl) / n if n else 0.0
    pw = sum(per_pw) / n if n else 0.0
    win = H - warm
    dep_rate = (L / W * 60.0) if W > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam * 60.0,
        'p_loss': pl,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
