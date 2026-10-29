import json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0 / 60.0 # per minute
    mu_base = 1.0 / 12.0 # per minute
    c = 2
    
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': c += 1
    
    horizon_min = a.horizon * 60.0 if a.time_unit == 'hour' else a.horizon
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
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
    all_seed_L = []
    all_seed_W = []
    all_seed_busy_frac = []
    all_seed_p_loss = []
    all_seed_p_wait = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = [] # list of (arrival_time, service_duration)
        servers_free_at = [0.0] * c
        
        total_wait_service_time = 0.0
        count_completed_in_window = 0
        count_arrivals_in_window = 0
        count_departures_in_window = 0
        count_blocked_in_window = 0
        
        area_N = 0.0
        last_event_t = 0.0
        current_N = 0
        
        while True:
            # Determine next event time
            min_server_free = min(servers_free_at) if servers_free_at else float('inf')
            next_event = min(next_arr, min_server_free)
            
            if next_event > horizon_min:
                break
            
            dt = next_event - t
            if t >= warmup_end:
                area_N += current_N * dt
            
            t = next_event
            
            if abs(t - next_arr) < 1e-9:
                # Arrival
                svc_dur = rng.expovariate(mu_base)
                arr_info = (t, svc_dur)
                
                # Find free server
                free_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t + 1e-9:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    servers_free_at[free_idx] = t + svc_dur
                    start_time = t
                else:
                    queue.append(arr_info)
                    start_time = None # Will be set when dequeued
                
                if t >= warmup_end:
                    count_arrivals_in_window += 1
                
                current_N += 1
                next_arr = t + rng.expovariate(lam_base)
                
            else:
                # Departure from server
                free_idx = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    # Check if queue has someone waiting for this slot? 
                    # Actually, we need to know who was being served.
                    # This simple loop doesn't track which customer is at which server easily without more state.
                    # Let's refine the simulation logic slightly to be robust.
                    pass
                
                # Re-implementing core loop with better state tracking for clarity and correctness within constraints
                # Resetting variables for cleaner implementation inside the seed loop
                pass
        
        # Restarting the inner simulation logic properly for one seed
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        # Queue stores tuples: (arrival_time, service_duration)
        q = []
        # Servers store: (finish_time, arrival_time, service_duration) or just finish_time if we track separately
        # To calculate W correctly, we need to know when service started.
        # Let's keep servers as list of finish times. When a server finishes, we pop from queue if exists.
        srv_finish = [float('inf')] * c
        
        total_w_s = 0.0 # Sum of (departure - arrival) for completed customers in window
        n_comp = 0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        
        area_n = 0.0
        prev_t = 0.0
        cur_n = 0
        
        while True:
            # Next arrival time
            na = next_arr
            # Next departure time
            nd = min(srv_finish)
            
            ne = min(na, nd)
            if ne > horizon_min:
                break
            
            dt = ne - prev_t
            if prev_t >= warmup_end:
                area_n += cur_n * dt
            
            prev_t = ne
            t = ne
            
            if t >= na - 1e-9: # Arrival happens
                dur = rng.expovariate(mu_base)
                cust = (t, dur)
                
                # Check for free server
                free_i = -1
                for i in range(c):
                    if srv_finish[i] <= t + 1e-9:
                        free_i = i
                        break
                
                if free_i != -1:
                    srv_finish[free_i] = t + dur
                    # Customer starts immediately
                    # We don't add to queue, but we need to track their completion later.
                    # Since we only have finish times, how do we know who finished?
                    # We need to associate the customer with the server slot.
                    # Let's change srv_finish to store (finish_time, arrival_time, duration)
                    pass
                
                # Refining again: Store full info in server slots
                # srv_slots[i] = (finish_time, arrival_time, duration) or None if idle
                # But we initialized with inf. Let's use a list of dicts or tuples.
                # Simpler: Keep srv_finish as times, and maintain a separate structure?
                # No, let's just make srv_finish hold the tuple.
                
                # Resetting for final clean implementation
                break 

        # Final Clean Implementation for One Seed
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        # Server states: list of (finish_time, arrival_time, service_duration)
        # If idle, finish_time is infinity
        servers = [(float('inf'), None, None) for _ in range(c)]
        queue = [] # List of (arrival_time, service_duration)
        
        sum_w = 0.0
        cnt_w = 0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        
        area_n = 0.0
        last_t = 0.0
        n_now = 0
        
        while True:
            # Find next event
            min_srv_fin = min(s[0] for s in servers)
            next_evt = min(next_arrival, min_srv_fin)
            
            if next_evt > horizon_min:
                break
            
            dt = next_evt - last_t
            if last_t >= warmup_end:
                area_n += n_now * dt
            
            last_t = next_evt
            t = next_evt
            
            if t >= next_arrival - 1e-9:
                # Arrival
                dur = rng.expovariate(mu_base)
                new_cust = (t, dur)
                
                # Try to assign to server
                assigned = False
                for i in range(c):
                    if servers[i][0] <= t + 1e-9:
                        servers[i] = (t + dur, t, dur)
                        assigned = True
                        break
                
                if not assigned:
                    queue.append(new_cust)
                
                if t >= warmup_end:
                    cnt_arr += 1
                
                n_now += 1
                next_arrival = t + rng.expovariate(lam_base)
                
            else:
                # Departure
                # Find which server finished
                fin_idx = -1
                for i in range(c):
                    if abs(servers[i][0] - t) < 1e-9:
                        fin_idx = i
                        break
                
                if fin_idx != -1:
                    _, arr_t, dur = servers[fin_idx]
                    # Calculate wait+service time
                    w = t - arr_t
                    if arr_t >= warmup_end: # Only count if arrival was in window? Or if departure is in window?
                        # Standard practice: Count events that complete in the window.
                        # The prompt says "statistics accumulated in window after removing first 25%".
                        # Usually, we count departures in the window.
                        if t >= warmup_end:
                            sum_w += w
                            cnt_w += 1
                            cnt_dep += 1
                    
                    # Serve next from queue if any
                    if queue:
                        nxt = queue.pop(0)
                        servers[fin_idx] = (t + nxt[1], nxt[0], nxt[1])
                    else:
                        servers[fin_idx] = (float('inf'), None, None)
                    
                    n_now -= 1
        
        # Post-process for this seed
        win_len = horizon_min - warmup_end
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w / cnt_w if cnt_w > 0 else 0
        
        # Busy fraction E[min(N,c)]/c
        # We didn't integrate min(N,c). We integrated N.
        # Need to re-calculate or approximate. 
        # For M/M/c, busy frac is often approximated by utilization.
        # Let's compute it properly by integrating min(N,c) during the loop?
        # Too late in this draft. I will adjust the loop to integrate both N and min(N,c).
        
        # Adjusting loop above mentally:
        # area_n += n_now * dt
        # area_busy += min(n_now, c) * dt
        
        # Recalculating with correct integration
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        servers = [(float('inf'), None, None) for _ in range(c)]
        queue = []
        
        sum_w = 0.0
        cnt_w = 0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        
        area_n = 0.0
        area_busy = 0.0 # Integral of min(N, c)
        last_t = 0.0
        n_now = 0
        
        while True:
            min_srv_fin = min(s[0] for s in servers)
            next_evt = min(next_arrival, min_srv_fin)
            
            if next_evt > horizon_min:
                break
            
            dt = next_evt - last_t
            if last_t >= warmup_end:
                area_n += n_now * dt
                area_busy += min(n_now, c) * dt
            
            last_t = next_evt
            t = next_evt
            
            if t >= next_arrival - 1e-9:
                dur = rng.expovariate(mu_base)
                new_cust = (t, dur)
                
                assigned = False
                for i in range(c):
                    if servers[i][0] <= t + 1e-9:
                        servers[i] = (t + dur, t, dur)
                        assigned = True
                        break
                
                if not assigned:
                    queue.append(new_cust)
                
                if t >= warmup_end:
                    cnt_arr += 1
                
                n_now += 1
                next_arrival = t + rng.expovariate(lam_base)
                
            else:
                fin_idx = -1
                for i in range(c):
                    if abs(servers[i][0] - t) < 1e-9:
                        fin_idx = i
                        break
                
                if fin_idx != -1:
                    _, arr_t, dur = servers[fin_idx]
                    w = t - arr_t
                    if t >= warmup_end:
                        sum_w += w
                        cnt_w += 1
                        cnt_dep += 1
                    
                    if queue:
                        nxt = queue.pop(0)
                        servers[fin_idx] = (t + nxt[1], nxt[0], nxt[1])
                    else:
                        servers[fin_idx] = (float('inf'), None, None)
                    
                    n_now -= 1
        
        win_len = horizon_min - warmup_end
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w / cnt_w if cnt_w > 0 else 0
        busy_frac_est = (area_busy / win_len) / c if win_len > 0 else 0
        busy_util_est = busy_frac_est # Same definition per prompt
        occupied_prob = 1 - (1 - busy_util_est)**c # Approximation for P(N>0)? No, exact pi_0 for M/M/c is complex.
        # Prompt asks for busy_occupied = 1 - pi_0. In discrete sim, pi_0 is fraction of time N=0.
        # We didn't integrate indicator(N==0).
        # Let's assume busy_occupied is derived or we skip precise pi_0 if not integrated.
        # However, prompt requires it. I should have integrated area_occ where occ=1 if n>0 else 0.
        
        # Re-re-run with area_occ
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        servers = [(float('inf'), None, None) for _ in range(c)]
        queue = []
        
        sum_w = 0.0
        cnt_w = 0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        last_t = 0.0
        n_now = 0
        
        while True:
            min_srv_fin = min(s[0] for s in servers)
            next_evt = min(next_arrival, min_srv_fin)
            
            if next_evt > horizon_min:
                break
            
            dt = next_evt - last_t
            if last_t >= warmup_end:
                area_n += n_now * dt
                area_busy += min(n_now, c) * dt
                area_occ += (1 if n_now > 0 else 0) * dt
            
            last_t = next_evt
            t = next_evt
            
            if t >= next_arrival - 1e-9:
                dur = rng.expovariate(mu_base)
                new_cust = (t, dur)
                
                assigned = False
                for i in range(c):
                    if servers[i][0] <= t + 1e-9:
                        servers[i] = (t + dur, t, dur)
                        assigned = True
                        break
                
                if not assigned:
                    queue.append(new_cust)
                
                if t >= warmup_end:
                    cnt_arr += 1
                
                n_now += 1
                next_arrival = t + rng.expovariate(lam_base)
                
            else:
                fin_idx = -1
                for i in range(c):
                    if abs(servers[i][0] - t) < 1e-9:
                        fin_idx = i
                        break
                
                if fin_idx != -1:
                    _, arr_t, dur = servers[fin_idx]
                    w = t - arr_t
                    if t >= warmup_end:
                        sum_w += w
                        cnt_w += 1
                        cnt_dep += 1
                    
                    if queue:
                        nxt = queue.pop(0)
                        servers[fin_idx] = (t + nxt[1], nxt[0], nxt[1])
                    else:
                        servers[fin_idx] = (float('inf'), None, None)
                    
                    n_now -= 1
        
        win_len = horizon_min - warmup_end
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w / cnt_w if cnt_w > 0 else 0
        bf_est = (area_busy / win_len) / c if win_len > 0 else 0
        bo_est = area_occ / win_len if win_len > 0 else 0
        
        # p_wait: Probability an arrival sees queue non-empty (or all servers busy)
        # We counted arrivals. We need to count how many arrived when no server was free.
        # In the loop, if not assigned, they went to queue.
        # So p_wait = (count of arrivals that were queued) / (total arrivals in window)
        # We didn't track that specifically. 
        # Let's infer: Arrivals that found all servers busy.
        # In the arrival block: if not assigned -> queued.
        # I need a counter for that.
        
        # Final Pass with p_wait counter
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        servers = [(float('inf'), None, None) for _ in range(c)]
        queue = []
        
        sum_w = 0.0
        cnt_w = 0
        cnt_arr = 0
        cnt_dep = 0
        cnt_queued_arr = 0 # Arrivals that had to wait
        
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        last_t = 0.0
        n_now = 0
        
        while True:
            min_srv_fin = min(s[0] for s in servers)
            next_evt = min(next_arrival, min_srv_fin)
            
            if next_evt > horizon_min:
                break
            
            dt = next_evt - last_t
            if last_t >= warmup_end:
                area_n += n_now * dt
                area_busy += min(n_now, c) * dt
                area_occ += (1 if n_now > 0 else 0) * dt
            
            last_t = next_evt
            t = next_evt
            
            if t >= next_arrival - 1e-9:
                dur = rng.expovariate(mu_base)
                new_cust = (t, dur)
                
                assigned = False
                for i in range(c):
                    if servers[i][0] <= t + 1e-9:
                        servers[i] = (t + dur, t, dur)
                        assigned = True
                        break
                
                if not assigned:
                    queue.append(new_cust)
                    if t >= warmup_end:
                        cnt_queued_arr += 1
                
                if t >= warmup_end:
                    cnt_arr += 1
                
                n_now += 1
                next_arrival = t + rng.expovariate(lam_base)
                
            else:
                fin_idx = -1
                for i in range(c):
                    if abs(servers[i][0] - t) < 1e-9:
                        fin_idx = i
                        break
                
                if fin_idx != -1:
                    _, arr_t, dur = servers[fin_idx]
                    w = t - arr_t
                    if t >= warmup_end:
                        sum_w += w
                        cnt_w += 1
                        cnt_dep += 1
                    
                    if queue:
                        nxt = queue.pop(0)
                        servers[fin_idx] = (t + nxt[1], nxt[0], nxt[1])
                    else:
                        servers[fin_idx] = (float('inf'), None, None)
                    
                    n_now -= 1
        
        win_len = horizon_min - warmup_end
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w / cnt_w if cnt_w > 0 else 0
        bf_est = (area_busy / win_len) / c if win_len > 0 else 0
        bo_est = area_occ / win_len if win_len > 0 else 0
        pw_est = cnt_queued_arr / cnt_arr if cnt_arr > 0 else 0
        
        dep_rate_est = (cnt_dep / win_len) * 60.0 if win_len > 0 else 0 # Per hour
        lam_eff_est = (cnt_arr / win_len) * 60.0 if win_len > 0 else 0 # Per hour
        
        all_seed_L.append(L_est)
        all_seed_W.append(W_est)
        all_seed_busy_frac.append(bf_est)
        all_seed_p_wait.append(pw_est)
        all_seed_p_loss.append(0.0) # No loss in infinite queue model
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(bf_est)
        all_p_wait.append(pw_est)
        all_arr.append(cnt_arr)
        all_dep.append(cnt_dep)
        all_blk.append(0)
        all_busy_util.append(bf_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(0.0)

    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_bf = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0
    avg_pw = sum(all_p_wait)/len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr)/len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep)/len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk)/len(all_blk) if all_blk else 0
    avg_bu = sum(all_busy_util)/len(all_busy_util) if all_busy_util else 0
    avg_dr = sum(all_dep_rate)/len(all_dep_rate) if all_dep_rate else 0
    avg_le = sum(all_lam_eff)/len(all_lam_eff) if all_lam_eff else 0
    avg_pl = sum(all_p_loss)/len(all_p_loss) if all_p_loss else 0
    
    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": "minute",
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "minute",
        "win": round(horizon_min * 0.75, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bu, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dr, 4),
        "lam_eff": round(avg_le, 4),
        "p_loss": round(avg_pl, 4),
        "per_seed_L": [round(x, 4) for x in all_seed_L],
        "per_seed_W": [round(x, 4) for x in all_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
