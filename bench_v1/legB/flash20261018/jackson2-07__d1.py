import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 12.0
    elif a.pert == 'c_up':
        mu1 = 10.0
        mu2 = 10.0
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_wait = 0.0
    tot_busy = 0.0
    tot_win = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        q1 = []
        q2 = []
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        wait = 0.0
        busy = 0.0
        last = 0.0
        while True:
            if not q1:
                dt = rng.expovariate(lam)
                t += dt
                if t > H:
                    break
                svc = rng.expovariate(mu1)
                q1.append((t, svc))
                arr += 1
                if t >= warm:
                    area += (n1 + n2) * (t - last)
                    busy += (b1 + b2) * (t - last)
                last = t
                n1 += 1
                if b1 == 0.0:
                    b1 = svc
            else:
                tnext = q1[0][0]
                if tnext > t:
                    dt = tnext - t
                    if t + dt > H:
                        dt = H - t
                    if t >= warm:
                        area += (n1 + n2) * dt
                        busy += (b1 + b2) * dt
                    t += dt
                    if t >= H:
                        break
                    last = t
                if q1 and q1[0][0] <= t:
                    arr_t, svc = q1.pop(0)
                    n1 -= 1
                    if b1 == 0.0:
                        b1 = svc
                    q2.append((t, svc))
                    n2 += 1
                    if b2 == 0.0:
                        b2 = svc
            if b1 > 0:
                b1 -= 0
            if b2 > 0:
                b2 -= 0
            if q2 and b2 == 0.0:
                b2 = q2[0][1]
            if b1 > 0 and b2 > 0:
                dt = min(b1, b2)
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += (b1 + b2) * dt
                t += dt
                b1 -= dt
                b2 -= dt
                if b1 <= 1e-12:
                    b1 = 0.0
                    if q2:
                        pass
                if b2 <= 1e-12:
                    b2 = 0.0
                    if q2:
                        q2.pop(0)
                        n2 -= 1
                        dep += 1
                        if t >= warm:
                            wait += t - q2[0][0] if q2 else 0
                    if q1:
                        pass
                if t >= H:
                    break
                last = t
            elif b1 > 0:
                dt = b1
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += b1 * dt
                t += dt
                b1 -= dt
                if b1 <= 1e-12:
                    b1 = 0.0
                if t >= H:
                    break
                last = t
            elif b2 > 0:
                dt = b2
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += b2 * dt
                t += dt
                b2 -= dt
                if b2 <= 1e-12:
                    b2 = 0.0
                    if q2:
                        q2.pop(0)
                        n2 -= 1
                        dep += 1
                if t >= H:
                    break
                last = t
            else:
                if q1:
                    arr_t, svc = q1.pop(0)
                    n1 -= 1
                    b1 = svc
                    q2.append((t, svc))
                    n2 += 1
                    if b2 == 0.0:
                        b2 = svc
                elif q2:
                    b2 = q2[0][1]
                else:
                    dt = rng.expovariate(lam)
                    t += dt
                    if t > H:
                        break
                    svc = rng.expovariate(mu1)
                    q1.append((t, svc))
                    arr += 1
                    n1 += 1
                    if b1 == 0.0:
                        b1 = svc
                    if t >= warm:
                        area += (n1 + n2) * (t - last)
                        busy += (b1 + b2) * (t - last)
                    last = t
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        bf = busy / (2 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy
        tot_win += win
    n = a.seeds
    L = tot_area / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    bf = tot_busy / (2 * tot_win) if tot_win > 0 else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': tot_win / n if n > 0 else 0.0,
        'arr': tot_arr / n,
        'blk': tot_blk / n,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tot_dep / n,
        'dep_rate': dep_rate,
        'lam_eff': dep_rate,
        'p_loss': pl,
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
