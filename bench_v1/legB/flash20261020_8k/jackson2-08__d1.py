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
        busy1 = 0.0
        busy2 = 0.0
        area1 = 0.0
        area2 = 0.0
        area_sys = 0.0
        last = 0.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        n_wait = 0
        n_serv = 0
        sum_wait = 0.0
        sum_stay = 0.0
        n_stay = 0
        next_arr = rng.expovariate(lam)
        s1 = None
        s2 = None
        while t < H:
            dt = next_arr - t
            if s1 is not None and s1 < dt:
                dt = s1
            if s2 is not None and s2 < dt:
                dt = s2
            if dt > 0:
                if t >= warm:
                    area1 += len(q1) * dt
                    area2 += len(q2) * dt
                    area_sys += (len(q1) + len(q2)) * dt
                t += dt
                if s1 is not None:
                    s1 -= dt
                if s2 is not None:
                    s2 -= dt
            if t >= H:
                break
            if s1 is not None and s1 <= 1e-12:
                s1 = None
                busy1 += 0.0
                if q1:
                    job = q1.pop(0)
                    job['start'] = t
                    sum_wait += t - job['arr']
                    n_wait += 1
                    s1 = job['svc1']
                    busy1 += job['svc1']
                    q2.append(job)
                else:
                    busy1 += 0.0
            if s2 is not None and s2 <= 1e-12:
                s2 = None
                if q2:
                    job = q2.pop(0)
                    s2 = job['svc2']
                    busy2 += job['svc2']
                    job['dep'] = t + job['svc2']
                    n_dep += 1
                    sum_stay += (t + job['svc2']) - job['arr']
                    n_stay += 1
            if next_arr <= t + 1e-12:
                n_arr += 1
                job = {'arr': t, 'svc1': rng.expovariate(mu1), 'svc2': rng.expovariate(mu2)}
                if s1 is None:
                    s1 = job['svc1']
                    busy1 += job['svc1']
                    job['start'] = t
                    sum_wait += 0.0
                    n_wait += 1
                    q2.append(job)
                else:
                    q1.append(job)
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = area_sys / win if win > 0 else 0.0
        W = (sum_stay / n_stay) if n_stay > 0 else 0.0
        bf = (busy1 + busy2) / (2.0 * win) if win > 0 else 0.0
        pl = n_blk / n_arr if n_arr > 0 else 0.0
        pw = n_wait / n_arr if n_arr > 0 else 0.0
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
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam,
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
