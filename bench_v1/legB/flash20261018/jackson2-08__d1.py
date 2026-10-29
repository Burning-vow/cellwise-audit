import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
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
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_busy = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n1 = 0
        n2 = 0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        area = 0.0
        wait_sum = 0.0
        served = 0
        busy = 0.0
        arr = dep = blk = 0
        last = 0.0
        while True:
            cand = []
            if s1 is not None:
                cand.append(s1)
            if s2 is not None:
                cand.append(s2)
            if q1:
                cand.append(q1[0][0])
            if q2:
                cand.append(q2[0][0])
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                break
            dt = nt - last
            if nt > warm:
                lo = max(last, warm)
                area += (n1+n2)*(nt-lo)
                busy += (1 if s1 is not None else 0)*(nt-lo)
                busy += (1 if s2 is not None else 0)*(nt-lo)
            last = nt
            t = nt
            if s1 is not None and s1 <= t:
                n1 -= 1
                s1 = None
                if q1:
                    arr_t, svc = q1.pop(0)
                    s1 = t + svc
                    wait_sum += t - arr_t
                    served += 1
            if s2 is not None and s2 <= t:
                n2 -= 1
                s2 = None
                if q2:
                    arr_t, svc = q2.pop(0)
                    s2 = t + svc
                    wait_sum += t - arr_t
                    served += 1
            if s1 is None and q1:
                arr_t, svc = q1.pop(0)
                s1 = t + svc
                wait_sum += t - arr_t
                served += 1
            if s2 is None and q2:
                arr_t, svc = q2.pop(0)
                s2 = t + svc
                wait_sum += t - arr_t
                served += 1
            if t >= warm:
                arr += 1
            svc1 = rng.expovariate(mu1)
            q1.append((t, svc1))
            n1 += 1
            if s1 is None:
                arr_t, svc = q1.pop(0)
                s1 = t + svc
                wait_sum += t - arr_t
                served += 1
            nxt = t + rng.expovariate(lam)
            if nxt > H:
                break
            t = nxt
            if t >= warm:
                arr += 1
            svc1 = rng.expovariate(mu1)
            q1.append((t, svc1))
            n1 += 1
            if s1 is None:
                arr_t, svc = q1.pop(0)
                s1 = t + svc
                wait_sum += t - arr_t
                served += 1
        win = H - warm
        L = area/win if win > 0 else 0.0
        W = wait_sum/served if served > 0 else 0.0
        bf = busy/(2*win) if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr
        tot_dep += served
        tot_blk += blk
        tot_area += area
        tot_wait += wait_sum
        tot_served += served
        tot_busy += busy
    n = a.seeds
    win = H - warm
    L = tot_area/(n*win) if win > 0 else 0.0
    W = tot_wait/tot_served if tot_served > 0 else 0.0
    bf = tot_busy/(2*n*win) if win > 0 else 0.0
    arr_avg = tot_arr/n
    dep_avg = tot_dep/n
    blk_avg = tot_blk/n
    dep_rate = dep_avg/win if win > 0 else 0.0
    lam_eff = arr_avg/win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
