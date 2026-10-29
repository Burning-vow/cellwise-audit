import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 3.0, 10.0
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": pass
    time_unit = "hour"
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    seeds_used = a.seeds
    seed_list = list(range(a.seed_start, a.seed_start + seeds_used))
    all_L, all_W, all_busy, all_ploss, all_pwait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; N = 0; busy = False; service_end = float('inf')
        arr_count = dep_count = blk_count = 0
        area_N = 0.0; area_wait = 0.0; area_busy = 0.0; area_occupied = 0.0
        wait_sum = 0.0; n_served = 0
        next_arr = rng.expovariate(lam_base)
        while t < horizon:
            if not busy and next_arr <= t:
                dt = next_arr - t
                area_N += N * dt; area_busy += (1 if busy else 0) * dt
                area_occupied += (1 if busy else 0) * dt
                t = next_arr
                if t >= win_start:
                    arr_count += 1
                    if N >= 1:
                        blk_count += 1
                    else:
                        dur = rng.expovariate(mu_base)
                        service_end = t + dur
                        busy = True; N += 1
                else:
                    if N >= 1: pass
                    else:
                        dur = rng.expovariate(mu_base)
                        service_end = t + dur
                        busy = True; N += 1
                next_arr = t + rng.expovariate(lam_base)
            elif busy and service_end <= t:
                dt = service_end - t
                area_N += N * dt; area_busy += (1 if busy else 0) * dt
                area_occupied += (1 if busy else 0) * dt
                t = service_end
                if t >= win_start:
                    dep_count += 1
                    if N > 0: N -= 1
                    busy = False
                else:
                    if N > 0: N -= 1
                    busy = False
            else:
                dt = min(next_arr, service_end) - t
                area_N += N * dt; area_busy += (1 if busy else 0) * dt
                area_occupied += (1 if busy else 0) * dt
                t = min(next_arr, service_end)
        L_est = area_N / (horizon - win_start) if horizon > win_start else 0
        W_est = wait_sum / n_served if n_served > 0 else 0
        busy_est = area_busy / (horizon - win_start) if horizon > win_start else 0
        occ_est = area_occupied / (horizon - win_start) if horizon > win_start else 0
        ploss_est = blk_count / arr_count if arr_count > 0 else 0
        pwait_est = 0.0
        all_L.append(L_est); all_W.append(W_est); all_busy.append(busy_est)
        all_ploss.append(ploss_est); all_pwait.append(pwait_est)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_busy = sum(all_busy)/len(all_busy) if all_busy else 0
    avg_ploss = sum(all_ploss)/len(all_ploss) if all_ploss else 0
    avg_pwait = sum(all_pwait)/len(all_pwait) if all_pwait else 0
    per_seed_L = [round(x,6) for x in all_L]
    per_seed_W = [round(x,6) for x in all_W]
    per_seed_busy_frac = [round(x,6) for x in all_busy]
    per_seed_p_loss = [round(x,6) for x in all_ploss]
    per_seed_p_wait = [round(x,6) for x in all_pwait]
    win_len = horizon - win_start
    dep_rate = total_dep / seeds_used / win_len * 60 if win_len > 0 else 0
    result = {
        "L": round(avg_L,6), "W": round(avg_W,6), "busy_frac": round(avg_busy,6),
        "runtime_units": round(horizon,6), "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": time_unit, "win": round(win_len,6),
        "arr": round(total_arr/seeds_used,6), "blk": round(total_blk/seeds_used,6),
        "busy_util": round(avg_busy,6), "dep": round(total_dep/seeds_used,6),
        "dep_rate": round(dep_rate,6), "lam_eff": round((total_dep/seeds_used)/win_len*60,6) if win_len>0 else 0,
        "p_loss": round(avg_ploss,6), "p_wait": round(avg_pwait,6),
        "per_seed_L": per_seed_L, "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac, "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
