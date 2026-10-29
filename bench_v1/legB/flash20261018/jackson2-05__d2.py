import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
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

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_wait = tot_busy = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = b2 = 0.0
        n1 = n2 = 0
        arr = dep = blk = 0
        area = wait = busy = 0.0
        win = 0.0
        nxt = rng.expovariate(lam)
        while t < H:
            if nxt <= t:
                t = nxt
                if t >= H:
                    break
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                cust = [svc1, svc2]
                if t >= warm:
                    arr += 1
                if b1 == 0.0:
                    b1 = t + svc1
                    if t >= warm:
                        busy += min(b1, H) - t
                else:
                    q1.append(cust)
                nxt = t + rng.expovariate(lam)
            else:
                t = nxt
                if t >= H:
                    break
                if b1 <= b2:
                    t = b1
                    if t >= H:
                        break
                    if t >= warm:
                        busy += min(b2, H) - t if b2 > t else 0.0
                    c = q1.pop(0) if q1 else None
                    if c is not None:
                        b1 = t + c[0]
                        if t >= warm:
                            busy += min(b1, H) - t
                    else:
                        b1 = 0.0
                    if b2 == 0.0:
                        b2 = t + c[1] if c is not None else 0.0
                        if c is not None and t >= warm:
                            busy += min(b2, H) - t
                    elif c is not None:
                        q2.append(c)
                else:
                    t = b2
                    if t >= H:
                        break
                    if t >= warm:
                        busy += min(b1, H) - t if b1 > t else 0.0
                    c = q2.pop(0) if q2 else None
                    if c is not None:
                        b2 = t + c[1]
                        if t >= warm:
                            busy += min(b2, H) - t
                    else:
                        b2 = 0.0
                    if b1 == 0.0:
                        b1 = t + c[0] if c is not None else 0.0
                        if c is not None and t >= warm:
                            busy += min(b1, H) - t
                    elif c is not None:
                        q1.append(c)
                nxt = t
        win = H - warm
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_wait += wait
        tot_busy += busy
        tot_win += win
        per_L.append(0.0)
        per_W.append(0.0)
        per_bf.append(0.0)
        per_pl.append(0.0)
        per_pw.append(0.0)

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_dep if tot_dep > 0 else 0.0
    bf = tot_busy / (2.0 * tot_win) if tot_win > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0

    out = {
        'L': L, 'W': W, 'runtime_units': 'minute', 'seed_list': seeds,
        'seeds_used': len(seeds), 'time_unit': 'minute', 'win': tot_win / len(seeds),
        'arr': tot_arr / len(seeds), 'blk': tot_blk / len(seeds),
        'busy_frac': bf, 'busy_util': bf, 'dep': tot_dep / len(seeds),
        'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W, 'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
