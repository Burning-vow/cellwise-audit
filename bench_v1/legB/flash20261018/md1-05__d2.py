import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0
    tot_serv = 0.0
    tot_serv_n = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        areaN = 0.0
        areaB = 0.0
        win = 0.0
        arr_w = dep_w = blk_w = 0
        wait_sum = 0.0
        wait_n = 0
        serv_sum = 0.0
        serv_n = 0
        last = 0.0
        while t < H:
            dt = min(next_arr, next_dep, H) - t
            if dt > 0:
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                    win += dt
                t += dt
            if t >= H:
                break
            if next_arr <= next_dep:
                if t >= warm:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    serv_sum += st
                    serv_n += 1
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                    next_dep = t + st
                else:
                    if t >= warm:
                        blk_w += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                busy -= 1
                n -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    st = queue.pop(0)
                    busy += 1
                    if t >= warm:
                        wait_sum += (t - st[0])
                        wait_n += 1
                    next_dep = t + st[1]
                else:
                    next_dep = float('inf')
        Ls = areaN / win if win > 0 else 0.0
        Ws = Ls / (dep_w / win) if dep_w > 0 and win > 0 else 0.0
        bfs = areaB / (win * c) if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = wait_n / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += win
        tot_wait += wait_sum
        tot_wait_n += wait_n
        tot_serv += serv_sum
        tot_serv_n += serv_n

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    dep_rate_per_min = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate_per_min if dep_rate_per_min > 0 else 0.0
    busy_util = tot_areaB / (tot_win * c) if tot_win > 0 else 0.0
    busy_occupied = busy_util
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    lam_eff = tot_dep / tot_win if tot_win > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_util,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": tot_win / ns if ns > 0 else 0.0,
        "arr": tot_arr / ns if ns > 0 else 0.0,
        "dep": tot_dep / ns if ns > 0 else 0.0,
        "blk": tot_blk / ns if ns > 0 else 0.0,
        "dep_rate": dep_rate_per_min * 60.0,
        "lam_eff": lam_eff * 60.0,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
