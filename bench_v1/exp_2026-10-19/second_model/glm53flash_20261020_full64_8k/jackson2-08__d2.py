import argparse, json, random

def run_seed(seed, H, lam, mu1, mu2):
    rng = random.Random(seed)
    warm = 0.25 * H
    t = 0.0
    q1, q2 = [], []
    b1 = None
    b2 = None
    busy1 = busy2 = 0.0
    L_int = 0.0
    arr = dep = waited = 0
    W_sum = 0.0
    def ntot():
        return len(q1) + (1 if b1 is not None else 0) + len(q2) + (1 if b2 is not None else 0)
    next_a = rng.expovariate(lam)
    while t < H:
        cands = [(next_a, 0)]
        if b1 is not None:
            cands.append((b1[1], 1))
        if b2 is not None:
            cands.append((b2[1], 2))
        nt, et = min(cands)
        if nt >= H:
            nt = H
            et = -1
        dt = nt - t
        if t >= warm:
            L_int += ntot() * dt
            if b1 is not None: busy1 += dt
            if b2 is not None: busy2 += dt
        t = nt
        if et == -1:
            break
        if et == 0:
            inwin = t >= warm
            if inwin: arr += 1
            job = {'a': t, 's1': rng.expovariate(mu1), 's2': rng.expovariate(mu2), 'w': False}
            if b1 is None:
                b1 = (job, t + job['s1'])
            else:
                job['w'] = True
                q1.append(job)
            next_a = t + rng.expovariate(lam)
        elif et == 1:
            job = b1[0]
            b1 = None
            if q1:
                nj = q1.pop(0)
                b1 = (nj, t + nj['s1'])
            if b2 is None:
                b2 = (job, t + job['s2'])
            else:
                job['w'] = True
                q2.append(job)
        else:
            job = b2[0]
            b2 = None
            if q2:
                nj = q2.pop(0)
                b2 = (nj, t + nj['s2'])
            if t >= warm:
                dep += 1
                W_sum += t - job['a']
                if job['w']: waited += 1
    win = H - warm
    n = dep
    W = W_sum / n if n else 0.0
    L = L_int / win if win > 0 else 0.0
    bf = (busy1 + busy2) / (2.0 * win) if win > 0 else 0.0
    p_wait = waited / arr if arr else 0.0
    return {'L': L, 'W': W, 'arr': arr, 'dep': dep, 'busy_frac': bf, 'p_wait': p_wait, 'p_loss': 0.0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 10.0, 12.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == 'c_up': mu1 /= 1.1; mu2 /= 1.1
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run_seed(s, a.horizon, lam, mu1, mu2) for s in seed_list]
    n = len(per)
    avg = lambda k: sum(p[k] for p in per) / n if n else 0.0
    out = {
        'L': avg('L'), 'W': avg('W'),
        'runtime_units': a.horizon, 'seed_list': seed_list, 'seeds_used': n,
        'time_unit': 'hour', 'win': a.horizon - 0.25 * a.horizon,
        'arr': avg('arr'), 'dep': avg('dep'), 'blk': 0.0,
        'busy_frac': avg('busy_frac'), 'busy_util': avg('busy_frac'),
        'dep_rate': avg('dep') / (a.horizon - 0.25 * a.horizon) if a.horizon else 0.0,
        'lam_eff': lam, 'p_loss': 0.0, 'p_wait': avg('p_wait'),
        'per_seed_L': [p['L'] for p in per], 'per_seed_W': [p['W'] for p in per],
        'per_seed_busy_frac': [p['busy_frac'] for p in per],
        'per_seed_p_loss': [0.0 for _ in per],
        'per_seed_p_wait': [p['p_wait'] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
