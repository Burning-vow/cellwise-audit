import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if args.pert == 'lam_up': lam = lam_base * 1.2
    elif args.pert == 'mu_up': mu = mu_base * 1.2
    elif args.pert == 'c_up': c = 2; K = 5
    else: lam, mu = lam_base, mu_base
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time = 0.0
    total_area_N = 0.0
    total_area_busy = 0.0
    total_wait_time = 0.0
    total_service_time = 0.0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        horizon = args.horizon
        next_arrival = rng.expovariate(lam)
        service_times = [] 
        queue = [] 
        busy_until = -1.0
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_sum = 0.0
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        busy_intervals = 0.0
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if busy_until > t and busy_until <= horizon:
                events.append(('dep', busy_until))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_t
            if dt > 0:
                area_N += last_N * dt
                if last_N > 0:
                    busy_intervals += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if len(queue) + (1 if busy_until > t else 0) < K:
                    queue.append((t, st))
                    if busy_until <= t:
                        start_t, dur = queue.pop(0)
                        busy_until = t + dur
                        wait_sum += (start_t - t) # Wait is time from arrival to start? No, W usually system time or waiting time?
                        # Standard Little's Law L = lambda * W where W is system time.
                        # Let's calculate System Time W_sys = Waiting + Service.
                        # But prompt asks for W. Usually in queues W is waiting time or system time.
                        # "W (minutes)" often implies waiting time in line OR total time in system.
                        # Given "L" is number in system, W should be time in system.
                        # Let's track departure times to compute exact system time.
                        pass
                else:
                    blk_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
                # Update state for area calculation
                current_N = len(queue) + (1 if busy_until > t else 0)
                last_N = current_N
                last_t = t
                
            elif ev_type == 'dep':
                dep_count += 1
                # The customer who finished service was the one that started at busy_until - duration
                # We need to know when they arrived to calculate system time.
                # This simple loop doesn't store arrival time of the person currently being served easily 
                # unless we pop from a separate structure or assume FIFO.
                # Let's restructure slightly to ensure we can calculate W correctly.
                pass

        # Re-implementing with better tracking for W (System Time)
        # Reset variables for this seed
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of (arrival_time, service_duration)
        busy_until = -1.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sys_time_sum = 0.0
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        busy_time_sum = 0.0
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if busy_until > t and busy_until <= horizon:
                events.append(('dep', busy_until))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_t
            if dt > 0:
                area_N += last_N * dt
                if last_N > 0:
                    busy_time_sum += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                # Check capacity: Queue length + (1 if server busy else 0) < K
                # Server is busy if busy_until > t
                is_server_busy = busy_until > t
                current_occupancy = len(queue) + (1 if is_server_busy else 0)
                
                if current_occupancy < K:
                    queue.append((t, st))
                    if not is_server_busy:
                        # Start service immediately
                        start_arr, dur = queue.pop(0)
                        busy_until = t + dur
                        # Note: The person starting service is removed from queue list conceptually 
                        # but physically they are in the system. 
                        # Our 'queue' list holds WAITING people.
                        # So occupancy check above was correct.
                        # When we pop, the person moves to "in service".
                        # We need to track their arrival time to calc W upon departure.
                        # Let's keep a variable for the person in service.
                        pass
                else:
                    blk_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
                # Recalculate N for next interval
                is_server_busy = busy_until > t
                current_N = len(queue) + (1 if is_server_busy else 0)
                last_N = current_N
                last_t = t
                
            elif ev_type == 'dep':
                dep_count += 1
                # Who departed? The one who started service at busy_until - duration.
                # We lost the arrival time of the person in service if we didn't store it.
                # Fix: Store (arrival_time, end_time) for the person in service.
                # Actually, simpler: Keep a variable `current_customer` = (arrival_time, service_end_time).
                # When dep happens, W = t - current_customer.arrival_time.
                # Then pick next from queue if any.
                pass

        # Final attempt with clean logic
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # (arrival_time, service_duration)
        curr_cust = None # (arrival_time, service_end_time)
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sys_time_sum = 0.0
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        busy_time_sum = 0.0
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if curr_cust and curr_cust[1] <= horizon and curr_cust[1] > t:
                events.append(('dep', curr_cust[1]))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_t
            if dt > 0:
                area_N += last_N * dt
                if last_N > 0:
                    busy_time_sum += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                # Occupancy: queue size + (1 if curr_cust exists)
                occ = len(queue) + (1 if curr_cust else 0)
                if occ < K:
                    queue.append((t, st))
                    if not curr_cust:
                        # Start service
                        arr_t, dur = queue.pop(0)
                        curr_cust = (arr_t, t + dur)
                else:
                    blk_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
                occ = len(queue) + (1 if curr_cust else 0)
                last_N = occ
                last_t = t
                
            elif ev_type == 'dep':
                dep_count += 1
                arr_t, end_t = curr_cust
                sys_time_sum += (end_t - arr_t)
                curr_cust = None
                
                if queue:
                    arr_t_next, dur_next = queue.pop(0)
                    curr_cust = (arr_t_next, t + dur_next)
                
                occ = len(queue) + (1 if curr_cust else 0)
                last_N = occ
                last_t = t

        # End of simulation for this seed
        # Calculate stats for this seed
        # Warmup removal: 25%
        warmup_end = horizon * 0.25
        
        # We need to re-run or store history to do proper warmup removal on area/time integrals.
        # Since I didn't store history, I'll approximate by running again or just using full run 
        # BUT requirement says "statistics only accumulated after removing first 25% warmup".
        # And "area quantities must be integrated before changing state".
        # My previous loop integrated over the whole time.
        # To strictly follow, I need to reset and run again, ignoring data before warmup_end.
        
        # Re-run for accurate warmup handling
        t = 0.0
        next_arrival = rng.expovariate(lam) # New stream? No, same seed, new RNG instance? 
        # Requirement: "Each seed uses independent random stream". 
        # If I re-run, I must use the SAME random sequence to get the same path, 
        # but filter the statistics.
        # Easiest way: Run once, store all event times and states? Too much memory/code.
        # Alternative: Run twice. First run to consume randomness? No, that changes stream.
        # Correct approach: Use a fresh RNG for each seed. Run simulation. 
        # During simulation, only accumulate stats if t >= warmup_end.
        
        # Let's restart the inner loop logic with filtering.
        
        rng = random.Random(seed) # Reset RNG for this seed to ensure reproducibility if needed, 
                                  # but actually we want ONE pass.
                                  # The issue is I already consumed the RNG in the failed attempts above.
                                  # I will refactor to do it in one pass properly.
                                  
        # Refactored Single Pass Logic
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        curr_cust = None
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sys_time_sum = 0.0
        area_N = 0.0
        busy_time_sum = 0.0
        last_t = 0.0
        last_N = 0
        warmup_end = horizon * 0.25
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if curr_cust and curr_cust[1] <= horizon and curr_cust[1] > t:
                events.append(('dep', curr_cust[1]))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_t
            if dt > 0:
                # Integrate area only if the interval overlaps with post-warmup window
                # Or simply: if last_t >= warmup_end, add full dt.
                # If straddling, split. For simplicity in discrete event sim without complex splitting:
                # We can just check if the START of the interval is past warmup.
                # Better: Accumulate raw, then subtract? No, hard for area.
                # Let's do precise integration.
                if last_t < warmup_end and ev_time > warmup_end:
                    # Split interval
                    dt_pre = warmup_end - last_t
                    dt_post = ev_time - warmup_end
                    # Pre part ignored
                    area_N += last_N * dt_post
                    if last_N > 0:
                        busy_time_sum += dt_post
                elif last_t >= warmup_end:
                    area_N += last_N * dt
                    if last_N > 0:
                        busy_time_sum += dt
                # Else entirely in warmup, ignore
            
            t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                occ = len(queue) + (1 if curr_cust else 0)
                if occ < K:
                    queue.append((t, st))
                    if not curr_cust:
                        arr_t, dur = queue.pop(0)
                        curr_cust = (arr_t, t + dur)
                else:
                    blk_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
                occ = len(queue) + (1 if curr_cust else 0)
                last_N = occ
                last_t = t
                
            elif ev_type == 'dep':
                dep_count += 1
                arr_t, end_t = curr_cust
                # Only count system time if the DEPARTURE is after warmup? 
                # Or if the ENTIRE stay is after warmup? 
                # Standard practice: Count customers who depart after warmup.
                if t >= warmup_end:
                    sys_time_sum += (end_t - arr_t)
                curr_cust = None
                
                if queue:
                    arr_t_next, dur_next = queue.pop(0)
                    curr_cust = (arr_t_next, t + dur_next)
                
                occ = len(queue) + (1 if curr_cust else 0)
                last_N = occ
                last_t = t

        # Post-processing for this seed
        win_len = horizon - warmup_end
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
        else:
            L_est = area_N / win_len
            # W = Total System Time / Number of Departures in Window
            # Note: dep_count includes those in warmup. We need deps in window.
            # I didn't count deps in window separately. 
            # Correction: In the loop, I incremented dep_count always.
            # I need a counter for deps in window.
            # Let's fix the loop variable usage.
            pass

        # Due to complexity of fixing mid-thought, I will write the final code carefully.
        # Key fixes:
        # 1. Track dep_in_window.
        # 2. Track arr_in_window? No, p_loss is based on arrivals in window.
        # 3. Ensure RNG is used correctly.

    # Since I cannot iterate further in thought block efficiently, I will generate the code directly.
    # Structure:
    # Loop seeds.
    # Init RNG.
    # Simulate.
    # Filter stats by warmup.
    # Aggregate.
    # Print JSON.

if __name__ == "__main__":
    main()
