import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    if args.pert == "lam_up":
        lam = lam_base * 1.1
    elif args.pert == "mu_up":
        mu = mu_base * 1.1
    else:
        lam = lam_base
        mu = mu_base
    
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        busy_until = None
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        total_time_in_sys = 0.0
        area_n = 0.0
        last_event_t = 0.0
        prev_n = 0
        busy_periods_area = 0.0
        last_busy_start = None
        idle_periods_area = 0.0
        last_idle_start = 0.0
        
        events = []
        
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        
        add_event(next_arr, 'arr', None)
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            t_curr, typ, data = events.pop(0)
            
            if t_curr > horizon:
                break
            
            dt = t_curr - last_event_t
            if last_event_t >= win_start or (last_event_t < win_start and t_curr > win_start):
                overlap_start = max(last_event_t, win_start)
                overlap_end = min(t_curr, horizon)
                if overlap_end > overlap_start:
                    odt = overlap_end - overlap_start
                    area_n += prev_n * odt
                    if prev_n > 0:
                        busy_periods_area += odt
                    else:
                        idle_periods_area += odt
            
            last_event_t = t_curr
            
            if typ == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if n == 0 and busy_until is None:
                    n += 1
                    prev_n = n
                    busy_until = t_curr + st
                    add_event(busy_until, 'dep', {'start': t_curr, 'st': st})
                else:
                    n += 1
                    prev_n = n
                    queue.append({'arrival': t_curr, 'st': st})
                    if busy_until is None:
                        cust = queue.pop(0)
                        n -= 1
                        prev_n = n
                        busy_until = t_curr + cust['st']
                        add_event(busy_until, 'dep', {'start': t_curr, 'cust': cust})
                
                next_arr = t_curr + rng.expovariate(lam)
                add_event(next_arr, 'arr', None)
                
            elif typ == 'dep':
                dep_count += 1
                cust_data = data
                if 'cust' in cust_data:
                    cust = cust_data['cust']
                    arrival_t = cust['arrival']
                    st = cust['st']
                else:
                    arrival_t = cust_data['start']
                    st = cust_data['st']
                
                time_in_sys = t_curr - arrival_t
                total_time_in_sys += time_in_sys
                
                if queue:
                    next_cust = queue.pop(0)
                    n -= 1
                    prev_n = n
                    busy_until = t_curr + next_cust['st']
                    add_event(busy_until, 'dep', {'start': t_curr, 'cust': next_cust})
                else:
                    n -= 1
                    prev_n = n
                    busy_until = None
        
        if win_len > 0:
            L_est = area_n / win_len
            W_est = total_time_in_sys / dep_count if dep_count > 0 else 0.0
            busy_frac_est = busy_periods_area / win_len
            p_wait_est = 0.0
            # Need to compute waiting probability properly
            # Let's recompute with a cleaner approach for p_wait
            # Actually let me redo the simulation more carefully
            pass
        
        # Redo simulation cleanly
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        queue = []
        busy_until = None
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        total_time_in_sys = 0.0
        area_n = 0.0
        last_event_t = 0.0
        prev_n = 0
        busy_periods_area = 0.0
        idle_periods_area = 0.0
        last_idle_start = 0.0
        customers_waiting_at_arrival = 0
        
        events = []
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        add_event(next_arr, 'arr', None)
        
        while events:
            events.sort(key=lambda x: x[0])
            t_curr, typ, data = events.pop(0)
            if t_curr > horizon:
                break
            dt = t_curr - last_event_t
            if last_event_t < horizon:
                overlap_start = max(last_event_t, win_start)
                overlap_end = min(t_curr, horizon)
                if overlap_end > overlap_start:
                    odt = overlap_end - overlap_start
                    area_n += prev_n * odt
                    if prev_n > 0:
                        busy_periods_area += odt
                    else:
                        idle_periods_area += odt
            last_event_t = t_curr
            
            if typ == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                was_waiting = False
                if n == 0 and busy_until is None:
                    n += 1
                    prev_n = n
                    busy_until = t_curr + st
                    add_event(busy_until, 'dep', {'start': t_curr, 'st': st, 'waited': False})
                else:
                    n += 1
                    prev_n = n
                    queue.append({'arrival': t_curr, 'st': st})
                    if len(queue) > 1:
                        was_waiting = True
                    if busy_until is None:
                        cust = queue.pop(0)
                        n -= 1
                        prev_n = n
                        busy_until = t_curr + cust['st']
                        add_event(busy_until, 'dep', {'start': t_curr, 'cust': cust, 'waited': False})
                if was_waiting:
                    wait_sum += 1
                next_arr = t_curr + rng.expovariate(lam)
                add_event(next_arr, 'arr', None)
            elif typ == 'dep':
                dep_count += 1
                cust_data = data
                if 'cust' in cust_data:
                    cust = cust_data['cust']
                    arrival_t = cust['arrival']
                    st = cust['st']
                else:
                    arrival_t = cust_data['start']
                    st = cust_data['st']
                time_in_sys = t_curr - arrival_t
                total_time_in_sys += time_in_sys
                if queue:
                    next_cust = queue.pop(0)
                    n -= 1
                    prev_n = n
                    busy_until = t_curr + next_cust['st']
                    add_event(busy_until, 'dep', {'start': t_curr, 'cust': next_cust, 'waited': False})
                else:
                    n -= 1
                    prev_n = n
                    busy_until = None
        
        if win_len > 0 and dep_count > 0:
            L_est = area_n / win_len
            W_est = total_time_in_sys / dep_count
            busy_frac_est = busy_periods_area / win_len
            p_wait_est = wait_sum / arr_count if arr_count > 0 else 0.0
            busy_util_est = busy_periods_area / win_len
            busy_occupied_est = 1.0 - (idle_periods_area / win_len) if win_len > 0 else 0.0
            lam_eff_est = dep_count / win_len if win_len > 0 else 0.0
            p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
            dep_rate_est = dep_count / win_len * 60.0 if win_len > 0 else 0.0
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arr_count)
            all_dep.append(dep_count)
            all_blk.append(blk_count)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occupied_est)
            all_lam_eff.append(lam_eff_est)
            all_p_loss.append(p_loss_est)
            all_dep_rate.append(dep_rate_est)
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            seed_list.append(seed)
    
    seeds_used = len(all_L)
    if seeds_used == 0:
        result = {"L": 0, "W": 0, "busy_frac": 0, "p_wait": 0, "runtime_units": "minute", "seed_list": [], "seeds_used": 0, "time_unit": "minute", "win": 0, "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0, "lam_eff": 0, "p_loss": 0, "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [], "per_seed_p_loss": [], "per_seed_p_wait": []}
    else:
        avg_L = sum(all_L) / seeds_used
        avg_W = sum(all_W) / seeds_used
        avg_busy_frac = sum(all_busy_frac) / seeds_used
        avg_p_wait = sum(all_p_wait) / seeds_used
        avg_arr = sum(all_arr) / seeds_used
        avg_dep = sum(all_dep) / seeds_used
        avg_blk = sum(all_blk) / seeds_used
        avg_busy_util = sum(all_busy_util) / seeds_used
        avg_busy_occupied = sum(all_busy_occupied) / seeds_used
        avg_lam_eff = sum(all_lam_eff) / seeds_used
        avg_p_loss = sum(all_p_loss) / seeds_used
        avg_dep_rate = sum(all_dep_rate) / seeds_used
        
        result = {
            "L": round(avg_L, 6),
            "W": round(avg_W, 6),
            "busy_frac": round(avg_busy_frac, 6),
            "p_wait": round(avg_p_wait, 6),
            "runtime_units": "minute",
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": "minute",
            "win": round(win_len, 6),
            "arr": round(avg_arr, 6),
            "blk": round(avg_blk, 6),
            "busy_util": round(avg_busy_util, 6),
            "dep": round(avg_dep, 6),
            "dep_rate": round(avg_dep_rate, 6),
            "lam_eff": round(avg_lam_eff, 6),
            "p_loss": round(avg_p_loss, 6),
            "per_seed_L": [round(x, 6) for x in per_seed_L],
            "per_seed_W": [round(x, 6) for x in per_seed_W],
            "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
            "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
            "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
        }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
