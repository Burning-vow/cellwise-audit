import argparse, json, math, random, sys

def run_seed(seed, lam, mu1, mu2, H):
    rnd = random.Random(seed)
    warm = 0.25 * H
    INF = math.inf
    t = 0.0
    q1 = []; q2 = []
    b1 = False; b2 = False
    dep1 = INF; dep2 = INF
    next_arr = rnd.expovariate(lam)
    area = 0.0; busy1 = 0.0; busy2 = 0.0; last = 0.0
    arr = 0; dep = 0; soj = 0.0; nw = 0
    def integ(now):
        nonlocal area, busy1, busy2, last
        lo = max(last, warm)
        if now > lo:
            n = len(q1) + len(q2) + (1 if b1 else 0) + (1 if b2 else 0)
            dt = now - lo
            area += n * dt
            if b1: busy1 += dt
            if b2: busy2 += dt
        last = now
    while t < H:
        t = min(next_arr, dep1, dep2)
        if t >= H:
            integ(H)
            break
        integ(t)
        if t == next_arr:
            s1 = rnd.expovariate(mu1); s2 = rnd.expovariate(mu2)
            job = {'a': t, 's1': s1, 's2': s2, 'w': False}
            if t >= warm: arr += 1
            if not b1:
                b1 = True; dep1 = t + s1; job['st1'] = t
            else:
                q1.append(job); job['w'] = True
            na = t + rnd.expovariate(lam)
            next_arr = na if na < H else INF
        elif t == dep1:
            j = None
            if q1:
                j = q1.pop(0); j['st1'] = t
                dep1 = t + j['s1']
            else:
                b1 = False; dep1 = INF
            if not b2:
                b2 = True; dep2 = t + j['s2']; j['st2'] = t
            else:
                q2.append(j); j['w'] = True
        else:
            j = None
            if q2:
                j = q2.pop(0); j['st2'] = t
                dep2 = t + j['s2']
            else:
                b2 = False; dep2 = INF
            if j is not None:
                if t >= warm:
                    dep += 1
                    soj += t - j['a']
                    if j['w']: nw += 1
    win = H - warm
    if dep > 0:
        W = (soj / dep) * 60.0
        pw = nw / dep
    else:
        W = 0.0; pw = 0.0
    L = area / win if win > 0 else 0.0
    bf = (busy1 + busy2) / win if win > 0 else 0.0
    return {'L': L, 'W': W, 'arr': arr, 'dep': dep, 'busy_frac': bf,
            'p_wait': pw, 'p_loss': 0.0, 'blk': 0.0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=10000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0; mu1 = 60.0 / 7.5; mu2 = 60.0 / 6.0
    c = 1
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == 'c_up': c = 2
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run_seed(s, lam, mu1, mu2, a.horizon) for s in seed_list]
    n = len(res)
    def mean(k): return sum(r[k] for r in res) / n
    out = {
        'L': mean('L'), 'W': mean('W'),
        'runtime_units': a.horizon, 'seed_list': seed_list,
        'seeds_used': n, 'time_unit': 'hour',
        'win': a.horizon * 0.75,
        'arr': mean('arr'), 'blk': mean('blk'), 'dep': mean('dep'),
        'busy_frac': mean('busy_frac'), 'busy_util': mean('busy_frac'),
        'dep_rate': mean('dep') / (a.horizon * 0.75) if a.horizon > 0 else 0.0,
        'lam_eff': mean('dep') / (a.horizon * 0.75) if a.horizon > 0 else 0.0,
        'p_loss': mean('p_loss'), 'p_wait': mean('p_wait'),
        'per_seed_L': [r['L'] for r in res],
        'per_seed_W': [r['W'] for r in res],
        'per_seed_busy_frac': [r['busy_frac'] for r in res],
        'per_seed_p_loss': [r['p_loss'] for r in res],
        'per_seed_p_wait': [r['p_wait'] for r in res],
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
