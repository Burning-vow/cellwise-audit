import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 2
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_serv = 0.0
    tot_served = 0
    tot_arrived = 0
    tot_waiters = 0
    win_total = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        wsum = ssum = 0.0
        served = 0
        arrived = 0
        waiters = 0
        lost = 0
        win_arr = win_dep = win_blk = 0.0
        win_areaN = win_areaB = 0.0
        win_wait = win_serv = 0.0
        win_served = 0
        win_arrived = 0
        win_waiters = 0
        while True:
            if next_arr <= t:
                dt = next_arr - t
                areaN += n * dt
                areaB += busy * dt
                if next_arr >= warm:
                    win_areaN += n * dt
                    win_areaB += busy * dt
                t = next_arr
                n += 1
                arrived += 1
                if t >= warm: win_arrived += 1
                st = rng.expovariate(mu)
                cust = [t, st, None]
                if busy < c:
                    busy += 1
                    cust[2] = t
                    wsum += 0.0
                    ssum += st
                    served += 1
                    if t >= warm:
                        win_served += 1
                        win_serv += st
                else:
                    queue.append(cust)
                    waiters += 1
                    if t >= warm: win_waiters += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if busy == 0 and not queue:
                    break
                if busy == 0:
                    t = queue[0][0]
                    continue
                dt = next_arr - t
                areaN += n * dt
                areaB += busy * dt
                if t >= warm:
                    win_areaN += n * dt
                    win_areaB += busy * dt
                t = next_arr
                busy -= 1
                n -= 1
                if queue:
                    cust = queue.pop(0)
                    w = t - cust[0]
                    wsum += w
                    ssum += cust[1]
                    served += 1
                    if t >= warm:
                        win_served += 1
                        win_wait += w
                        win_serv += cust[1]
                    busy += 1
                if t >= H:
                    break
        win = max(H - warm, 1e-9)
        L = win_areaN / win
        W = (win_wait + win_serv) / win_served if win_served > 0 else 0.0
        bf = win_areaB / win / c
        pw = win_waiters / win_arrived if win_arrived > 0 else 0.0
        pl = win_blk / win_arrived if win_arrived > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_areaN += win_areaN
        tot_areaB += win_areaB
        tot_wait += win_wait
        tot_serv += win_serv
        tot_served += win_served
        tot_arrived += win_arrived
        tot_waiters += win_waiters
        tot_arr += win_arrived
        tot_dep += win_served
        tot_blk += win_blk
        win_total += win
    L = tot_areaN / win_total
    W = (tot_wait + tot_serv) / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_areaB / win_total / c
    p_wait = tot_waiters / tot_arrived if tot_arrived > 0 else 0.0
    p_loss = tot_blk / tot_arrived if tot_arrived > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = dep / (win_total / len(seeds)) * 60.0
    lam_eff = arr / (win_total / len(seeds)) * 60.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds),
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': 1.0 - math.exp(-lam * (win_total / len(seeds)) / c) if False else busy_frac,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W, 'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
