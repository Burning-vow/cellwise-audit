import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0
    mu = 10.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_served = 0.0
    tot_waiters = tot_arrivals_win = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        areaN = areaB = 0.0
        wait_sum = 0.0
        served = 0
        waiters = 0
        arrivals_win = 0
        dep_win = 0
        blk_win = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            nxt = next_arr
            if servers:
                nxt = min(nxt, min(servers))
            if nxt > H:
                dt = H - last
                if last >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                break
            dt = nxt - last
            if last >= warm:
                areaN += n * dt
                areaB += busy * dt
            last = nxt
            if servers and min(servers) <= next_arr:
                fin = min(servers)
                servers.remove(fin)
                busy -= 1
                if queue:
                    qt, st = queue.pop(0)
                    if last >= warm:
                        wait_sum += last - qt
                        served += 1
                    servers.append(last + st)
                    busy += 1
                else:
                    if last >= warm:
                        served += 1
                if last >= warm:
                    dep_win += 1
            else:
                t = next_arr
                st = rng.expovariate(mu)
                n += 1
                if last >= warm:
                    arrivals_win += 1
                if busy < c:
                    busy += 1
                    servers.append(t + st)
                else:
                    queue.append((t, st))
                    if last >= warm:
                        waiters += 1
                next_arr = t + rng.expovariate(lam)
        wlen = H - warm
        win_total += wlen
        Ls = areaN / wlen if wlen > 0 else 0.0
        bf = areaB / (c * wlen) if wlen > 0 else 0.0
        Ws = (wait_sum + served * (1.0 / mu)) / served if served > 0 else 0.0
        pw = waiters / arrivals_win if arrivals_win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arrivals_win
        tot_dep += dep_win
        tot_blk += blk_win
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_served += served
        tot_waiters += waiters
        tot_arrivals_win += arrivals_win

    L = tot_areaN / win_total if win_total > 0 else 0.0
    busy_frac = tot_areaB / (c * win_total) if win_total > 0 else 0.0
    W = (tot_wait + tot_served * (1.0 / mu)) / tot_served if tot_served > 0 else 0.0
    p_wait = tot_waiters / tot_arrivals_win if tot_arrivals_win > 0 else 0.0
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': busy_frac, 'busy_occupied': busy_frac,
        'dep_rate': dep_rate, 'lam_eff': lam, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W, 'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
