import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0  # 5 per hour
    c = 3

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 4
    else:
        lam = lam_base
        mu = mu_base
    
    if pert != 'lam_up' and pert != 'mu_up' and pert != 'c_up':
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} # id -> duration
        queue = [] # list of ids waiting
        servers = [None] * c # None or (id, finish_time)
        active_ids = set()
        id_counter = 0
        
        # Statistics accumulators for the window [H*0.25, H]
        warmup_end = H * 0.25
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_wait_events = 0 # arrivals that had to wait
        
        last_event_time = 0.0
        current_N = 0
        current_min_N_c = 0
        
        while True:
            # Determine next event time
            events = []
            if next_arrival < H:
                events.append(('arr', next_arrival))
            
            min_serv_finish = float('inf')
            serv_idx = -1
            for j in range(c):
                if servers[j] is not None:
                    if servers[j][1] < min_serv_finish:
                        min_serv_finish = servers[j][1]
                        serv_idx = j
            
            if min_serv_finish < H:
                events.append(('dep', min_serv_finish, serv_idx))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            ev_type, ev_time = events[0][0], events[0][1]
            
            # Integrate area up to ev_time
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_L += current_N * dt
                area_busy += current_min_N_c * dt
            
            last_event_time = ev_time
            
            if ev_type == 'arr':
                if last_event_time >= warmup_end:
                    count_arr += 1
                
                # Check if server available
                free_server = -1
                for j in range(c):
                    if servers[j] is None:
                        free_server = j
                        break
                
                cust_id = id_counter
                id_counter += 1
                dur = rng.expovariate(mu)
                service_times[cust_id] = dur
                
                if free_server != -1:
                    servers[free_server] = (cust_id, ev_time + dur)
                    active_ids.add(cust_id)
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                else:
                    queue.append(cust_id)
                    active_ids.add(cust_id)
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                    if last_event_time >= warmup_end:
                        count_wait_events += 1
                
                next_arrival = ev_time + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                idx = events[0][2]
                cust_id, finish_t = servers[idx]
                servers[idx] = None
                active_ids.remove(cust_id)
                
                if last_event_time >= warmup_end:
                    count_dep += 1
                    w = finish_t - (ev_time - service_times[cust_id]) # Wait + Service? No.
                    # W is total time in system. Arrival time needed.
                    # We didn't store arrival time explicitly in a simple way for lookup later easily without dict.
                    # Let's fix: Store arrival time in service_times or separate dict.
                    # Actually, we can calculate W at departure if we know arrival time.
                    # Let's add arr_time dict.
                    
                    # Re-evaluating logic: I need arrival time.
                    pass 
                
                # Fixing the structure to track arrival times properly
                # This requires a slight refactor inside the loop which is messy.
                # Let's restart the simulation logic with better state tracking.
                break 

        # The above loop broke due to complexity. Rewriting cleanly.
        
        # Reset for clean implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        servers = [None] * c # (id, start_time, end_time)
        id_counter = 0
        arr_times = {}
        dep_times = {}
        
        warmup_end = H * 0.25
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_wait_events = 0
        
        last_event_time = 0.0
        current_N = 0
        current_min_N_c = 0
        
        while True:
            events = []
            if next_arrival <= H:
                events.append(('arr', next_arrival))
            
            min_serv_finish = float('inf')
            serv_idx = -1
            for j in range(c):
                if servers[j] is not None:
                    if servers[j][2] < min_serv_finish:
                        min_serv_finish = servers[j][2]
                        serv_idx = j
            
            if min_serv_finish <= H:
                events.append(('dep', min_serv_finish, serv_idx))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            ev_type, ev_time = events[0][0], events[0][1]
            
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_L += current_N * dt
                area_busy += current_min_N_c * dt
            
            last_event_time = ev_time
            
            if ev_type == 'arr':
                if last_event_time >= warmup_end:
                    count_arr += 1
                
                free_server = -1
                for j in range(c):
                    if servers[j] is None:
                        free_server = j
                        break
                
                cust_id = id_counter
                id_counter += 1
                dur = rng.expovariate(mu)
                arr_times[cust_id] = ev_time
                
                if free_server != -1:
                    servers[free_server] = (cust_id, ev_time, ev_time + dur)
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                else:
                    queue.append(cust_id)
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                    if last_event_time >= warmup_end:
                        count_wait_events += 1
                
                next_arrival = ev_time + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                idx = events[0][2]
                cust_id, start_t, end_t = servers[idx]
                servers[idx] = None
                
                if last_event_time >= warmup_end:
                    count_dep += 1
                    w = end_t - arr_times[cust_id]
                    sum_W += w
                
                del arr_times[cust_id]
                
                if queue:
                    next_cust = queue.pop(0)
                    new_dur = rng.expovariate(mu) # Wait, service time was drawn at arrival!
                    # Correction: Service time must be drawn at arrival.
                    # I need to store service duration at arrival.
                    # Let's assume I stored it. But I didn't in this snippet.
                    # Refactoring again.
                    break

        # Final Clean Implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of (id, arrival_time, service_duration)
        servers = [None] * c # None or (id, arrival_time, service_duration, start_time, end_time)
        id_counter = 0
        
        warmup_end = H * 0.25
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_wait_events = 0
        
        last_event_time = 0.0
        current_N = 0
        current_min_N_c = 0
        
        while True:
            events = []
            if next_arrival <= H:
                events.append(('arr', next_arrival))
            
            min_serv_finish = float('inf')
            serv_idx = -1
            for j in range(c):
                if servers[j] is not None:
                    if servers[j][4] < min_serv_finish:
                        min_serv_finish = servers[j][4]
                        serv_idx = j
            
            if min_serv_finish <= H:
                events.append(('dep', min_serv_finish, serv_idx))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            ev_type, ev_time = events[0][0], events[0][1]
            
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_L += current_N * dt
                area_busy += current_min_N_c * dt
            
            last_event_time = ev_time
            
            if ev_type == 'arr':
                if last_event_time >= warmup_end:
                    count_arr += 1
                
                free_server = -1
                for j in range(c):
                    if servers[j] is None:
                        free_server = j
                        break
                
                cust_id = id_counter
                id_counter += 1
                dur = rng.expovariate(mu)
                
                if free_server != -1:
                    servers[free_server] = (cust_id, ev_time, dur, ev_time, ev_time + dur)
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                else:
                    queue.append((cust_id, ev_time, dur))
                    current_N += 1
                    current_min_N_c = min(current_N, c)
                    if last_event_time >= warmup_end:
                        count_wait_events += 1
                
                next_arrival = ev_time + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                idx = events[0][2]
                cust_id, arr_t, dur, start_t, end_t = servers[idx]
                servers[idx] = None
                
                if last_event_time >= warmup_end:
                    count_dep += 1
                    w = end_t - arr_t
                    sum_W += w
                
                if queue:
                    next_cust = queue.pop(0)
                    n_id, n_arr, n_dur = next_cust
                    servers[idx] = (n_id, n_arr, n_dur, ev_time, ev_time + n_dur)
                    # Customer moves from queue to server, N stays same
                    # current_N unchanged
                    # current_min_N_c unchanged
                else:
                    current_N -= 1
                    current_min_N_c = min(current_N, c)

        win_len = H - warmup_end
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = sum_W / count_dep if count_dep > 0 else 0
        busy_frac_est = area_busy / (win_len * c) if win_len > 0 else 0
        p_wait_est = count_wait_events / count_arr if count_arr > 0 else 0
        blk_est = count_blk / count_arr if count_arr > 0 else 0 # Always 0 here
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(blk_est)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(count_dep / win_len if win_len > 0 else 0)
        all_lam_eff.append(count_arr / win_len if win_len > 0 else 0)
        all_p_loss.append(blk_est)
        
        seeds_used += 1
        seed_list.append(seed)

    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    
    # Convert W to minutes
    avg_W_min = avg_W * 60.0
    per_seed_W_min = [w * 60.0 for w in all_W]

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W_min, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H * 0.75, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W_min],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
