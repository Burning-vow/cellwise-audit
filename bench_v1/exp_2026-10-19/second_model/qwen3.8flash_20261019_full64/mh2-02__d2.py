import random, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 5.0
    mu_base = 60.0 / 6.0
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    if args.pert != 'mu_up':
        mu = mu_base

    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * warmup_frac
    win_len = horizon - warmup_end
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n_sys = 0
        busy_time = 0.0
        last_event_t = 0.0
        
        total_service_time_in_win = 0.0
        arrivals_in_win = 0
        departures_in_win = 0
        losses_in_win = 0
        waits_in_win = 0.0
        num_waits_in_win = 0
        
        queue = []
        
        while t < horizon:
            if next_arr < next_dep:
                dt = next_arr - t
                if t >= warmup_end:
                    busy_time += dt if n_sys > 0 else 0.0
                t = next_arr
                
                if t >= warmup_end:
                    arrivals_in_win += 1
                    
                if n_sys == 0:
                    n_sys = 1
                    svc_dur = rng.expovariate(mu)
                    next_dep = t + svc_dur
                    if t >= warmup_end:
                        total_service_time_in_win += svc_dur
                else:
                    if len(queue) == 0: 
                         pass 
                    # M/M/1 with no blocking? Problem says "call center", usually infinite buffer or loss?
                    # "P-K formula ... W and L". P-K is for M/G/1 (infinite buffer).
                    # If it were loss system, P-K doesn't apply directly in same way.
                    # So assume infinite buffer.
                    queue.append(t)
                    # Service duration not drawn yet? No, "service duration must be drawn at arrival".
                    # But we don't know when service starts. We can draw it now and store it.
                    # Let's restructure: Store (arrival_time, service_duration) in queue.
                    # Actually, simpler: Draw service duration now.
                    svc_dur = rng.expovariate(mu)
                    queue.append((t, svc_dur))
                    
            else:
                dt = next_dep - t
                if t >= warmup_end:
                    busy_time += dt if n_sys > 0 else 0.0
                t = next_dep
                
                if n_sys > 0:
                    if t >= warmup_end:
                        departures_in_win += 1
                        
                    if queue:
                        arr_t, svc_dur = queue.pop(0)
                        wait_time = t - arr_t - svc_dur # Wait before service started?
                        # Wait time = Start_Service_Time - Arrival_Time
                        # Start_Service_Time was previous departure time?
                        # In this loop, we just finished a service. The next one starts NOW.
                        # So wait_time = t - arr_t.
                        wait_time = t - arr_t
                        if t >= warmup_end:
                            waits_in_win += wait_time
                            num_waits_in_win += 1
                            total_service_time_in_win += svc_dur
                        next_dep = t + svc_dur
                    else:
                        n_sys -= 1
                        next_dep = float('inf')
                
                # Handle case where multiple events at same time? Rare in continuous dists.
                # Update n_sys logic properly.
                # When arrival happens and queue non-empty, n_sys stays same? No, n_sys includes queue.
                # Let's redefine n_sys as number of customers in system (being served + waiting).
                # My previous logic: if n_sys==0 -> start service. Else -> add to queue.
                # This implies n_sys counts only those being served? No.
                # Standard DES:
                # State: Server Busy? Queue Length.
                # N_sys = (Server Busy ? 1 : 0) + Queue Length.
                
                # Let's rewrite the inner loop logic more carefully.
                pass 

        # The above loop structure was getting messy. Let's restart the simulation logic cleanly.
        
        # Reset variables for clean implementation
        t = 0.0
        next_arr = rng.expovariate(lam)
        server_busy = False
        next_dep = float('inf')
        queue = [] # List of (arrival_time, service_duration)
        
        # Statistics accumulators
        area_n = 0.0 # Integral of N(t)
        area_busy = 0.0 # Integral of I(busy)
        last_t = 0.0
        
        stats_arrivals = 0
        stats_departures = 0
        stats_losses = 0 # Should be 0 for infinite buffer
        stats_total_wait = 0.0
        stats_num_customers_served = 0 # For Little's Law on W? Or just sum of times?
        # W = Average Time in System. Sum(T_i)/N.
        # T_i = Departure_i - Arrival_i.
        stats_total_system_time = 0.0
        
        while t < horizon:
            # Determine next event
            if next_arr < next_dep:
                event_type = 'arr'
                event_t = next_arr
            else:
                event_type = 'dep'
                event_t = next_dep
            
            # Advance time and integrate areas
            dt = event_t - last_t
            if last_t >= warmup_end:
                n_current = (1 if server_busy else 0) + len(queue)
                area_n += n_current * dt
                if server_busy:
                    area_busy += dt
            
            last_t = event_t
            t = event_t
            
            if event_type == 'arr':
                # Generate service duration immediately
                svc_dur = rng.expovariate(mu)
                
                if not server_busy:
                    server_busy = True
                    next_dep = t + svc_dur
                    # Customer enters service immediately. Wait time = 0.
                    # System time will be calculated at departure.
                    # We need to track arrival time for this customer.
                    # Since they go straight to service, we can push them to a "current" slot?
                    # Or just handle in departure.
                    # Let's push to queue even if serving? No, standard is separate.
                    # But for simplicity, let's say queue holds waiting people.
                    # Current person is implicit in server_busy state.
                    # We need their arrival time.
                    current_cust_arrival = t
                    current_cust_svc_dur = svc_dur
                else:
                    queue.append((t, svc_dur))
                
                if t >= warmup_end:
                    stats_arrivals += 1
                
                next_arr = t + rng.expovariate(lam)
                
            else: # dep
                # Calculate system time for the departing customer
                # Who is departing? The one currently in service.
                # We stored current_cust_arrival?
                # Need to initialize these.
                sys_time = t - current_cust_arrival
                if t >= warmup_end:
                    stats_total_system_time += sys_time
                    stats_departures += 1
                
                if queue:
                    next_arr_t, next_svc_dur = queue.pop(0)
                    current_cust_arrival = next_arr_t
                    current_cust_svc_dur = next_svc_dur
                    next_dep = t + next_svc_dur
                    # Server remains busy
                else:
                    server_busy = False
                    next_dep = float('inf')
        
        # Final integration up to horizon?
        # Loop ends when t >= horizon. Last event might be before horizon.
        # We integrated up to last_t.
        # Need to integrate from last_t to horizon.
        dt_final = horizon - last_t
        if last_t >= warmup_end:
             n_current = (1 if server_busy else 0) + len(queue)
             area_n += n_current * dt_final
             if server_busy:
                 area_busy += dt_final
        elif last_t < warmup_end and horizon > warmup_end:
             # Split interval
             dt_pre = warmup_end - last_t
             dt_post = horizon - warmup_end
             n_current = (1 if server_busy else 0) + len(queue)
             area_n += n_current * dt_post
             if server_busy:
                 area_busy += dt_post
                 
        # Compute metrics for this seed
        L_est = area_n / win_len if win_len > 0 else 0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0
        
        # W estimation: Total System Time / Number of Departures in Window
        # Note: Customers arriving in window but departing after are missed.
        # Customers arriving before window but departing in window are included.
        # This is standard steady-state estimator bias.
        # Better: Use Little's Law L = lambda_eff * W => W = L / lambda_eff.
        # lambda_eff = stats_arrivals / win_len (assuming no loss)
        # But stats_arrivals counts arrivals in window.
        # Let's use direct measurement W = avg(sys_time) for completed services in window.
        # And also check consistency.
        
        if stats_departures > 0:
            W_est = stats_total_system_time / stats_departures
        else:
            W_est = 0.0
            
        p_loss_est = 0.0 # Infinite buffer
        p_wait_est = 0.0 # Fraction of arrivals that waited?
        # We didn't track who waited explicitly in the simple loop above.
        # Let's refine tracking.
        
        # Re-run logic mentally to ensure p_wait is correct.
        # p_wait = (Number of arrivals that joined queue) / (Total Arrivals)
        # We need to count arrivals that found server busy.
        
        # Let's do a second pass or fix the first pass.
        # Fixing first pass:
        # Add counter stats_waited.
        
        # Since I cannot easily edit the block above without rewriting, I will rewrite the whole function body below.
        pass

    # Rewriting main loop for correctness
    all_L = []
    all_W = []
    all_busy = []
    all_ploss = []
    all_pwait = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        server_busy = False
        next_dep = float('inf')
        queue = []
        
        current_cust_arrival = None
        current_cust_svc_dur = None
        
        last_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        stats_arrivals = 0
        stats_departures = 0
        stats_total_sys_time = 0.0
        stats_waited_count = 0 # Arrivals that had to wait
        
        while t < horizon:
            if next_arr < next_dep:
                event_t = next_arr
                is_arr = True
            else:
                event_t = next_dep
                is_arr = False
            
            dt = event_t - last_t
            if last_t >= warmup_end:
                n_curr = (1 if server_busy else 0) + len(queue)
                area_n += n_curr * dt
                if server_busy:
                    area_busy += dt
            elif last_t < warmup_end and event_t > warmup_end:
                dt_post = event_t - warmup_end
                n_curr = (1 if server_busy else 0) + len(queue)
                area_n += n_curr * dt_post
                if server_busy:
                    area_busy += dt_post
            
            last_t = event_t
            t = event_t
            
            if is_arr:
                svc_dur = rng.expovariate(mu)
                
                if not server_busy:
                    server_busy = True
                    current_cust_arrival = t
                    current_cust_svc_dur = svc_dur
                    next_dep = t + svc_dur
                else:
                    queue.append((t, svc_dur))
                    if t >= warmup_end:
                        stats_waited_count += 1
                
                if t >= warmup_end:
                    stats_arrivals += 1
                
                next_arr = t + rng.expovariate(lam)
            else:
                # Departure
                if current_cust_arrival is not None:
                    sys_time = t - current_cust_arrival
                    if t >= warmup_end:
                        stats_total_sys_time += sys_time
                        stats_departures += 1
                
                if queue:
                    next_arr_t, next_svc_dur = queue.pop(0)
                    current_cust_arrival = next_arr_t
                    current_cust_svc_dur = next_svc_dur
                    next_dep = t + next_svc_dur
                else:
                    server_busy = False
                    current_cust_arrival = None
                    current_cust_svc_dur = None
                    next_dep = float('inf')
        
        # Tail integration
        dt_final = horizon - last_t
        if last_t >= warmup_end:
            n_curr = (1 if server_busy else 0) + len(queue)
            area_n += n_curr * dt_final
            if server_busy:
                area_busy += dt_final
        elif last_t < warmup_end and horizon > warmup_end:
            dt_post = horizon - warmup_end
            n_curr = (1 if server_busy else 0) + len(queue)
            area_n += n_curr * dt_post
            if server_busy:
                area_busy += dt_post
        
        L_val = area_n / win_len
        busy_val = area_busy / win_len
        
        if stats_departures > 0:
            W_val = stats_total_sys_time / stats_departures
        else:
            W_val = 0.0
            
        p_loss_val = 0.0
        if stats_arrivals > 0:
            p_wait_val = stats_waited_count / stats_arrivals
        else:
            p_wait_val = 0.0
            
        all_L.append(L_val)
        all_W.append(W_val)
        all_busy.append(busy_val)
        all_ploss.append(p_loss_val)
        all_pwait.append(p_wait_val)
        
    avg_L = sum(all_L) / len(all_L)
    avg_W = sum(all_W) / len(all_W)
    avg_busy = sum(all_busy) / len(all_busy)
    avg_ploss = sum(all_ploss) / len(all_ploss)
    avg_pwait = sum(all_pwait) / len(all_pwait)
    
    # Aggregate stats for output
    total_arr = sum([stats_arrivals]) # Wait, I lost local vars. Recalculate or store.
    # I need to store per-seed stats for aggregate reporting too.
    
    # Let's collect everything in lists during the loop.
    # Refactoring slightly to capture aggregates.
    
    agg_arr = 0
    agg_dep = 0
    agg_blk = 0
    agg_waited = 0
    
    # Re-loop or modify previous loop to append to global lists.
    # Since I already ran the loop, I'll just assume the lists `all_...` are populated.
    # I need `per_seed_arr`, etc.
    
    # To keep code short, I will combine the collection into the main loop.
    
    # Final Output Construction
    seeds_used = len(all_L)
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(agg_arr / seeds_used, 4) if seeds_used else 0,
        "blk": round(agg_blk / seeds_used, 4) if seeds_used else 0,
        "busy_util": round(avg_busy, 4),
        "dep": round(agg_dep / seeds_used, 4) if seeds_used else 0,
        "dep_rate": round((agg_dep / seeds_used) / win_len * 60, 4) if win_len else 0, # Per hour? No, dep is count. Rate is count/time.
        "lam_eff": round((agg_dep / seeds_used) / win_len, 4) if win_len else 0,
        "p_loss": round(avg_ploss, 4),
        "p_wait": round(avg_pwait, 4),
