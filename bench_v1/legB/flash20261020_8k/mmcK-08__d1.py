import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 10.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 4
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaBusy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = 0.0
        areaBusy = 0.0
        win_arr = win_dep = win_blk = 0.0
        win_wait = 0.0
        win_waited = 0.0
        win_served = 0.0
        last_t = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy > 0 else 0) * dt
                t = next_arr
                if t >= warm:
                    win_arr += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if busy < c:
                        busy += 1
                        arr_t, sv = queue.pop(0)
                        dep_t = t + sv
                        queue.insert(0, (arr_t, sv))
                        queue[0] = (arr_t, sv, dep_t)
                else:
                    if t >= warm:
                        win_blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                arr_t, sv, dep_t = queue[0]
                if next_arr < dep_t:
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                    t = next_arr
                    if t >= warm:
                        win_arr += 1
                    if n < cap:
                        n += 1
                        svc = rng.expovariate(mu)
                        if busy < c:
                            busy += 1
                            queue.append((t, svc, t + svc))
                        else:
                            queue.append((t, svc))
                    else:
                        if t >= warm:
                            win_blk += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    dt = dep_t - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                    t = dep_t
                    n -= 1
                    busy -= 1
                    queue.pop(0)
                    if t >= warm:
                        win_dep += 1
                        win_served += 1
                        win_wait += arr_t - arr_t
                        win_waited += 0
                    if queue:
                        arr_t2, sv2 = queue[0][0], queue[0][1]
                        busy += 1
                        queue[0] = (arr_t2, sv2, t + sv2)
                    if t >= H:
                        break
        w = H - warm
        tot_win += w
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        L = areaN / w if w > 0 else 0.0
        bf = areaBusy / w if w > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        W = (areaN / win_dep) if win_dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(0.0)

    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    W = (tot_areaN / tot_dep) if tot_dep > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0
    busy_util = min(L, c) / c if c > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_loss": p_loss,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "minute",
        "win": tot_win / len(seeds) if seeds else 0.0,
        "arr": tot_arr / len(seeds) if seeds else 0.0,
        "blk": tot_blk / len(seeds) if seeds else 0.0,
        "busy_util": busy_util,
        "busy_occupied": busy_frac,
        "dep": tot_dep / len(seeds) if seeds else 0.0,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_wait": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
