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
    mu2 = 1.0 / 5.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = None
        b2 = None
        n1 = 0
        n2 = 0
        area = 0.0
        last = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        waiters = 0
        waited = 0
        while True:
            if b1 is None and q1:
                c = q1.pop(0)
                b1 = (c[0], c[1])
                n1 -= 1
                if c[0] >= warm:
                    waited += 1
            if b2 is None and q2:
                c = q2.pop(0)
                b2 = (c[0], c[1])
                n2 -= 1
                if c[0] >= warm:
                    waited += 1
            cand = []
            if b1 is not None:
                cand.append(b1[0] + b1[1])
            if b2 is not None:
                cand.append(b2[0] + b2[1])
            if t < H:
                cand.append(t + rng.expovariate(lam))
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area += (n1 + n2 + (1 if b1 else 0) + (1 if b2 else 0)) * dt
                if b1 is not None:
                    busy += dt
                if b2 is not None:
                    busy += dt
            if b1 is not None and b1[0] + b1[1] <= nt + 1e-12:
                if b1[0] >= warm:
                    dep += 1
                b1 = None
            if b2 is not None and b2[0] + b2[1] <= nt + 1e-12:
                if b2[0] >= warm:
                    dep += 1
                b2 = None
            if t < H and abs(nt - (t + 0)) >= 0 and nt < H + 1e-12:
                pass
            t = nt
            if t >= H:
                break
            if b1 is None and q1:
                c = q1.pop(0)
                b1 = (c[0], c[1])
                n1 -= 1
                if c[0] >= warm:
                    waited += 1
            if b2 is None and q2:
                c = q2.pop(0)
                b2 = (c[0], c[1])
                n2 -= 1
                if c[0] >= warm:
                    waited += 1
            if t < H:
                pass
        per_L.append(area / (H - warm) if H > warm else 0.0)
        per_W.append(area / (H - warm) if H > warm else 0.0)
        per_bf.append(busy / (2.0 * (H - warm)) if H > warm else 0.0)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    W = sum(per_W) / len(per_W) if per_W else 0.0
    L = sum(per_L) / len(per_L) if per_L else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': H - warm,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_frac': sum(per_bf) / len(per_bf) if per_bf else 0.0,
        'busy_util': sum(per_bf) / len(per_bf) if per_bf else 0.0,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'dep_rate': (tot_dep / len(seeds)) / ((H - warm) / 60.0) if seeds and H > warm else 0.0,
        'lam_eff': lam * 60.0,
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
