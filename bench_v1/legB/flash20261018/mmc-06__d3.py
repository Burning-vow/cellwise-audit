import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 14.0
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
    tot_wait = tot_soj = 0.0
    tot_dep_n = 0
    tot_wait_n = 0
    tot_arr_n = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        areaN = 0.0
        areaB = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_n = 0
        soj_sum = 0.0
        dep_n = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while t < H:
            cand = next_arr
            if servers:
                cand = min(cand, min(servers))
            if cand >= H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = cand - t
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
            t = cand
            if t == next_arr:
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                        soj_sum += svc
                        dep_n += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        blk_w += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                servers.remove(cand)
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += (t - at)
                        wait_n += 1
                        soj_sum += (t - at) + svc
                        dep_n += 1
        win = H - warm
        win_total += win
        Ls = areaN / win if win > 0 else 0.0
        bf = (areaB / win) / c if win > 0 else 0.0
        Ws = (soj_sum / dep_n) if dep_n > 0 else 0.0
        pw = (blk_w / arr_w) if arr_w > 0 else 0.0
        pl = (blk_w / arr_w) if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_n += dep_n
        tot_wait_n += wait_n
        tot_arr_n += arr_w

    L = tot_areaN / win_total if win_total > 0 else 0.0
    busy_frac = (tot_areaB / win_total) / c if win_total > 0 else 0.0
    W = tot_soj / tot_dep_n if tot_dep_n > 0 else 0.0
    p_wait = tot_blk / tot_arr_n if tot_arr_n > 0 else 0.0
    p_loss = p_wait
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = dep / (win_total / len(seeds)) if win_total > 0 else 0.0
    lam_eff = arr / (win_total / len(seeds)) if win_total > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "busy_occupied": busy_frac,
        "p_wait": p_wait,
        "p_loss": p_loss,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "minute",
        "win": win_total / len(seeds),
        "arr": arr,
        "dep": dep,
        "blk": blk,
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
