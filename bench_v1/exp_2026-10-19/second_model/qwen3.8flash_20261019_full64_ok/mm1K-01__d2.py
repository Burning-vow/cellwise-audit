import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    
    if a.pert == 'lam_up': lam = lam_base * 1.2
    elif a.pert == 'mu_up': mu = mu_base * 1.2
    elif a.pert == 'c_up': c = 2
    else: lam, mu, c = lam_base, mu_base, 1
    
    if a.pert != 'c_up': c = 1
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time_in_system = 0.0
    total_busy_time = 0.0
    total_non_empty_time = 0.0
    total_wait_time = 0.0
    total_customers_served = 0
    
    horizon_hours = a.horizon / 60.0 if a.time_unit == 'minute' else a.horizon
    time_unit = 'hour'
    horizon = a.horizon
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        busy_until = -1.0
        n = 0
        
        warmup_end = horizon * 0.25
        stats_t = 0.0
        last_stats_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        area_non_empty = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sum_w = 0.0
        sum_wait = 0.0
        
        while t < horizon:
            events = []
            if next_arr < horizon: events.append(('arr', next_arr))
            if busy_until >= 0 and busy_until < horizon: events.append(('dep', busy_until))
            
            if not events: break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            if ev_time > last_stats_t:
                dt = ev_time - last_stats_t
                if ev_time > warmup_end:
                    start_int = max(last_stats_t, warmup_end)
                    int_dt = ev_time - start_int
                    if int_dt > 0:
                        area_n += n * int_dt
                        if n > 0:
                            area_busy += int_dt
                            area_non_empty += int_dt
                last_stats_t = ev_time
            
            t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if n < 4:
                    if n == 0:
                        busy_until = t + st
                        service_times[t] = st
                        n += 1
                    else:
                        queue.append((t, st))
                        n += 1
                else:
                    blk_count += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                dep_count += 1
                n -= 1
                if queue:
                    arr_t, st = queue.pop(0)
                    wait = t - arr_t
                    sum_wait += wait
                    sum_w += wait + st
                    busy_until = t + st
                    service_times[t] = st
                    n += 1
                else:
                    busy_until = -1.0
        
        if last_stats_t < horizon:
            dt = horizon - last_stats_t
            if horizon > warmup_end:
                start_int = max(last_stats_t, warmup_end)
                int_dt = horizon - start_int
                if int_dt > 0:
                    area_n += n * int_dt
                    if n > 0:
                        area_busy += int_dt
                        area_non_empty += int_dt
        
        win_len = horizon - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_n / win_len
        W_est = sum_w / dep_count if dep_count > 0 else 0.0
        busy_frac_est = area_non_empty / win_len
        p_loss_est = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0.0
        p_wait_est = sum_wait / dep_count if dep_count > 0 else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += arr_count
        total_blk += blk_count
        total_dep += dep_count
        total_time_in_system += sum_w
        total_busy_time += area_busy
        total_non_empty_time += area_non_empty
        total_wait_time += sum_wait
        total_customers_served += dep_count

    N_seeds = len(seeds_used)
    avg_L = sum(per_seed_L) / N_seeds
    avg_W = sum(per_seed_W) / N_seeds
    avg_busy_frac = sum(per_seed_busy_frac) / N_seeds
    avg_p_loss = sum(per_seed_p_loss) / N_seeds
    avg_p_wait = sum(per_seed_p_wait) / N_seeds
    
    avg_arr = total_arr / N_seeds
    avg_blk = total_blk / N_seeds
    avg_dep = total_dep / N_seeds
    
    total_win = N_seeds * (horizon - horizon*0.25)
    dep_rate = avg_dep / ((horizon - horizon*0.25)/60.0) if time_unit=='minute' else avg_dep / (horizon - horizon*0.25)
    lam_eff = dep_rate
    
    busy_util = avg_busy_frac
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used,
        "seeds_used": N_seeds,
        "time_unit": "hour",
        "win": round(horizon - horizon*0.25, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
