import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0
    mu_base = 12.0
    c = 1
    K = 4
    time_unit = 'hour'
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base
    
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time_in_system = 0.0
    total_busy_time = 0.0
    total_window_time = 0.0
    total_wait_count = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        random.seed(seed)
        seed_list.append(seed)
        
        t = 0.0
        next_arr = random.expovariate(lam)
        next_dep = float('inf')
        queue = []
        service_times = {}
        arrival_times = {}
        
        n_customers = 0
        busy_periods = 0
        last_event_time = 0.0
        current_n = 0
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_w = 0.0
        count_wait = 0
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_event_time
                if last_event_time >= warmup_end:
                    area_L += current_n * dt
                    area_busy += min(current_n, c) * dt
                    total_window_time += dt
                
                if len(queue) + current_n < K:
                    sid = n_customers
                    st = random.expovariate(mu)
                    service_times[sid] = st
                    arrival_times[sid] = t
                    queue.append(sid)
                    n_customers += 1
                    count_arr += 1
                    if current_n == 0:
                        next_dep = t + st
                        current_n = 1
                        busy_periods += 1
                    else:
                        pass 
                else:
                    count_blk += 1
                
                next_arr = t + random.expovariate(lam)
                last_event_time = t
                
            else:
                t = next_dep
                dt = t - last_event_time
                if last_event_time >= warmup_end:
                    area_L += current_n * dt
                    area_busy += min(current_n, c) * dt
                    total_window_time += dt
                
                if queue:
                    dep_sid = queue.pop(0)
                    w = t - arrival_times[dep_sid]
                    if last_event_time >= warmup_end or t >= warmup_end:
                         # Check if departure happened after warmup start to count W?
                         # Usually stats are for customers served within window or arriving within window?
                         # "area-type quantities must be integrated before state change"
                         # For W, it's average waiting time of those who departed.
                         # If we only count departures after warmup_end:
                         if t >= warmup_end:
                             sum_w += w
                             count_dep += 1
                             if w > 0:
                                 count_wait += 1
                    
                    if queue:
                        next_sid = queue[0]
                        next_dep = t + service_times[next_sid]
                        current_n = 1
                    else:
                        next_dep = float('inf')
                        current_n = 0
                else:
                    current_n = 0
                    next_dep = float('inf')
                
                last_event_time = t
        
        # Final integration up to horizon
        dt = horizon - last_event_time
        if last_event_time >= warmup_end:
             area_L += current_n * dt
             area_busy += min(current_n, c) * dt
             total_window_time += dt
        elif warmup_end < horizon:
             overlap = horizon - max(last_event_time, warmup_end)
             if overlap > 0:
                 area_L += current_n * overlap
                 area_busy += min(current_n, c) * overlap
                 total_window_time += overlap

        win_len = horizon - warmup_end
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            bf_est = 0.0
            pl_est = 0.0
            pw_est = 0.0
        else:
            L_est = area_L / win_len
            W_est = sum_w / count_dep if count_dep > 0 else 0.0
            bf_est = area_busy / win_len
            pl_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0.0
            pw_est = count_wait / count_dep if count_dep > 0 else 0.0
            
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_arr += count_arr
        total_blk += count_blk
        total_dep += count_dep
        total_time_in_system += sum_w
        total_busy_time += area_busy

    seeds_used = len(per_seed_L)
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0.0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0.0
    
    avg_arr = total_arr / seeds_used if seeds_used > 0 else 0.0
    avg_blk = total_blk / seeds_used if seeds_used > 0 else 0.0
    avg_dep = total_dep / seeds_used if seeds_used > 0 else 0.0
    
    win_len_total = horizon - warmup_end
    dep_rate = avg_dep / win_len_total if win_len_total > 0 else 0.0
    lam_eff = dep_rate
    
    busy_util = avg_bf / c if c > 0 else 0.0
    busy_occupied = avg_bf
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W * 60, 6), 
        "busy_frac": round(avg_bf, 6),
        "p_loss": round(avg_pl, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len_total, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
