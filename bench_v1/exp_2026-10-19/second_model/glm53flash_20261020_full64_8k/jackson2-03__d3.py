import argparse, json, random

def run_seed(seed, H, lam, mu):
    rnd = random.Random(seed)
    TW = 0.25 * H
    t = 0.0
    na = rnd.expovariate(lam)
    c1 = float('inf'); c2 = float('inf')
    q1 = []; q2 = []
    s1 = None; s2 = None
    areaL = 0.0; areaBusy = 0.0
    tl = 0.0
    deps = []
    def L():
        return len(q1) + (1 if s1 else 0) + len(q2) + (1 if s2 else 0)
    def busy():
        return (1 if s1 else 0) + (1 if s2 else 0)
    def integrate(t0, t1):
        nonlocal areaL, areaBusy
        a = max(t0, TW); b = min(t1, H)
        if b > a:
            areaL += (t1 - t0) * 0 if False else (b - a) * L()
            areaBusy += (b - a) * busy()
    while True:
        t = min(na, c1, c2)
        if t > H:
            integrate(tl, H)
            break
        integrate(tl, t)
        tl = t
        if t == na:
            q1.append([t, False])
            na = t + rnd.expovariate(lam)
            if s1 is None:
                s1 = q1.pop(0); c1 = t + rnd.expovariate(mu)
        elif t == c1:
            s1[0] = s1[0]
            sv2 = rnd.expovariate(mu)
            if s2 is None:
                s2 = (s1, sv2); c2 = t + sv2
            else:
                q2.append((s1, sv2))
            s1 = None; c1 = float('inf')
            if q1:
                s1 = q1.pop(0); s1[1] = True; c1 = t + rnd.expovariate(mu)
        else:
            job, _ = s2
            deps.append((t, t - job[0], job[1]))
            s2 = None; c2 = float('inf')
            if q2:
                job2, sv = q2.pop(0); job2[1] = True
                s2 = (job2, sv); c2 = t + sv
    wd = [(d, w, wt) for (d, w, wt) in deps if d > TW]
    nd = len(wd)
    win = H - TW
    Lbar = areaL / win if win > 0 else 0.0
    W = (sum(w for _, w, _ in wd) / nd * 60.0) if nd else 0.0
    bf = areaBusy / (2.0 * win) if win > 0 else 0.0
    pw = (sum(1 for _, _, wt in wd if wt) / nd) if nd else 0.0
    return Lbar, W, bf, pw, nd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=lambda x: float(x), default=20000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu = 4.0, 10.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': mu /= 1.1
    per = [run_seed(s, a.horizon, lam, mu) for s in range(a.seed_start, a.seed_start + a.seeds)]
    n = len(per)
    seed_list = list(range(a.seed_start, a.seed_start + n))
    win = a.horizon * 0.75
    L = sum(p[0] for p in per) / n
    W = sum(p[1] for p in per) / n
    bf = sum(p[2] for p in per) / n
    pw = sum(p[3] for p in per) / n
    dep = sum(p[4] for p in per) / n
    out = {
        'L': L, 'W': W, 'runtime_units': a.horizon, 'seed_list': seed_list,
        'seeds_used': n, 'time_unit': 'hour', 'win': win,
        'arr': lam, 'blk': 0.0, 'busy_frac': bf, 'busy_util': bf,
        'dep': dep, 'dep_rate': dep / win, 'lam_eff': dep / win,
        'p_loss': 0.0, 'p_wait': pw,
        'per_seed_L': [p[0] for p in per], 'per_seed_W': [p[1] for p in per],
        'per_seed_busy_frac': [p[2] for p in per],
        'per_seed_p_loss': [0.0] * n, 'per_seed_p_wait': [p[3] for p in per],
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
