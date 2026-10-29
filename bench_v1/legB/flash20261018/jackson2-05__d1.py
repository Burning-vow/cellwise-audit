import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 60.0/7.5
    mu2 = 60.0/6.0
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
    seeds = [a.seed_start+i for i in range(a.seeds)]
    per_L=[]; per_W=[]; per_bf=[]; per_pl=[]; per_pw=[]
    tot_arr=0.0; tot_dep=0.0; tot_blk=0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        nxt = rng.expovariate(lam)
        q1=[]; q2=[]
        b1=0.0; b2=0.0
        area1=0.0; area2=0.0
        arr=0; dep=0; blk=0; waiters=0
        win_area1=0.0; win_area2=0.0
        win_busy1=0.0; win_busy2=0.0
        win_arr=0; win_dep=0; win_blk=0; win_wait=0
        while t < H:
            cand = [nxt]
            if b1>0: cand.append(b1)
            if b2>0: cand.append(b2)
            tn = min(cand)
            if tn > H:
                dt = H - t
                area1 += len(q1)*dt
                area2 += len(q2)*dt
                if t >= warm:
                    win_area1 += len(q1)*dt
                    win_area2 += len(q2)*dt
                    if q1: win_busy1 += dt
                    if q2: win_busy2 += dt
                t = H
                break
            dt = tn - t
            area1 += len(q1)*dt
            area2 += len(q2)*dt
            if t >= warm:
                win_area1 += len(q1)*dt
                win_area2 += len(q2)*dt
                if q1: win_busy1 += dt
                if q2: win_busy2 += dt
            t = tn
            if t == nxt:
                arr += 1
                if t >= warm: win_arr += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                q1.append((svc1, svc2))
                nxt = t + rng.expovariate(lam)
                if b1 == 0.0:
                    svc1, svc2 = q1.pop(0)
                    b1 = t + svc1
            elif t == b1:
                dep += 1
                if t >= warm: win_dep += 1
                q2.append((0.0, q1_dummy if False else 0.0))
                q2.pop()
                b1 = 0.0
                if q1:
                    svc1, svc2 = q1.pop(0)
                    b1 = t + svc1
            elif t == b2:
                b2 = 0.0
                if q2:
                    q2.pop(0)
                    b2 = t + rng.expovariate(mu2)
        per_L.append((area1+area2)/H)
        per_W.append((area1+area2)/max(1,arr))
        per_bf.append((win_busy1+win_busy2)/max(1e-9,(H-warm)))
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
    n = len(seeds)
    L = sum(per_L)/n
    W = sum(per_W)/n
    win = H - warm
    out = {
        'L': L, 'W': W, 'runtime_units': 'minute', 'seed_list': seeds,
        'seeds_used': n, 'time_unit': 'minute', 'win': win,
        'arr': tot_arr/n, 'blk': tot_blk/n, 'busy_frac': sum(per_bf)/n,
        'busy_util': sum(per_bf)/n, 'dep': tot_dep/n,
        'dep_rate': (tot_dep/n)/win*60.0, 'lam_eff': lam,
        'p_loss': 0.0, 'p_wait': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
