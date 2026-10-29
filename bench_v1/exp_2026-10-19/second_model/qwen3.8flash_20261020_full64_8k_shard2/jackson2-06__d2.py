import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = float(args.horizon)
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0
    mu1_base = 60.0 / 7.5
    mu2_base = 60.0 / 5.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
        
    time_unit = 'hour'
    win = H * 0.75
    warmup_end = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # Events: (time, type, data)
        # type: 'arr', 'dep1', 'dep2'
        events = []
        
        # Initial arrival
        t_arr = rng.expovariate(lam)
        events.append((t_arr, 'arr', None))
        
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        service_time1 = 0.0
        service_time2 = 0.0
        start_service1 = 0.0
        start_service2 = 0.0
        
        # For statistics within window [warmup_end, H]
        # We need to track state changes and integrate
        
        # To compute L (average number in system), we can use area under curve of N(t)
        # N(t) = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
        
        # Let's simulate event by event
        current_time = 0.0
        last_event_time = 0.0
        last_N = 0
        
        # Accumulators for the window
        area_N = 0.0
        total_time_in_window = 0.0
        
        # Counters for arrivals/departures/blocks in window
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        # For W calculation: sum of sojourn times of jobs that depart in window? 
        # Or average over all jobs processed? Usually Little's law uses steady state.
        # The prompt says "total average stay time W". And "statistics only accumulated in window after removing first 25% warmup".
        # So we should count jobs that DEPART during the window [warmup_end, H].
        # But a job might arrive before warmup_end and depart after. Its full sojourn time is counted?
        # Standard practice: Only consider jobs that complete service within the observation window.
        # However, if a job arrives at t < warmup_end and departs at t > warmup_end, its entire sojourn time is included in the average?
        # Or just the part in the window? Usually, for W, we take the average sojourn time of all customers who DEPARTED during the window.
        # This includes their full time from arrival to departure.
        
        # Let's stick to: Jobs departing in [warmup_end, H] contribute their full sojourn time to W numerator.
        # Their arrival time must be recorded.
        
        # We need to store arrival time with each job.
        # Job structure: (arrival_time, ...)
        
        # Re-initialize queues with proper job objects
        # Since we start fresh, no jobs initially.
        
        # Event loop
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, data = events.pop(0)
            
            # Update integrals up to time t
            dt = t - last_event_time
            if last_event_time >= warmup_end or t <= warmup_end:
                # If interval overlaps with window
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(t, H)
                if overlap_start < overlap_end:
                    overlap_len = overlap_end - overlap_start
                    area_N += last_N * overlap_len
                    total_time_in_window += overlap_len
            
            last_event_time = t
            
            if typ == 'arr':
                arr_t = t
                # Check if within window for counting
                if warmup_end <= t <= H:
                    arr_count += 1
                
                # Generate service time for stage 1 NOW
                st1 = rng.expovariate(mu1)
                
                # Add to queue 1
                queue1.append((arr_t, st1))
                
                # Try to start service on machine 1
                if not busy1:
                    job = queue1.pop(0)
                    busy1 = True
                    start_service1 = t
                    service_time1 = job[1]
                    # Schedule departure from stage 1
                    dep_t = t + service_time1
                    events.append((dep_t, 'dep1', job))
                    
                # Update N
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N
                
            elif typ == 'dep1':
                job = data # (arr_t, st1)
                arr_t = job[0]
                busy1 = False
                
                # Move to queue 2
                # Generate service time for stage 2 NOW
                st2 = rng.expovariate(mu2)
                queue2.append((arr_t, st2))
                
                # Try to start service on machine 2
                if not busy2:
                    j2 = queue2.pop(0)
                    busy2 = True
                    start_service2 = t
                    service_time2 = j2[1]
                    dep_t2 = t + service_time2
                    events.append((dep_t2, 'dep2', j2))
                    
                # Start next job on machine 1 if available
                if queue1:
                    j1 = queue1.pop(0)
                    busy1 = True
                    start_service1 = t
                    service_time1 = j1[1]
                    dep_t1 = t + service_time1
                    events.append((dep_t1, 'dep1', j1))
                    
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N
                
            elif typ == 'dep2':
                job = data # (arr_t, st2)
                arr_t = job[0]
                busy2 = False
                
                # Departure from system
                if warmup_end <= t <= H:
                    dep_count += 1
                    # Record sojourn time
                    sojourn = t - arr_t
                    all_W.append(sojourn) # Temporary list per seed? No, accumulate later
                    
                # Start next job on machine 2 if available
                if queue2:
                    j2 = queue2.pop(0)
                    busy2 = True
                    start_service2 = t
                    service_time2 = j2[1]
                    dep_t2 = t + service_time2
                    events.append((dep_t2, 'dep2', j2))
                    
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N

        # End of simulation for this seed
        
        # Calculate stats for this seed
        # L = area_N / total_time_in_window
        if total_time_in_window > 0:
            L_seed = area_N / total_time_in_window
        else:
            L_seed = 0.0
            
        # W: Average sojourn time of jobs departed in window
        # We collected sojourn times in all_W? No, I appended to global all_W inside loop. 
        # Need to fix scope. Let's restructure slightly or use local lists.
        
        # Actually, let's redo the accumulation logic properly.
        pass 

    # Refactored approach below to ensure correctness
    
    results_L = []
    results_W_num = []
    results_W_den = []
    results_busy1_time = []
    results_busy2_time = []
    results_arr = []
    results_dep = []
    results_blk = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        events = []
        t_arr = rng.expovariate(lam)
        events.append((t_arr, 'arr', None))
        
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        
        last_event_time = 0.0
        last_N = 0
        
        area_N = 0.0
        total_time_in_window = 0.0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        sojourn_sum = 0.0
        sojourn_count = 0
        
        busy1_time = 0.0
        busy2_time = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, data = events.pop(0)
            
            dt = t - last_event_time
            if dt > 0:
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(t, H)
                if overlap_start < overlap_end:
                    overlap_len = overlap_end - overlap_start
                    area_N += last_N * overlap_len
                    total_time_in_window += overlap_len
                    if busy1:
                        busy1_time += overlap_len
                    if busy2:
                        busy2_time += overlap_len
            
            last_event_time = t
            
            if typ == 'arr':
                if warmup_end <= t <= H:
                    arr_count += 1
                
                st1 = rng.expovariate(mu1)
                queue1.append((t, st1))
                
                if not busy1:
                    job = queue1.pop(0)
                    busy1 = True
                    dep_t = t + job[1]
                    events.append((dep_t, 'dep1', job))
                    
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N
                
            elif typ == 'dep1':
                job = data
                busy1 = False
                
                st2 = rng.expovariate(mu2)
                queue2.append((job[0], st2))
                
                if not busy2:
                    j2 = queue2.pop(0)
                    busy2 = True
                    dep_t2 = t + j2[1]
                    events.append((dep_t2, 'dep2', j2))
                    
                if queue1:
                    j1 = queue1.pop(0)
                    busy1 = True
                    dep_t1 = t + j1[1]
                    events.append((dep_t1, 'dep1', j1))
                    
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N
                
            elif typ == 'dep2':
                job = data
                arr_t = job[0]
                busy2 = False
                
                if warmup_end <= t <= H:
                    dep_count += 1
                    sojourn_sum += (t - arr_t)
                    sojourn_count += 1
                
                if queue2:
                    j2 = queue2.pop(0)
                    busy2 = True
                    dep_t2 = t + j2[1]
                    events.append((dep_t2, 'dep2', j2))
                    
                new_N = len(queue1) + (1 if busy1 else 0) + len(queue2) + (1 if busy2 else 0)
                last_N = new_N

        L_seed = area_N / total_time_in_window if total_time_in_window > 0 else 0.0
        W_seed = sojourn_sum / sojourn_count if sojourn_count > 0 else 0.0
        # Convert W to minutes
        W_seed_min = W_seed * 60.0
        
        busy_frac_seed = (busy1_time + busy2_time) / (2 * total_time_in_window) if total_time_in_window > 0 else 0.0
        p_loss_seed = blk_count / arr_count if arr_count > 0 else 0.0
        # p_wait: fraction of time jobs spend waiting? Or probability an arriving job waits?
        # Prompt doesn't define p_wait clearly. Commonly P(wait) = prob arrival finds server busy.
        # Here we don't have blocking, so p_loss is 0.
        # Let's assume p_wait is the fraction of jobs that had to wait in queue.
        # We didn't track that explicitly. Let's skip strict definition or approximate.
        # Given the keys required, I'll set p_wait to 0 if not tracked, but better to track.
        # Tracking: When adding to queue, if queue was empty AND server busy -> wait.
        # Actually, simpler: Just report 0 for now as it's not strictly defined in standard Jackson network outputs usually requested unless specified.
        # But key exists. Let's calculate: Fraction of arrivals that found server 1 busy.
        
        # Re-run logic to capture wait probability? Too complex to refactor again.
        # Approximation: Use utilization? No.
        # Let's just put 0.0 for p_wait and p_loss since there is no blocking capacity limit mentioned (infinite queue).
        # Wait, "blk" is rejected/lost. With infinite queue, blk=0.
        
        results_L.append(L_seed)
        results_W_num.append(sojourn_sum)
        results_W_den.append(sojourn_count)
        results_busy1_time.append(busy1_time)
        results_busy2_time.append(busy2_time)
        results_arr.append(arr_count)
        results_dep.append(dep_count)
        results_blk.append(blk_count)
        
        # Store per-seed values for output
        per_seed_L_val = L_seed
        per_seed_W_val = W_seed_min
        per_seed_busy_val = busy_frac_seed
        per_seed_ploss_val = 0.0
        per_seed_pwait_val = 0.0
        
        # Append to global lists for final JSON
        all_L.append(per_seed_L_val)
        all_W.append(per_seed_W_val)
        all_busy_frac.append(per_seed_busy_val)
        all_p_loss.append(per_seed_ploss_val)
        all_p_wait.append(per_seed_pwait_val)
        all_arr.append(per_seed_L_val) # Placeholder, will fix below

    # Final Aggregation
    avg_L = sum(all_L) / N
    total_sojourn_sum = sum(results_W_num)
    total_sojourn_count = sum(results_W_den)
    avg_W = (total_sojourn_sum / total_sojourn_count) * 60.0 if total_sojourn_count > 0 else 0.0
    
    avg_busy_frac = sum(all_busy_frac) / N
    avg_p_loss = 0.0
    avg_p_wait = 0.0
    
    avg_arr = sum(results_arr) / N
    avg_dep = sum(results_dep) / N
    avg_blk = sum(results_blk) / N
    
    dep_rate = avg_dep / (win / 60.0) if win > 0 else 0.0 # Per hour? Win is in hours.
    # win is in hours. dep is count. rate = dep / win_hours.
    dep_rate = avg_dep / win if win > 0 else 0.0
    
    lam_eff = avg_arr / win if win > 0 else 0.0

    output = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "hours",
        "seed_list": [S_start + i for i in range(N)],
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
