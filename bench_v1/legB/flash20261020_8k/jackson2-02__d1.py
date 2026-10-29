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
    tot_busy = 0.0
    tot_area = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        wait_sum = 0.0
        served = 0
        waited = 0
        busy = 0.0
        last = 0.0
        while True:
            if s1 is None and q1:
                c = q1.pop(0)
                s1 = (c[0], c[1], c[2])
            if s2 is None and q2:
                c = q2.pop(0)
                s2 = (c[0], c[1], c[2])
            cand = []
            if s1 is not None:
                cand.append(s1[0] + s1[1])
            if s2 is not None:
                cand.append(s2[0] + s2[1])
            cand.append(t + rng.expovariate(lam))
            nt = min(cand)
            if nt > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += (1.0 if s1 is not None else 0.0) * dt
                t = H
                break
            dt = nt - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += (1.0 if s1 is not None else 0.0) * dt
            t = nt
            if s1 is not None and abs(t - (s1[0] + s1[1])) < 1e-12:
                c = s1
                s1 = None
                n1 -= 1
                if t >= warm:
                    dep += 1
                    wait_sum += (t - c[2])
                    served += 1
                q2.append((t, rng.expovariate(mu2), c[2]))
                n2 += 1
            elif s2 is not None and abs(t - (s2[0] + s2[1])) < 1e-12:
                c = s2
                s2 = None
                n2 -= 1
                if t >= warm:
                    dep += 1
                    wait_sum += (t - c[2])
                    served += 1
            else:
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                if t >= warm:
                    arr += 1
                if s1 is None:
                    s1 = (t, svc1, t)
                    n1 += 1
                else:
                    q1.append((t, svc1, t))
                    n1 += 1
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (wait_sum / served) if served > 0 else 0.0
        bfs = busy / win if win > 0 else 0.0
        pls = blk / arr if arr > 0 else 0.0
        pws = waited / arr if arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += busy
        tot_area += area
        tot_wait += wait_sum
        tot_served += served
        tot_waited += waited
    n = len(seeds)
    win = H - warm
    L = (tot_area / n) / win if win > 0 else 0.0
    W = (tot_wait / tot_served) if tot_served > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / n,
        'blk': tot_blk / n,
        'busy_frac': (tot_busy / n) / win if win > 0 else 0.0,
        'busy_util': (tot_busy / n) / win if win > 0 else 0.0,
        'dep': tot_dep / n,
        'dep_rate': (tot_dep / n) / (win / 60.0) if win > 0 else 0.0,
        'lam_eff': (tot_dep / n) / (win / 60.0) if win > 0 else 0.0,
        'p_loss': (tot_blk / tot_arr) if tot_arr > 0 else 0.0,
        'p_wait': (tot_waited / tot_arr) if tot_arr > 0 else 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
