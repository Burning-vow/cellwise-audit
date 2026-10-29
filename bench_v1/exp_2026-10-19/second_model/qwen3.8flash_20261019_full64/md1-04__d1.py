import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 12.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    win_len = horizon - warmup_end
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_area_N = 0.0
    total_busy_time = 0.0
    
    for i in range(a.seeds):
        seed_val = a.seed_start + i
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        n = 0
        queue = []
        
        last_event_time = 0.0
        area_n = 0.0
        busy_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        time_in_sys_sum = 0.0
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_event_time
                if last_event_time < warmup_end and t > warmup_end:
                    split_dt = warmup_end - last_event_time
                    area_n += n * split_dt
                    if n > 0:
                        busy_time += split_dt
                    remaining_dt = t - warmup_end
                    area_n += n * remaining_dt
                    if n > 0:
                        busy_time += remaining_dt
                elif last_event_time >= warmup_end:
                    area_n += n * dt
                    if n > 0:
                        busy_time += dt
                elif t <= warmup_end:
                    pass
                
                last_event_time = t
                arr_count += 1
                service_time = 1.0 / mu
                if n == 0:
                    n = 1
                    next_dep = t + service_time
                    queue.append((t, service_time))
                else:
                    n += 1
                    queue.append((t, service_time))
                    if n == 1:
                        next_dep = t + service_time
                
                next_arr = t + rng.expovariate(lam)
                
            else:
                t = next_dep
                dt = t - last_event_time
                if last_event_time < warmup_end and t > warmup_end:
                    split_dt = warmup_end - last_event_time
                    area_n += n * split_dt
                    if n > 0:
                        busy_time += split_dt
                    remaining_dt = t - warmup_end
                    area_n += n * remaining_dt
                    if n > 0:
                        busy_time += remaining_dt
                elif last_event_time >= warmup_end:
                    area_n += n * dt
                    if n > 0:
                        busy_time += dt
                elif t <= warmup_end:
                    pass
                    
                last_event_time = t
                
                if queue:
                    arrival_time, svc_dur = queue.pop(0)
                    dep_count += 1
                    time_in_sys_sum += (t - arrival_time)
                    n -= 1
                    if n > 0:
                        next_svc = queue[0][1]
                        next_dep = t + next_svc
                    else:
                        next_dep = float('inf')
        
        final_dt = horizon - last_event_time
        if last_event_time < warmup_end and horizon > warmup_end:
            split_dt = warmup_end - last_event_time
            area_n += n * split_dt
            if n > 0:
                busy_time += split_dt
            remaining_dt = horizon - warmup_end
            area_n += n * remaining_dt
            if n > 0:
                busy_time += remaining_dt
        elif last_event_time >= warmup_end:
            area_n += n * final_dt
            if n > 0:
                busy_time += final_dt
        
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = time_in_sys_sum / dep_count if dep_count > 0 else 0
        bf_est = busy_time / win_len if win_len > 0 else 0
        pl_est = blk_count / arr_count if arr_count > 0 else 0
        pw_est = 1.0 - (dep_count / arr_count) if arr_count > 0 else 0
        
        seeds_used.append(seed_val)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_time_in_sys += time_in_sys_sum
        total_area_N += area_n
        total_busy_time += busy_time
        
    num_seeds = len(seeds_used)
    avg_arr = total_arr / num_seeds if num_seeds > 0 else 0
    avg_dep = total_dep / num_seeds if num_seeds > 0 else 0
    avg_blk = total_blk / num_seeds if num_seeds > 0 else 0
    
    overall_L = total_area_N / (win_len * num_seeds) if num_seeds > 0 and win_len > 0 else 0
    overall_W = total_time_in_sys / total_dep if total_dep > 0 else 0
    overall_bf = total_busy_time / (win_len * num_seeds) if num_seeds > 0 and win_len > 0 else 0
    overall_pl = total_blk / total_arr if total_arr > 0 else 0
    overall_pw = 1.0 - (total_dep / total_arr) if total_arr > 0 else 0
    
    dep_rate = (avg_dep / win_len) * 60.0 if win_len > 0 else 0
    lam_eff = (avg_arr / win_len) * 60.0 if win_len > 0 else 0
    
    result = {
        "L": round(overall_L, 4),
        "W": round(overall_W, 4),
        "busy_frac": round(overall_bf, 4),
        "runtime_units": "minute",
        "seed_list": seeds_used,
        "seeds_used": num_seeds,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(overall_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(overall_pl, 4),
        "p_wait": round(overall_pw, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
