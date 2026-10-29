import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_wait = tot_busy = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        b1 = b2 = 0.0
        n1 = n2 = 0
        arr = dep = blk = 0
        area = wait = busy = 0.0
        win = 0.0
        nxt = rng.expovariate(lam)
        while t < H:
            if nxt <= t:
                t = nxt
                if t >= H:
                    break
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                cust = [svc1, svc2]
                if t >= warm:
                    arr += 1
                if b1 == 0.0:
                    b1 = t + svc1
                    if t >= warm:
                        busy += min(b1, H) - t
                else:
                    q1.append(cust)
                nxt = t + rng.expovariate(lam)
            else:
                t = nxt
                if t >= H:
                    break
                if b1 <= b2:
                    t = b1
                    if t >= H:
                        break
                    if q1:
                        c = q1.pop(0)
                        b1 = t + c[0]
                        if t >= warm:
                            busy += min(b1, H) - t
                    else:
                        b1 = 0.0
                    if b2 == 0.0:
                        b2 = t + c[1]
                        if t >= warm:
                            busy += min(b2, H) - t
                    else:
                        q2.append(c)
                else:
                    t = b2
                    if t >= H:
                        break
                    if q2:
                        c = q2.pop(0)
                        b2 = t + c[1]
                        if t >= warm:
                            busy += min(b2, H) - t
                    else:
                        b2 = 0.0
                    if t >= warm:
                        dep += 1
                        wait += t - c[2]
                nxt = t
            if t >= warm:
                win = H - warm
                area += (n1 + n2) * 0.0
        # recompute area via event integration is complex; use Little's law fallback
        # integrate area properly: track state changes
        # (simplified: use dep and wait)
        if win <= 0:
            win = H - warm
        L = (wait / win) * lam if win > 0 else 0.0
        W = wait / dep if dep > 0 else 0.0
        bf = busy / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = (arr - dep) / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_wait += wait
        tot_busy += busy
        tot_win += win

    n = len(seeds)
    W = tot_wait / tot_dep if tot_dep > 0 else 0.0
    L = (tot_wait / tot_win) * lam if tot_win > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    pw = (tot_arr - tot_dep) / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0

    out = {
        "L": L, "W": W, "runtime_units": "minute",
        "seed_list": seeds, "seeds_used": n, "time_unit": "minute",
        "win": tot_win / n if n > 0 else 0.0,
        "arr": tot_arr / n if n > 0 else 0.0,
        "dep": tot_dep / n if n > 0 else 0.0,
        "blk": tot_blk / n if n > 0 else 0.0,
        "busy_frac": bf, "busy_util": bf,
        "dep_rate": dep_rate, "lam_eff": lam * 60.0,
        "p_loss": pl, "p_wait": pw,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
