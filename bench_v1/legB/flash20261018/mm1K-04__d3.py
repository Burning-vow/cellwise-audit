import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_win = 0.0
    tot_areaN = tot_areaBusy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        queue = []
        areaN = 0.0
        areaBusy = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        served = 0
        waited = 0
        win_start = warm
        win_len = H - warm
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    areaN += n * (H - t)
                    areaBusy += (H - t)
                else:
                    areaN += n * (H - t)
                break
            if busy:
                areaN += n * dt
                areaBusy += dt
                t = next_dep
                n -= 1
                if n > 0:
                    nxt = queue.pop(0)
                    w = t - nxt[1]
                    if t >= win_start:
                        wait_sum += w
                        served += 1
                        if w > 0:
                            waited += 1
                    next_dep = t + nxt[0]
                else:
                    busy = False
                    next_dep = float('inf')
            else:
                areaN += n * dt
                t += dt
                arr += 1
                if n >= K:
                    blk += 1
                else:
                    svc = rng.expovariate(mu)
                    n += 1
                    if n == 1:
                        busy = True
                        next_dep = t + svc
                    else:
                        queue.append((svc, t))
        if win_len > 0:
            Ls = areaN / H
            bf = areaBusy / H
            pl = blk / arr if arr > 0 else 0.0
            Ws = wait_sum / served if served > 0 else 0.0
            pw = waited / served if served > 0 else 0.0
        else:
            Ls = bf = pl = Ws = pw = 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_win += H
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        tot_wait += wait_sum
        tot_served += served
        tot_waited += waited
    ns = a.seeds
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (H / 60.0) if H > 0 else 0.0
    lam_eff = arr_avg / (H / 60.0) if H > 0 else 0.0
    busy_util = busy_frac
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
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
