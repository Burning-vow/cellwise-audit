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
    warm = 0.25*H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
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
        wsum = 0.0
        wcnt = 0
        area = 0.0
        busy = 0.0
        last = 0.0
        nwait = 0
        narr = 0
        while True:
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1['start'] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2['start'] = t
            cand = []
            if s1 is not None:
                cand.append(s1['start'] + s1['svc'])
            if s2 is not None:
                cand.append(s2['start'] + s2['svc'])
            if t < H:
                cand.append(t + rng.expovariate(lam))
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area += (len(q1) + len(q2) + (1 if s1 else 0) + (1 if s2 else 0)) * dt
                busy += ((1 if s1 else 0) + (1 if s2 else 0)) * dt
            t = nt
            if s1 is not None and t >= s1['start'] + s1['svc']:
                q2.append(s1)
                s1 = None
            if s2 is not None and t >= s2['start'] + s2['svc']:
                if t >= warm:
                    wsum += t - s2['arr']
                    wcnt += 1
                    dep += 1
                s2 = None
            if t < H and abs(t - (cand[-1] if len(cand) > 0 else -1)) < 1e-12:
                pass
            if t < H:
                pass
            if t >= H:
                break
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1['start'] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2['start'] = t
        per_L.append(area/(H-warm) if H > warm else 0.0)
        per_W.append(wsum/wcnt if wcnt > 0 else 0.0)
        per_bf.append(busy/(2*(H-warm)) if H > warm else 0.0)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    n = a.seeds
    L = sum(per_L)/n if n else 0.0
    W = sum(per_W)/n if n else 0.0
    bf = sum(per_bf)/n if n else 0.0
    win = H - warm
    dep_rate = (tot_dep/n)/win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr/n if n else 0.0,
        'blk': tot_blk/n if n else 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tot_dep/n if n else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': dep_rate,
        'p_loss': 0.0,
        'p_wait': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
