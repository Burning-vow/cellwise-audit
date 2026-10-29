import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    if a.pert == 'lam_up': lam_base *= 1.1
    elif a.pert == 'mu_up': mu_base *= 1.1
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0.0
    total_dep = 0.0
    total_blk = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_stay_time = 0.0
    total_departures_in_win = 0.0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        service_times = {}
        
        area_n = 0.0
        last_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        stay_sum = 0.0
        busy_time = 0.0
        
        while t < horizon:
            if next_arr <= next_dep:
                dt = next_arr - t
                if t >= win_start or (t < win_start and next_arr > win_start):
                    seg_start = max(t, win_start)
                    seg_end = min(next_arr, horizon)
                    if seg_end > seg_start:
                        dur = seg_end - seg_start
                        area_n += n * dur
                        if busy:
                            busy_time += dur
                t = next_arr
                if n == 0:
                    busy = True
                    st = rng.expovariate(mu_base)
                    service_times[t] = st
                    next_dep = t + st
                else:
                    blk_count += 1
                arr_count += 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                dt = next_dep - t
                if t >= win_start or (t < win_start and next_dep > win_start):
                    seg_start = max(t, win_start)
                    seg_end = min(next_dep, horizon)
                    if seg_end > seg_start:
                        dur = seg_end - seg_start
                        area_n += n * dur
                        if busy:
                            busy_time += dur
                t = next_dep
                if t in service_times:
                    del service_times[t]
                n -= 1
                dep_count += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    # Find earliest remaining departure
                    if service_times:
                        next_dep = min(service_times.keys())
                    else:
                        next_dep = float('inf')
        
        # Final segment to horizon
        if t < horizon:
            seg_start = max(t, win_start)
            if seg_start < horizon:
                dur = horizon - seg_start
                area_n += n * dur
                if busy:
                    busy_time += dur
        
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = stay_sum / dep_count if dep_count > 0 else 0.0
        bf_est = busy_time / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = wait_count / arr_count if arr_count > 0 else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_busy_time += busy_time
        total_stay_time += stay_sum
        total_departures_in_win += dep_count
    
    N_seeds = len(seeds_used)
    avg_arr = total_arr / N_seeds
    avg_dep = total_dep / N_seeds
    avg_blk = total_blk / N_seeds
    avg_busy_frac = total_busy_time / (N_seeds * win_len) if win_len > 0 else 0.0
    avg_L = sum(per_seed_L) / N_seeds
    avg_W = sum(per_seed_W) / N_seeds
    avg_p_loss = sum(per_seed_p_loss) / N_seeds
    avg_p_wait = sum(per_seed_p_wait) / N_seeds
    dep_rate = avg_dep / win_len * 60.0 if win_len > 0 else 0.0  # per hour? No, dep is count, win_len in hours. Rate = count/hour.
    # Actually dep_rate should be effective departure rate in units of "per hour". 
    # avg_dep is average number of departures per seed in window. Window length is win_len hours.
    # So rate = avg_dep / win_len. But the prompt says "个/每小时".
    dep_rate_val = avg_dep / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate_val
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_frac, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
