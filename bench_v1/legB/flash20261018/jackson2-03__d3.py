import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = 4.8
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 12.0
    elif a.pert == 'c_up':
        lam = 4.0
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
        area_w = 0.0
        nwait = 0
        narr = 0
        while True:
            if not q1 and not q2:
                dt = rng.expovariate(lam)
                t += dt
                if t > H:
                    break
                sv1 = rng.expovariate(mu1)
                sv2 = rng.expovariate(mu2)
                arr += 1
                narr += 1
                if t >= warm:
                    area += (n1 + n2) * dt
                n1 += 1
                q1.append((t, sv1, sv2))
                if t >= warm:
                    area_w += 0.0
                continue
            cand = []
            if q1:
                cand.append(q1[0][0])
            if q2:
                cand.append(q2[0][0])
            if not q1 and not q2:
                continue
            if q1 and (not q2 or q1[0][0] <= q2[0][0]):
                nt = q1[0][0]
            else:
                nt = q2[0][0]
            if nt > H:
                if t < H:
                    dt = H - t
                    if t >= warm:
                        area += (n1 + n2) * dt
                    t = H
                break
            if nt > t:
                dt = nt - t
                if t >= warm:
                    area += (n1 + n2) * dt
                t = nt
            if q1 and q1[0][0] <= t:
                at, sv1, sv2 = q1.pop(0)
                n1 -= 1
                if t >= warm:
                    area_w += 0.0
                q2.append((t + sv1, sv2))
                n2 += 1
                if t >= warm:
                    area_w += 0.0
                continue
            if q2 and q2[0][0] <= t:
                ft, sv2 = q2.pop(0)
                n2 -= 1
                dep += 1
                if t >= warm:
                    area_w += 0.0
                continue
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        bf = (b1 + b2) / (2.0 * win) if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / win if win > 0 else 0.0
    lam_eff = arr_avg / win if win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = 0.0
    busy_frac = sum(per_bf) / ns
    busy_util = busy_frac
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': busy_frac,
        'busy_util': busy_util,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
