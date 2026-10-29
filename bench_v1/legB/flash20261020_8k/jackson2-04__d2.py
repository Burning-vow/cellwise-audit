import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu1 = 1.0 / 6.0
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
    tot_wait_area = 0.0
    tot_sys_area = 0.0
    tot_n1_area = 0.0
    tot_n2_area = 0.0
    tot_waiters = 0.0
    tot_arrivals_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        q1 = []
        q2 = []
        arr_win = 0
        dep_win = 0
        blk_win = 0
        wait_area = 0.0
        sys_area = 0.0
        n1_area = 0.0
        n2_area = 0.0
        waiters_area = 0.0
        busy_area = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while t < H:
            cand = next_arr
            if q1 and q1[0][0] < cand:
                cand = q1[0][0]
            if q2 and q2[0][0] < cand:
                cand = q2[0][0]
            if cand > H:
                cand = H
            dt = cand - t
            if t >= warm:
                wait_area += (n1 + n2) * dt
                sys_area += (n1 + n2) * dt
                n1_area += n1 * dt
                n2_area += n2 * dt
                waiters_area += (max(n1 - 1, 0) + max(n2 - 1, 0)) * dt
                busy_area += (b1 + b2) * dt
            t = cand
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                if t >= warm:
                    arr_win += 1
                if n1 == 0 and b1 == 0.0:
                    b1 = 1.0
                    svc = rng.expovariate(mu1)
                    q1.append((t + svc, svc))
                else:
                    q1.append((t, rng.expovariate(mu1)))
                n1 += 1
                next_arr = t + rng.expovariate(lam)
            elif q1 and abs(t - q1[0][0]) < 1e-12:
                _, svc = q1.pop(0)
                n1 -= 1
                if t >= warm:
                    dep_win += 1
                if n2 == 0 and b2 == 0.0:
                    b2 = 1.0
                    svc2 = rng.expovariate(mu2)
                    q2.append((t + svc2, svc2))
                else:
                    q2.append((t, rng.expovariate(mu2)))
                n2 += 1
                if q1:
                    b1 = 1.0
                    q1[0] = (t + q1[0][1], q1[0][1])
                else:
                    b1 = 0.0
            elif q2 and abs(t - q2[0][0]) < 1e-12:
                _, svc = q2.pop(0)
                n2 -= 1
                if q2:
                    b2 = 1.0
                    q2[0] = (t + q2[0][1], q2[0][1])
                else:
                    b2 = 0.0
        win = H - warm
        Ls = sys_area / win if win > 0 else 0.0
        Ws = wait_area / max(dep_win, 1) if dep_win > 0 else 0.0
        bf = busy_area / (2.0 * win) if win > 0 else 0.0
        pl = blk_win / max(arr_win, 1) if arr_win > 0 else 0.0
        pw = waiters_area / max(arr_win, 1) if arr_win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_sys_area += sys_area
        tot_n1_area += n1_area
        tot_n2_area += n2_area
        tot_waiters += waiters_area
        tot_arrivals_win += arr_win
    n = len(seeds)
    win = H - warm
    L = tot_sys_area / (n * win) if win > 0 else 0.0
    W = tot_wait_area / max(tot_dep, 1) if tot_dep > 0 else 0.0
    bf = tot_busy / (2.0 * n * win) if win > 0 else 0.0
    pl = tot_blk / max(tot_arr, 1) if tot_arr > 0 else 0.0
    pw = tot_waiters / max(tot_arr, 1) if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (n * win) * 60.0 if win > 0 else 0.0
    lam_eff = tot_arr / (n * win) * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / n,
        'blk': tot_blk / n,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tot_dep / n,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
