import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N = a.seeds; H = a.horizon; S = a.seed_start; pert = a.pert
    lam = 8.0; mu = 10.0; c = 1
    if pert == "lam_up": lam *= 1.2
    elif pert == "mu_up": mu *= 1.2
    elif pert == "c_up": c += 1
    time_unit = "hour"
    warmup_frac = 0.25
    seeds_used = 0
    all_L = []; all_W = []; all_busy = []; all_ploss = []; all_pwait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0; n_in_sys = 0; busy_time = 0.0; last_event_t = 0.0
        arr_count = 0; dep_count = 0; blk_count = 0
        wait_count = 0
        # state: next arrival time, service end time (if busy), queue list of arrival times
        next_arr = rng.expovariate(lam)
        svc_end = float('inf')
        queue = []
        area_L = 0.0; area_busy = 0.0; area_wait = 0.0
        warmup_t = H * warmup_frac
        while True:
            # determine next event
            ev_arr = next_arr if next_arr <= H else float('inf')
            ev_svc = svc_end if svc_end <= H else float('inf')
            if ev_arr == float('inf') and ev_svc == float('inf'):
                break
            if ev_arr <= ev_svc:
                dt = ev_arr - t
                if t >= warmup_t:
                    area_L += n_in_sys * dt
                    area_busy += min(n_in_sys, c) * dt
                    if queue:
                        area_wait += len(queue) * dt
                t = ev_arr
                arr_count += 1
                if n_in_sys < c:
                    n_in_sys += 1
                    dur = rng.expovariate(mu)
                    svc_end = t + dur
                else:
                    if n_in_sys >= c + 1000:
                        blk_count += 1
                    else:
                        queue.append(t)
                        n_in_sys += 1
                        wait_count += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dt = ev_svc - t
                if t >= warmup_t:
                    area_L += n_in_sys * dt
                    area_busy += min(n_in_sys, c) * dt
                    if queue:
                        area_wait += len(queue) * dt
                t = ev_svc
                dep_count += 1
                if queue:
                    at = queue.pop(0)
                    n_in_sys -= 1
                    dur = rng.expovariate(mu)
                    svc_end = t + dur
                else:
                    n_in_sys -= 1
                    svc_end = float('inf')
        win_len = H - warmup_t
        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = area_L / dep_count if dep_count > 0 else 0.0
        busy_est = area_busy / win_len if win_len > 0 else 0.0
        ploss_est = blk_count / arr_count if arr_count > 0 else 0.0
        pwait_est = wait_count / arr_count if arr_count > 0 else 0.0
        all_L.append(L_est); all_W.append(W_est); all_busy.append(busy_est)
        all_ploss.append(ploss_est); all_pwait.append(pwait_est)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
        seeds_used += 1
    avg_L = sum(all_L)/seeds_used if seeds_used else 0.0
    avg_W = sum(all_W)/seeds_used if seeds_used else 0.0
    avg_busy = sum(all_busy)/seeds_used if seeds_used else 0.0
    avg_ploss = sum(all_ploss)/seeds_used if seeds_used else 0.0
    avg_pwait = sum(all_pwait)/seeds_used if seeds_used else 0.0
    per_seed_avg_arr = total_arr/seeds_used if seeds_used else 0.0
    per_seed_avg_dep = total_dep/seeds_used if seeds_used else 0.0
    per_seed_avg_blk = total_blk/seeds_used if seeds_used else 0.0
    dep_rate = per_seed_avg_dep / (H - H*warmup_frac) * 60.0 if (H*(1-warmup_frac))>0 else 0.0
    lam_eff = dep_rate
    result = {
        "L": round(avg_L,6), "W": round(avg_W,6), "busy_frac": round(avg_busy,6),
        "p_wait": round(avg_pwait,6), "runtime_units": time_unit,
        "seed_list": [S+i for i in range(seeds_used)], "seeds_used": seeds_used,
        "time_unit": time_unit, "win": round(H*(1-warmup_frac),6),
        "arr": round(per_seed_avg_arr,6), "blk": round(per_seed_avg_blk,6),
        "busy_util": round(avg_busy,6), "dep": round(per_seed_avg_dep,6),
        "dep_rate": round(dep_rate,6), "lam_eff": round(lam_eff,6),
        "p_loss": round(avg_ploss,6),
        "per_seed_L": [round(x,6) for x in all_L],
        "per_seed_W": [round(x,6) for x in all_W],
        "per_seed_busy_frac": [round(x,6) for x in all_busy],
        "per_seed_p_loss": [round(x,6) for x in all_ploss],
        "per_seed_p_wait": [round(x,6) for x in all_pwait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
