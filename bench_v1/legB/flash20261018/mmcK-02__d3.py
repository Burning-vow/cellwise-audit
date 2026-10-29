import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr = dep = blk = 0
        areaN = areaB = 0.0
        wait_sum = 0.0
        served = 0
        waited = 0
        t_next = rng.expovariate(lam)
        while t < H:
            if t_next <= t:
                t = t_next
                if n < cap:
                    n += 1
                    arr += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if busy < c:
                        busy += 1
                        st, sd = queue.pop(0)
                        wait_sum += t - st
                        served += 1
                        if t - st > 0:
                            waited += 1
                        dep_t = t + sd
                        queue.append((dep_t, -1))
                else:
                    blk += 1
                t_next = t + rng.expovariate(lam)
            else:
                dt = t_next - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = t_next
                if queue:
                    st, sd = queue.pop(0)
                    if sd >= 0:
                        pass
                    busy -= 1
                    n -= 1
                    dep += 1
                    if busy < c and queue:
                        st2, sd2 = queue.pop(0)
                        wait_sum += t - st2
                        served += 1
                        if t - st2 > 0:
                            waited += 1
                        busy += 1
                        queue.append((t + sd2, -1))
                t_next = t + rng.expovariate(lam)

        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaB / (c * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / served if served > 0 else 0.0
        W = wait_sum / served if served > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += win
        tot_wait += wait_sum
        tot_served += served
        tot_waited += waited

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr_avg / (tot_win / ns) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': tot_win / ns,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_frac,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
