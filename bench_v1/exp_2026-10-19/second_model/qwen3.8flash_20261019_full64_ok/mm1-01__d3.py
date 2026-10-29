import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    n_seeds = args.seeds
    horizon = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 4.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr? No, 6 min = 0.1 hr. Mean service time = 0.1 hr. Rate mu = 1/0.1 = 10 per hour.
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
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
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    
    for i in range(n_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of (arrival_time, service_duration)
        server_free_time = 0.0
        num_in_system = 0
        
        # Statistics accumulators for the window [burn_in_end, horizon]
        burn_in_end = horizon * 0.25
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_wait_events = 0 # For p_wait: fraction of arrivals that waited
        
        last_event_time = 0.0
        
        while True:
            # Determine next event time
            arr_t = next_arrival
            dep_t = float('inf')
            if queue:
                # The head of queue is being served or waiting?
                # In M/M/1 with FCFS:
                # If server is busy, the current service ends at server_free_time.
                # But we need to know when the *next* departure happens.
                # Actually, standard DES:
                # Events: Arrival, Departure.
                # State: Server status (busy/free), Queue length.
                
                # Let's refine state representation.
                # We track:
                # - t: current simulation time
                # - server_status: 0 (free), 1 (busy)
                # - queue: list of customers waiting (not including one in service)
                # - current_service_end_time: if server is busy
                
                pass
            
            # Re-implementing loop structure properly
            
            # Reset variables for this seed run
            t = 0.0
            next_arrival = rng.expovariate(lam)
            queue = [] 
            server_busy_until = 0.0
            is_server_busy = False
            
            # Stats
            area_L = 0.0
            area_busy = 0.0
            count_arr = 0
            count_dep = 0
            count_blk = 0
            sum_W = 0.0
            count_waited = 0
            
            last_update_time = 0.0
            
            while t < horizon:
                # Find next event
                events = []
                if next_arrival <= horizon:
                    events.append(('arr', next_arrival))
                if is_server_busy and server_busy_until <= horizon:
                    events.append(('dep', server_busy_until))
                    
                if not events:
                    break
                    
                events.sort(key=lambda x: x[1])
                evt_type, evt_time = events[0]
                
                # Integrate stats from last_update_time to evt_time
                dt = evt_time - last_update_time
                if last_update_time >= burn_in_end:
                    # Only integrate within the statistical window
                    # But wait, if we cross the boundary, we should split integration.
                    # Simpler: Always integrate, but only accumulate if interval overlaps window.
                    # Or: Check if last_update_time >= burn_in_end.
                    # Since we process events sequentially, let's handle the boundary carefully.
                    
                    start_int = max(last_update_time, burn_in_end)
                    end_int = min(evt_time, horizon)
                    if start_int < end_int:
                        int_len = end_int - start_int
                        # L is number in system
                        n_sys = len(queue) + (1 if is_server_busy else 0)
                        area_L += n_sys * int_len
                        if is_server_busy:
                            area_busy += 1 * int_len
                            
                elif last_update_time < burn_in_end and evt_time > burn_in_end:
                    # Crosses boundary
                    int_len_pre = burn_in_end - last_update_time
                    int_len_post = evt_time - burn_in_end
                    n_sys = len(queue) + (1 if is_server_busy else 0)
                    area_L += n_sys * int_len_post
                    if is_server_busy:
                        area_busy += 1 * int_len_post
                        
                last_update_time = evt_time
                t = evt_time
                
                if evt_type == 'arr':
                    count_arr += 1
                    # Generate service time now
                    svc_time = rng.expovariate(mu)
                    
                    if not is_server_busy:
                        is_server_busy = True
                        server_busy_until = t + svc_time
                        # Customer does not wait
                        w = svc_time
                        sum_W += w
                    else:
                        queue.append((t, svc_time))
                        # Customer waits
                        # Wait time will be calculated upon departure
                        count_waited += 1 # Mark as waited arrival
                        
                    next_arrival = t + rng.expovariate(lam)
                    
                elif evt_type == 'dep':
                    count_dep += 1
                    # Calculate W for the departing customer
                    # Who is departing? The one who started service at server_busy_until - svc_time?
                    # No, we need to track arrival time of the one in service.
                    # Let's change queue structure.
                    # queue stores (arrival_time, service_duration)
                    # When server becomes free, it takes from queue.
                    
                    # Correction: We need to know the arrival time of the person currently in service.
                    # Let's add a variable `current_cust_arrival`
                    pass

            # Need to restructure slightly to track current customer arrival time
            # Let's restart the inner loop logic with better state tracking.
            
            # --- Restart Seed Loop Logic ---
            t = 0.0
            next_arrival = rng.expovariate(lam)
            queue = [] # (arrival_time, service_duration)
            is_server_busy = False
            server_busy_until = 0.0
            current_cust_arrival = None
            
            area_L = 0.0
            area_busy = 0.0
            count_arr = 0
            count_dep = 0
            count_blk = 0
            sum_W = 0.0
            count_waited = 0
            last_update_time = 0.0
            
            while t < horizon:
                events = []
                if next_arrival <= horizon:
                    events.append(('arr', next_arrival))
                if is_server_busy and server_busy_until <= horizon:
                    events.append(('dep', server_busy_until))
                    
                if not events:
                    break
                    
                events.sort(key=lambda x: x[1])
                evt_type, evt_time = events[0]
                
                dt = evt_time - last_update_time
                if dt > 0:
                    start_int = max(last_update_time, burn_in_end)
                    end_int = min(evt_time, horizon)
                    if start_int < end_int:
                        int_len = end_int - start_int
                        n_sys = len(queue) + (1 if is_server_busy else 0)
                        area_L += n_sys * int_len
                        if is_server_busy:
                            area_busy += 1 * int_len
                            
                last_update_time = evt_time
                t = evt_time
                
                if evt_type == 'arr':
                    count_arr += 1
                    svc_time = rng.expovariate(mu)
                    
                    if not is_server_busy:
                        is_server_busy = True
                        server_busy_until = t + svc_time
                        current_cust_arrival = t
                        # W = svc_time (no wait)
                        sum_W += svc_time
                    else:
                        queue.append((t, svc_time))
                        count_waited += 1
                        
                    next_arrival = t + rng.expovariate(lam)
                    
                elif evt_type == 'dep':
                    count_dep += 1
                    # This customer leaves
                    # W = (departure_time - arrival_time)
                    w = t - current_cust_arrival
                    sum_W += w
                    
                    if queue:
                        next_arr, next_svc = queue.pop(0)
                        is_server_busy = True
                        server_busy_until = t + next_svc
                        current_cust_arrival = next_arr
                    else:
                        is_server_busy = False
                        server_busy_until = 0.0
                        current_cust_arrival = None
            
            # Final integration up to horizon if needed? 
            # The loop breaks when t >= horizon or no events.
            # If t < horizon after loop, we might miss tail.
            # But events are generated only if <= horizon.
            # So t will reach horizon or stop before.
            # If stopped before horizon because no more events, we need to integrate remaining time.
            if t < horizon:
                start_int = max(t, burn_in_end)
                end_int = horizon
                if start_int < end_int:
                    int_len = end_int - start_int
                    n_sys = len(queue) + (1 if is_server_busy else 0)
                    area_L += n_sys * int_len
                    if is_server_busy:
                        area_busy += 1 * int_len
            
            win_len = horizon - burn_in_end
            if win_len <= 0:
                win_len = 1e-9
                
            L_est = area_L / win_len
            W_est = sum_W / count_dep if count_dep > 0 else 0.0
            busy_frac_est = area_busy / win_len
            p_wait_est = count_waited / count_arr if count_arr > 0 else 0.0
            p_loss_est = count_blk / count_arr if count_arr > 0 else 0.0
            lam_eff_est = count_dep / win_len
            dep_rate_est = count_dep / win_len # per hour since time_unit is hour
            
            busy_util_est = busy_frac_est # E[min(N,c)]/c with c=1
            busy_occ_est = busy_frac_est # 1 - pi_0 approx by time average
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(count_arr)
            all_dep.append(count_dep)
            all_blk.append(count_blk)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occ_est)
            all_lam_eff.append(lam_eff_est)
            all_p_loss.append(p_loss_est)
            
    seeds_used = n_seeds
    seed_list = [seed_start + i for i in range(seeds_used)]
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occ = sum(all_busy_occupied) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    
    result = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "p_wait": avg_p_wait,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": horizon * 0.75,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": avg_busy_util,
        "dep": avg_dep,
        "dep_rate": avg_lam_eff,
        "lam_eff": avg_lam_eff,
        "p_loss": avg_p_loss,
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait,
        "busy_occupied": avg_busy_occ
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
