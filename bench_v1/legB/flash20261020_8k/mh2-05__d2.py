import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0
    mean_s = 0.1
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p2 = min(max(p2, 1e-9), 1.0 - 1e-9)
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2)))) if var_s > mean_s**2 else mean_s * 0.5
    m1 = max(m1, 1e-12)
    m2 = max(mean_s - p2 * m1, 1e-12) / (1.0 - p2) if p2 < 1.0 else m1
    m2 = max(m2, 1e-12)

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        win_start = warm
        last = 0.0
        while t < H:
            if busy:
                dt = min(rem, H - t)
                if t + dt > win_start:
                    s0 = max(t, win_start)
                    area += (t + dt - s0)
                    busy_area += (t + dt - s0)
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    if t > win_start:
                        dep_c += 1
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t < H and t + dt > win_start:
                        area += (H - max(t, win_start)) if H > win_start else 0.0
                    t = H
                    break
                t += dt
                if t > win_start:
                    area += (t - max(last, win_start)) if t > win_start else 0.0
                last = t
                arr_c += 1
                u = rng.random()
                s = m1 if u < p2 else m2
                if t > win_start:
                    wait_n += 1
                busy = True
                rem = s
                if t > win_start:
                    wait_area += 0.0
        win_len = max(H - warm, 1e-12)
        Lv = area / win_len
        Wv = (area / max(dep_c, 1)) if dep_c > 0 else 0.0
        bf = busy_area / win_len
        pl = blk_c / max(arr_c, 1)
        pw = wait_n / max(arr_c, 1)
        per_L.append(Lv)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_win += win_len

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns

    out = {
        "L": L,
        "W": W,
        "busy_frac": bf,
        "busy_util": bf,
        "busy_occupied": bf,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "hour",
        "win": win,
        "arr": arr,
        "dep": dep,
        "blk": blk,
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
