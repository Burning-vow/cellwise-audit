import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base = 4.0; mu_base = 12.0; c = 1
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": c += 1
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        service_time = 60.0 / mu_base
        queue = []
        busy_until = -1.0
        n_in_sys = 0
        area_n = 0.0
        last_event_t = 0.0
        arr_count = 0; dep_count = 0; blk_count = 0
        wait_sum = 0.0; wait_count = 0
        while True:
            if next_arr < float('inf') and (busy_until < 0 or next_arr <= busy_until):
                ev_t = next_arr
                dt = ev_t - last_event_t
                if ev_t > win_start:
                    area_n += n_in_sys * min(dt, ev_t - max(last_event_t, win_start)) if last_event_t < win_start else n_in_sys * dt
                # simpler: integrate only within window
                if last_event_t < win_start and ev_t > win_start:
                    area_n += n_in_sys * (ev_t - win_start)
                elif last_event_t >= win_start:
                    area_n += n_in_sys * dt
                last_event_t = ev_t
                if n_in_sys < c:
                    n_in_sys += 1
                    arr_count += 1
                    start_t = ev_t
                    end_t = start_t + service_time
                    queue.append((start_t, end_t))
                    busy_until = end_t
                    next_arr = ev_t + rng.expovariate(lam_base)
                else:
                    blk_count += 1
                    next_arr = ev_t + rng.expovariate(lam_base)
            else:
                if not queue:
                    break
                ev_t = queue[0][1]
                dt = ev_t - last_event_t
                if last_event_t < win_start and ev_t > win_start:
                    area_n += n_in_sys * (ev_t - win_start)
                elif last_event_t >= win_start:
                    area_n += n_in_sys * dt
                last_event_t = ev_t
                st, et = queue.pop(0)
                n_in_sys -= 1
                dep_count += 1
                w = et - st
                if st >= win_start:
                    wait_sum += w
                    wait_count += 1
                if queue:
                    busy_until = queue[-1][1]
                else:
                    busy_until = -1.0
                if ev_t >= horizon:
                    break
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = wait_sum / wait_count if wait_count > 0 else 0.0
        busy_frac_est = (area_n / win_len) if win_len > 0 else 0.0
        p_loss_est = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0.0
        p_wait_est = 0.0
        all_L.append(L_est); all_W.append(W_est); all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est); all_p_wait.append(p_wait_est)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
    avg_L = sum(all_L)/len(all_L) if all_L else 0.0
    avg_W = sum(all_W)/len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_loss = sum(all_p_loss)/len(all_p_loss) if all_p_loss else 0.0
    avg_p_wait = sum(all_p_wait)/len(all_p_wait) if all_p_wait else 0.0
    arr_avg = total_arr/seeds_used; dep_avg = total_dep/seeds_used; blk_avg = total_blk/seeds_used
    dep_rate = dep_avg / (win_len/60.0) if win_len > 0 else 0.0
    lam_eff = arr_avg / (win_len/60.0) if win_len > 0 else 0.0
    out = {
        "L": round(avg_L,6), "W": round(avg_W,6), "busy_frac": round(avg_busy_frac,6),
        "runtime_units": "minute", "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "minute", "win": round(win_len,6),
        "arr": round(arr_avg,6), "blk": round(blk_avg,6), "busy_util": round(avg_busy_frac,6),
        "dep": round(dep_avg,6), "dep_rate": round(dep_rate,6), "lam_eff": round(lam_eff,6),
        "p_loss": round(avg_p_loss,6), "p_wait": round(avg_p_wait,6),
        "per_seed_L": [round(x,6) for x in all_L], "per_seed_W": [round(x,6) for x in all_W],
        "per_seed_busy_frac": [round(x,6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x,6) for x in all_p_loss],
        "per_seed_p_wait": [round(x,6) for x in all_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
