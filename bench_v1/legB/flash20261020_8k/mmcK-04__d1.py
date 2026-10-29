import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waiters = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        arr = dep = blk = 0
        areaN = areaB = 0.0
        wait_sum = 0.0
        served = 0
        waiters = 0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            nxt = next_arr
            for sv in servers:
                if sv is not None and sv < nxt:
                    nxt = sv
            if nxt > H:
                dt = H - t
                if t >= win_start:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = nxt - t
            if t >= win_start:
                areaN += n * dt
                areaB += busy * dt
            elif nxt > win_start:
                areaN += n * (nxt - win_start)
                areaB += busy * (nxt - win_start)
            t = nxt
            if t == next_arr:
                arr += 1
                if n < cap:
                    n += 1
                    st = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        servers[busy - 1] = t + st
                        if t >= win_start:
                            served += 1
                    else:
                        queue.append((t, st))
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                for i in range(c):
                    if servers[i] is not None and servers[i] == t:
                        servers[i] = None
                        busy -= 1
                        n -= 1
                        dep += 1
                        if queue:
                            at, st = queue.pop(0)
                            w = t - at
                            if t >= win_start:
                                wait_sum += w
                                waiters += 1
                            busy += 1
                            servers[i] = t + st
                            if t >= win_start:
                                served += 1
                        break
        L = areaN / win_len if win_len > 0 else 0.0
        bf = areaB / (c * win_len) if win_len > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waiters / served if served > 0 else 0.0
        W = wait_sum / waiters if waiters > 0 else 0.0
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
        tot_win += win_len
        tot_wait += wait_sum
        tot_served += served
        tot_waiters += waiters

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac / c
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waiters / tot_served if tot_served > 0 else 0.0
    W = tot_wait / tot_waiters if tot_waiters > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    lam_eff = (tot_arr - tot_blk) / tot_win if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
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
