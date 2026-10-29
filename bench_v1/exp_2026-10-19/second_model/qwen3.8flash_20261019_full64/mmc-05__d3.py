import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 10.0
    mu_base = 10.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
        mu = mu_base
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    horizon_hours = H if time_unit == "hour" else (H/60.0 if time_unit=="minute" else H/3600.0)
    win_hours = horizon_hours * 0.75
    warmup_end = horizon_hours * 0.25
    
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
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] 
        total_time_in_system = 0.0
        num_completed = 0
        num_arrivals = 0
        num_blocked = 0
        
        area_L = 0.0
        last_event_t = 0.0
        current_N = 0
        
        events = []
        if next_arr <= horizon_hours:
            events.append(('arr', next_arr))
            
        while events:
            events.sort(key=lambda x: x[1])
            etype, etime = events.pop(0)
            
            dt = etime - last_event_t
            if last_event_t >= warmup_end and etime > warmup_end:
                pass 
            if last_event_t < warmup_end and etime > warmup_end:
                dt_warm = warmup_end - last_event_t
                dt_stat = etime - warmup_end
                area_L += current_N * dt_stat
            elif last_event_t >= warmup_end:
                area_L += current_N * dt
            
            last_event_t = etime
            
            if etype == 'arr':
                if etime > horizon_hours: break
                
                service_time = rng.expovariate(mu)
                
                min_free_idx = -1
                min_free_time = float('inf')
                for k in range(c):
                    if servers_free_at[k] < min_free_time:
                        min_free_time = servers_free_at[k]
                        min_free_idx = k
                        
                start_service_time = max(etime, min_free_time)
                end_service_time = start_service_time + service_time
                
                wait_time = start_service_time - etime
                system_time = end_service_time - etime
                
                if etime >= warmup_end:
                    total_time_in_system += system_time
                    num_completed += 1
                    if wait_time > 0:
                        num_blocked += 1 # Using blocked as proxy for waiting? No, p_wait is prob of waiting upon arrival.
                        # Let's track arrivals that waited separately for p_wait calculation in window.
                
                # Update state
                servers_free_at[min_free_idx] = end_service_time
                current_N += 1
                
                # Schedule departure
                if end_service_time <= horizon_hours:
                    events.append(('dep', end_service_time))
                    
                # Schedule next arrival
                next_arr_time = etime + rng.expovariate(lam)
                if next_arr_time <= horizon_hours:
                    events.append(('arr', next_arr_time))
                    
                # Count arrivals in window for stats
                if etime >= warmup_end:
                    num_arrivals_window = getattr(main, '_num_arr_win', 0)
                    # This approach is messy. Let's restart logic with cleaner accumulation.
                    pass

        # Re-implementing cleanly below to avoid confusion
        pass

    # Clean implementation
    results = []
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        server_next_free = [0.0] * c
        active_customers = [] # list of (arrival_time, service_duration, start_time, end_time)
        
        # Statistics accumulators for the window [warmup_end, horizon]
        stat_area_L = 0.0
        stat_total_system_time = 0.0
        stat_num_completions = 0
        stat_num_arrivals = 0
        stat_num_waiting_arrivals = 0 # Arrivals who had to wait (start > arrival)
        stat_num_lost = 0 # Not applicable here as no loss system, but keeping key
        
        last_update_time = 0.0
        current_count = 0
        
        # We need to simulate until horizon.
        # Events: Arrival, Departure
        
        heap = []
        if next_arrival <= horizon_hours:
            heapq.heappush(heap, (next_arrival, 'A'))
            
        # Need import heapq
        import heapq
        
        while heap:
            time_now, event_type = heapq.heappop(heap)
            
            if time_now > horizon_hours:
                break
                
            # Update Area L before changing state
            dt = time_now - last_update_time
            if last_update_time < warmup_end and time_now > warmup_end:
                # Split interval
                dt_pre = warmup_end - last_update_time
                dt_post = time_now - warmup_end
                stat_area_L += current_count * dt_post
            elif last_update_time >= warmup_end:
                stat_area_L += current_count * dt
            
            last_update_time = time_now
            
            if event_type == 'A':
                # Generate service time now
                svc_dur = rng.expovariate(mu)
                
                # Find earliest available server
                min_free_t = float('inf')
                min_idx = -1
                for k in range(c):
                    if server_next_free[k] < min_free_t:
                        min_free_t = server_next_free[k]
                        min_idx = k
                
                start_t = max(time_now, min_free_t)
                end_t = start_t + svc_dur
                
                # Check if this customer completes within horizon? 
                # For W, we usually count completed customers in window.
                # If end_t > horizon, they are still in system at horizon.
                # But standard DES often truncates or handles partials.
                # Given "average waiting+processing time", it implies completed ones.
                # However, if we only count completed, we might bias.
                # Let's assume we count completions that happen <= horizon.
                
                # State update
                current_count += 1
                server_next_free[min_idx] = end_t
                
                # Record for stats if arrival was in window
                if time_now >= warmup_end:
                    stat_num_arrivals += 1
                    if start_t > time_now:
                        stat_num_waiting_arrivals += 1
                    
                    # If completion happens later, we add to total time then.
                    # We need to store info to retrieve at departure.
                    # Since we don't have a class, we can push a departure event with data.
                    # But heap elements must be comparable. Tuple (time, type, data).
                    # Data needs to be unique or handled carefully.
                    # Let's use a counter ID.
                    cust_id = len(active_customers) # Not really used, just for uniqueness if needed
                    heapq.heappush(heap, (end_t, 'D', time_now, svc_dur, start_t))
                
                # Next arrival
                next_arrival = time_now + rng.expovariate(lam)
                if next_arrival <= horizon_hours:
                    heapq.heappush(heap, (next_arrival, 'A'))
                    
            elif event_type == 'D':
                _, _, arr_t, svc_dur, start_t = event_type_data # Wait, unpacking issue
                # Correction: The tuple pushed was (end_t, 'D', time_now, svc_dur, start_t)
                # So when popped:
                # time_now is end_t
                # event_type is 'D'
                # rest are arr_t, svc_dur, start_t
                
                # Actually, let's restructure the push/pop to be safe.
                pass

        # Restarting clean loop structure inside the seed loop
        pass

    # Final Clean Code Generation
    import heapq
    
    def run_sim(seed, lam, mu, c, horizon_hours, warmup_end):
        rng = random.Random(seed)
        heap = []
        next_arr = rng.expovariate(lam)
        if next_arr <= horizon_hours:
            heapq.heappush(heap, (next_arr, 'A', None, None, None))
            
        server_free = [0.0] * c
        current_n = 0
        last_t = 0.0
        
        area_L = 0.0
        sum_sys_time = 0.0
        n_compl = 0
        n_arr_win = 0
        n_wait_arr = 0
        
        while heap:
            t, typ, arr_t, svc_d, st_t = heapq.heappop(heap)
            
            if t > horizon_hours:
                break
                
            dt = t - last_t
            if last_t < warmup_end and t > warmup_end:
                area_L += current_n * (t - warmup_end)
            elif last_t >= warmup_end:
                area_L += current_n * dt
            last_t = t
            
            if typ == 'A':
                svc_dur = rng.expovariate(mu)
                min_idx = 0
                min_val = server_free[0]
                for k in range(1, c):
                    if server_free[k] < min_val:
                        min_val = server_free[k]
                        min_idx = k
                
                start_time = max(t, min_val)
                end_time = start_time + svc_dur
                
                current_n += 1
                server_free[min_idx] = end_time
                
                if t >= warmup_end:
                    n_arr_win += 1
                    if start_time > t:
                        n_wait_arr += 1
                
                heapq.heappush(heap, (end_time, 'D', t, svc_dur, start_time))
                
                na = t + rng.expovariate(lam)
                if na <= horizon_hours:
                    heapq.heappush(heap, (na, 'A', None, None, None))
                    
            elif typ == 'D':
                current_n -= 1
                if arr_t >= warmup_end:
                    sys_time = t - arr_t
                    sum_sys_time += sys_time
                    n_compl += 1
        
        return area_L, sum_sys_time, n_compl, n_arr_win, n_wait_arr

    seeds_used = 0
    tot_area_L = 0.0
    tot_sum_sys = 0.0
    tot_n_compl = 0
    tot_n_arr = 0
    tot_n_wait = 0
    
    ps_L = []
    ps_W = []
    ps_bf = []
    ps_pl = []
    ps_pw = []
    
    for i in range(N_seeds):
        s = S_start + i
        aL, sS, nc, na, nw = run_sim(s, lam, mu, c, horizon_hours, warmup_end)
        
        win_len = horizon_hours - warmup_end
        if win_len <= 0: continue
        
        L_est = aL / win_len
        W_est = sS / nc if nc > 0 else 0.0
        pw_est = nw / na if na > 0 else 0.0
        
        # busy_frac definition: E[min(N,c)]/c
        # We didn't track min(N,c) area directly. 
        # Approximation: In M/M/c, utilization rho = lam/mu. 
        # But we need empirical. 
        # Let's modify run_sim to track area_minNc.
        pass

    # Refactor run_sim to include area_minNc
    def run_sim_full(seed, lam, mu, c, horizon_hours, warmup_end):
        rng = random.Random(seed)
        heap = []
        next_arr = rng.expovariate(lam)
        if next_arr <= horizon_hours:
            heapq.heappush(heap, (next_arr, 'A', None, None, None))
            
        server_free = [0.0] * c
        current_n = 0
        last_t = 0.0
        
        area_L = 0.0
        area_minNc = 0.0
        sum_sys_time = 0.0
        n_compl = 0
        n_arr_win = 0
        n_wait_arr = 0
        
        while heap:
            t, typ, arr_t, svc_d, st_t = heapq.heappop(heap)
            
            if t > horizon_hours:
                break
                
            dt = t - last_t
            if last_t < warmup_end and t > warmup_end:
                eff_dt = t - warmup_end
                area_L += current_n * eff_dt
                area_minNc += min(current_n, c) * eff_dt
            elif last_t >= warmup_end:
                area_L += current_n * dt
                area_minNc += min(current_n, c) * dt
            last_t = t
            
            if typ == 'A':
                svc_dur = rng.expovariate(mu)
                min_idx = 0
                min_val = server_free[0]
                for k in range(1, c):
                    if server_free[k] < min_val:
                        min_val = server_free[k]
                        min_idx = k
                
                start_time = max(t, min_val)
                end_time = start_time + svc_dur
                
                current_n += 1
                server_free[min_idx] = end_time
                
                if t >= warmup_end:
                    n_arr_win += 1
                    if start_time > t:
                        n_wait_arr += 1
                
                heapq.heappush(heap, (end_time, 'D', t, svc_dur, start_time))
                
                na = t + rng.expovariate(lam)
                if na <= horizon_hours:
                    heapq.heappush(heap, (na, 'A', None, None, None))
                    
            elif typ == 'D':
                current_n -= 1
                if arr_t >= warmup_end:
                    sys_time = t - arr_t
                    sum_sys_time += sys_time
                    n_compl += 1
        
        return area_L, area_minNc, sum_sys_time, n_compl, n_arr_win, n_wait_arr

    res_L = []
    res_W = []
    res_bf = []
    res_pw = []
    res_na = []
    res_nc = []
    res_nw = []
    res_amn = []
    
    for i in range(N_seeds):
        s = S_start + i
        aL, aM, sS, nc, na, nw = run_sim_full(s, lam, mu, c, horizon_hours, warmup_end)
        res_L.append(aL)
        res_amn.append(aM)
        res_W.append(sS)
        res_nc.append(nc)
        res_na.append(na)
        res_nw.append(nw)
        
        win_len = horizon_hours - warmup_end
        if win_len > 0:
            l_est = aL / win_len
            w_est = sS / nc if nc > 0 else 0.0
            bf_est = aM / (win_len * c)
            pw_est = nw / na if na > 0 else 0.0
            
            ps_L.append(l_est)
            ps_W.append(w_est)
            ps_bf.append(bf_est)
            ps_pw.append(pw_est)
            ps_pl.append(0.0) # No loss
            
    seeds_used = len(ps_L)
    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(ps_L) / seeds_used
    avg_W = sum(ps_W) / seeds_used
    avg_bf = sum(ps_bf) / seeds_used
    avg_pw = sum(ps_pw) / seeds_used
    
    total_na = sum(res_na)
    total_nc = sum(res_nc)
    total_nw = sum(res_nw)
    total_aL = sum(res_L)
    total_aM = sum(res_amn)
    total_sS = sum(res_W)
    
    win_len_avg = horizon_hours - warmup_end
    
    arr_per_seed = total_na / seeds_used
    dep_per_seed = total_nc / seeds_used
    blk_per_seed =
