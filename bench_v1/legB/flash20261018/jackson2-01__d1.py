import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_win = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
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
        arr = dep = blk = 0
        area = 0.0
        busy = 0.0
        wait_sum = 0.0
        served = 0
        last = 0.0
        while True:
            if q1:
                t1 = q1[0][0]
            else:
                t1 = float('inf')
            if q2:
                t2 = q2[0][0]
            else:
                t2 = float('inf')
            tn = t + rng.expovariate(lam)
            nxt = min(t1, t2, tn)
            if nxt > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += (b1 + b2) * dt
                t = H
                break
            dt = nxt - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += (b1 + b2) * dt
            t = nxt
            if t1 <= t2 and t1 <= tn:
                st, _ = q1.pop(0)
                n1 -= 1
                b1 = 1.0
                if t >= warm:
                    wait_sum += t - st
                    served += 1
                dep += 1
                svc = rng.expovariate(mu1)
                q2.append((t + svc, t))
                n2 += 1
            elif t2 <= tn:
                st, _ = q2.pop(0)
                n2 -= 1
                b2 = 1.0
                if t >= warm:
                    wait_sum += t - st
                    served += 1
                dep += 1
                svc = rng.expovariate(mu2)
                q2.append((t + svc, t))
                n2 += 1
            else:
                arr += 1
                svc = rng.expovariate(mu1)
                q1.append((t + svc, t))
                n1 += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = wait_sum / served if served > 0 else 0.0
        bf = busy / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 if served > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_win += win
        tot_busy += busy
        tot_wait += wait_sum
        tot_served += served
    n = a.seeds
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    bf = tot_busy / (2.0 * tot_win) if tot_win > 0 else 0.0
    arr_avg = tot_arr / n
    dep_avg = tot_dep / n
    blk_avg = tot_blk / n
    dep_rate = dep_avg / (tot_win / n) * 60.0 if tot_win > 0 else 0.0
    lam_eff = dep_rate / 60.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = 1.0 if tot_served > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': tot_win / n if n > 0 else 0.0,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': bf,
        'busy_util': bf,
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
