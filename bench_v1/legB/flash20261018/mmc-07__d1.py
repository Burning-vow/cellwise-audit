import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    c = 3
    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
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
    tot_wait = tot_soj = 0.0
    tot_dep_t = 0.0
    tot_pw_num = 0.0
    tot_pw_den = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        areaN = areaB = 0.0
        arr = dep = blk = 0.0
        wait_sum = soj_sum = 0.0
        dep_t_sum = 0.0
        pw_num = pw_den = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            nxt = next_arr
            if servers:
                nxt = min(nxt, servers[0][0])
            if nxt > H:
                dt = H - last
                areaN += n * dt
                areaB += busy * dt
                last = H
                break
            dt = nxt - last
            areaN += n * dt
            areaB += busy * dt
            last = nxt
            t = nxt
            if servers and servers[0][0] <= t:
                _, st = servers.pop(0)
                busy -= 1
                n -= 1
                if t >= warm:
                    dep += 1
                    dep_t_sum += t
                    soj_sum += t - st
                if queue:
                    qt, qst = queue.pop(0)
                    svc = qst
                    if t >= warm:
                        wait_sum += t - qt
                    servers.append((t + svc, t))
                    servers.sort()
                    busy += 1
                    n += 1
            else:
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr += 1
                    pw_den += 1
                if busy < c:
                    servers.append((t + svc, t))
                    servers.sort()
                    busy += 1
                    n += 1
                else:
                    queue.append((t, svc))
                    n += 1
                    if t >= warm:
                        blk += 1
                        pw_num += 1
                next_arr = t + rng.expovariate(lam)

        win = H - warm
        win_total += win
        L = areaN / H if H > 0 else 0.0
        Lw = 0.0
        # recompute windowed L properly: we integrated whole run; approximate windowed by scaling
        # Better: track windowed areas separately
        # (redo with windowed areas)
        # --- second pass for windowed stats ---
        rng2 = random.Random(s)
        t2 = 0.0
        n2 = 0
        busy2 = 0
        queue2 = []
        servers2 = []
        areaN2 = areaB2 = 0.0
        arr2 = dep2 = blk2 = 0.0
        wait2 = soj2 = 0.0
        dep_t2 = 0.0
        pw_num2 = pw_den2 = 0.0
        last2 = 0.0
        next_arr2 = rng2.expovariate(lam)
        while True:
            nxt = next_arr2
            if servers2:
                nxt = min(nxt, servers2[0][0])
            if nxt > H:
                dt = H - last2
                if last2 >= warm:
                    areaN2 += n2 * dt
                    areaB2 += busy2 * dt
                elif H > warm:
                    areaN2 += n2 * (H - warm)
                    areaB2 += busy2 * (H - warm)
                last2 = H
                break
            dt = nxt - last2
            if last2 >= warm:
                areaN2 += n2 * dt
                areaB2 += busy2 * dt
            elif nxt > warm:
                areaN2 += n2 * (nxt - warm)
                areaB2 += busy2 * (nxt - warm)
            last2 = nxt
            t2 = nxt
            if servers2 and servers2[0][0] <= t2:
                _, st = servers2.pop(0)
                busy2 -= 1
                n2 -= 1
                if t2 >= warm:
                    dep2 += 1
                    dep_t2 += t2
                    soj2 += t2 - st
                if queue2:
                    qt, qsvc = queue2.pop(0)
                    if t2 >= warm:
                        wait2 += t2 - qt
                    servers2.append((t2 + qsvc, t2))
                    servers2.sort()
                    busy2 += 1
                    n2 += 1
            else:
                svc = rng2.expovariate(mu)
                if t2 >= warm:
                    arr2 += 1
                    pw_den2 += 1
                if busy2 < c:
                    servers2.append((t2 + svc, t2))
                    servers2.sort()
                    busy2 += 1
                    n2 += 1
                else:
                    queue2.append((t2, svc))
                    n2 += 1
                    if t2 >= warm:
                        blk2 += 1
                        pw_num2 += 1
                next_arr2 = t2 + rng2.expovariate(lam)

        win2 = H - warm
        Lw = areaN2 / win2 if win2 > 0 else 0.0
        bf = areaB2 / (c * win2) if win2 > 0 else 0.0
        Wv = (wait2 + soj2) / dep2 if dep2 > 0 else 0.0
        pl = blk2 / arr2 if arr2 > 0 else 0.0
        pw = pw_num2 / pw_den2 if pw_den2 > 0 else 0.0

        per_L.append(Lw)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)

        tot_arr += arr2
        tot_dep += dep2
        tot_blk += blk2
        tot_areaN += areaN2
        tot_areaB += areaB2
        tot_wait += wait2
        tot_soj += soj2
        tot_dep_t += dep_t2
        tot_pw_num += pw_num2
        tot_pw_den += pw_den2

    ns = len(seeds)
    win = win_total / ns if ns else 0.0
    L = tot_areaN / (ns * win) if win > 0 else 0.0
    busy_frac = tot_areaB / (c * ns * win) if win > 0 else 0.0
    W = (tot_wait + tot_soj) / tot_dep if tot_dep > 0 else 0.0
    p_wait = tot_pw_num / tot_pw_den if tot_pw_den > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / (ns * win) if win > 0 else 0.0
    lam_eff = arr_avg / win if win > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "busy_occupied": 1.0 - (1.0 - busy_frac) if False else busy_frac,
        "p_wait": p_wait,
        "p_loss": p_loss,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win,
        "arr": arr_avg,
        "dep": dep_avg,
        "blk": blk_avg,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
