import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait_n = 0
    tot_wait_sum = 0.0
    tot_served = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        arr_c = dep_c = blk_c = 0
        wait_sum = 0.0
        wait_n = 0
        served = 0
        queue = []
        server_free = 0.0
        last = 0.0
        while True:
            if n == 0:
                dt = next_arr - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                    win_area += dt
                t += dt
                if t >= H:
                    break
                n += 1
                busy = 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
                if t >= warm:
                    arr_c += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dt = next_arr - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                    win_area += dt
                t += dt
                if t >= H:
                    break
                n += 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
                if t >= warm:
                    arr_c += 1
                next_arr = t + rng.expovariate(lam)
            while queue and queue[0][0] + queue[0][1] <= t:
                at, sv = queue.pop(0)
                n -= 1
                if n == 0:
                    busy = 0
                if at + sv >= warm:
                    dep_c += 1
                    served += 1
                    wait_sum += (at + sv - at)
                    wait_n += 1
        w = win_area
        L = area / w if w > 0 else 0.0
        bf = busy_area / w if w > 0 else 0.0
        W = L / (arr_c / w) if arr_c > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_win += w
        tot_wait_n += wait_n
        tot_wait_sum += wait_sum
        tot_served += served

    L = tot_area / tot_win if tot_win > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_rate = tot_arr / tot_win if tot_win > 0 else 0.0
    W = L / arr_rate if arr_rate > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    lam_eff = arr_rate * (1 - p_loss)

    out = {
        "L": L,
        "W": W,
        "busy_frac": bf,
        "busy_util": bf,
        "busy_occupied": bf,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "hour",
        "win": tot_win / len(seeds) if seeds else 0.0,
        "arr": tot_arr / len(seeds) if seeds else 0.0,
        "dep": tot_dep / len(seeds) if seeds else 0.0,
        "blk": tot_blk / len(seeds) if seeds else 0.0,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
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
