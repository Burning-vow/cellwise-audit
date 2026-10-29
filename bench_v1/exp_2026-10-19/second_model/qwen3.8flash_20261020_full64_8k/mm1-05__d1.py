import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_h = 7.0; mu_min = 6.0
    if a.pert == "lam_up": lam_h *= 1.1
    elif a.pert == "mu_up": mu_min /= 1.1
    elif a.pert == "c_up": pass
    time_unit = "minute"
    horizon = a.horizon * 60.0 if time_unit == "minute" else a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    seeds_used = 0
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []
    per_seed_p_loss = []; per_seed_p_wait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    seed_list = []
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0; N = 0; busy = False
        next_arr = rng.expovariate(lam_h / 60.0)
        next_dep = float('inf')
        custs = []
        area_N = 0.0; area_busy = 0.0; n_arr_w = 0; n_dep_w = 0; n_blk_w = 0
        sum_W = 0.0; n_wait_w = 0
        last_t = 0.0
        while t < horizon:
            dt_arr = next_arr - t
            dt_dep = next_dep - t if busy else float('inf')
            if dt_arr <= dt_dep and dt_arr >= 0:
                ev_t = next_arr
            elif dt_dep < dt_arr and dt_dep >= 0:
                ev_t = next_dep
            else:
                break
            if ev_t > horizon:
                break
            delta = ev_t - t
            if t >= win_start:
                area_N += N * delta
                area_busy += (1 if busy else 0) * delta
            t = ev_t
            if abs(ev_t - next_arr) < 1e-9:
                svc = rng.expovariate(1.0 / mu_min)
                custs.append((t, svc))
                n_arr_w += 1 if t >= win_start else 0
                if not busy:
                    busy = True
                    next_dep = t + svc
                else:
                    if len(custs) > 10000:
                        n_blk_w += 1 if t >= win_start else 0
                        custs.pop(0)
                next_arr = t + rng.expovariate(lam_h / 60.0)
            else:
                if custs:
                    arr_t, _ = custs.pop(0)
                    W_val = t - arr_t
                    if t >= win_start:
                        sum_W += W_val
                        n_wait_w += 1
                    n_dep_w += 1 if t >= win_start else 0
                if custs:
                    next_dep = t + custs[0][1]
                else:
                    busy = False
                    next_dep = float('inf')
        if t >= win_start:
            area_N += N * (horizon - t)
            area_busy += (1 if busy else 0) * (horizon - t)
        win_len = horizon - win_start
        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = sum_W / n_wait_w if n_wait_w > 0 else 0.0
        bf_est = area_busy / win_len if win_len > 0 else 0.0
        pl_est = n_blk_w / n_arr_w if n_arr_w > 0 else 0.0
        pw_est = n_wait_w / n_arr_w if n_arr_w > 0 else 0.0
        per_seed_L.append(L_est); per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est); per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        total_arr += n_arr_w; total_dep += n_dep_w; total_blk += n_blk_w
        seeds_used += 1
    avg_L = sum(per_seed_L) / seeds_used if seeds_used else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used else 0.0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used else 0.0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used else 0.0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used else 0.0
    arr_avg = total_arr / seeds_used if seeds_used else 0.0
    dep_avg = total_dep / seeds_used if seeds_used else 0.0
    blk_avg = total_blk / seeds_used if seeds_used else 0.0
    win_len = horizon - win_start
    dep_rate = (total_dep / seeds_used) / (win_len / 60.0) if seeds_used and win_len > 0 else 0.0
    lam_eff = dep_rate
    busy_util = avg_bf
    busy_occ = avg_bf
    out = {
        "L": round(avg_L, 6), "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6), "p_wait": round(avg_pw, 6),
        "runtime_units": time_unit, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6), "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6), "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6), "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occ, 6)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
