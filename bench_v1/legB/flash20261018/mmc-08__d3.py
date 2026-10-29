import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_served = 0.0
    tot_arrived_win = 0.0
    tot_waiters = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        wait_sum = 0.0
        served = 0
        arrived_win = 0
        waiters = 0
        blk = 0
        last = 0.0
        while True:
            cand = [next_arr]
            if servers:
                cand.append(min(servers))
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = nt - t
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
            t = nt
            if t >= next_arr - 1e-12 and abs(t - next_arr) < 1e-9:
                n += 1
                if t >= warm:
                    arrived_win += 1
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    servers.append(t + st)
                else:
                    queue.append(t)
                next_arr = t + rng.expovariate(lam)
            else:
                servers.sort()
                servers.pop(0)
                busy -= 1
                if queue:
                    at = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        wait_sum += w
                        served += 1
                        waiters += 1
                    busy += 1
                    st = rng.expovariate(mu)
                    servers.append(t + st)
        win = H - warm
        win_total += win
        L = areaN / win if win > 0 else 0.0
        W = (wait_sum / served + 1.0 / mu) if served > 0 else 0.0
        bf = areaB / (win * c) if win > 0 else 0.0
        pw = waiters / arrived_win if arrived_win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_served += served
        tot_arrived_win += arrived_win
        tot_waiters += waiters
        tot_arr += arrived_win
        tot_dep += served
        tot_blk += blk

    nseeds = len(seeds)
    L = tot_areaN / (win_total * nseeds) if win_total > 0 else 0.0
    W = (tot_wait / tot_served + 1.0 / mu) if tot_served > 0 else 0.0
    busy_frac = tot_areaB / (win_total * c * nseeds) if win_total > 0 else 0.0
    p_wait = tot_waiters / tot_arrived_win if tot_arrived_win > 0 else 0.0
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = dep / (win_total / nseeds) if win_total > 0 else 0.0
    lam_eff = arr / (win_total / nseeds) if win_total > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': nseeds,
        'time_unit': 'minute', 'win': win_total / nseeds if nseeds else 0.0,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
