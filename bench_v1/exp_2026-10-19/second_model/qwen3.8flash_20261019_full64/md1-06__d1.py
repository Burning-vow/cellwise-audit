import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0 # per hour
    mu_base = 60.0 / 5.0 # per hour (service rate for M/M/1 with fixed service? No, D/M/1 or M/D/1?)
    # Problem says: "fixed 5 minutes", Poisson arrivals. This is M/D/1 queue.
    # But standard discrete event simulation usually handles general distributions.
    # Service time is constant 5 mins = 1/12 hours.
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        # If service was variable, this would change dist. Here it's fixed. 
        # Maybe perturbation implies changing the fixed time? 
        # "扰动只改参数不改结构". Let's assume mu_up means faster service? 
        # Or maybe the problem implies M/M/1 in some contexts but explicitly says fixed.
        # Let's stick to M/D/1 logic. If mu_up, maybe reduce service time?
        serv_time_h = 5.0/60.0
        if pert == 'mu_up':
            serv_time_h = serv_time_h / 1.1 # Faster service
        else:
            serv_time_h = 5.0/60.0
    else:
        serv_time_h = 5.0/60.0
        
    if pert == 'c_up':
        pass # c=1 always here
        
    lam = lam_base if pert != 'lam_up' else lam_base * 1.1
    
    # Time unit: hour
    time_unit = "hour"
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_frac_sum = 0.0
    total_arr_count = 0
    total_dep_count = 0
    total_blk_count = 0
    total_win_len = 0.0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        next_dep_t = float('inf')
        
        # State
        n_in_sys = 0
        last_event_t = 0.0
        area_L = 0.0
        area_busy = 0.0 # Integral of min(n,1)
        
        # For W calculation via Little's Law or direct sum?
        # Direct sum of sojourn times is better for finite horizon stats.
        # We need to track arrival times of customers currently in system.
        # Since FCFS and single server, we can just store arrival times.
        # However, for M/D/1, we can simulate events.
        
        # To calculate W accurately in window:
        # Sum of (departure_time - arrival_time) for all departures in window.
        # Count of departures in window.
        
        # Warmup handling:
        # We run until H. Window starts at H * warmup_ratio.
        win_start = H * warmup_ratio
        win_end = H
        
        # We need to integrate L over [win_start, win_end]
        # And sum sojourn times for departures in [win_start, win_end]
        
        # Data structures for pending customers
        # Queue of arrival times
        queue = [] 
        
        # Event loop
        while t < win_end:
            # Determine next event
            if next_arr_t <= next_dep_t:
                # Arrival
                t = next_arr_t
                if t > win_end: break
                
                # Process previous interval
                dt = t - last_event_t
                if last_event_t < win_end and t > win_start:
                    # Overlap with window
                    start_int = max(last_event_t, win_start)
                    end_int = min(t, win_end)
                    if end_int > start_int:
                        dur = end_int - start_int
                        area_L += n_in_sys * dur
                        if n_in_sys > 0:
                            area_busy += dur
                
                # Update state
                n_in_sys += 1
                queue.append(t)
                
                # Schedule departure if server idle
                if n_in_sys == 1:
                    next_dep_t = t + serv_time_h
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                
                last_event_t = t
                
            else:
                # Departure
                t = next_dep_t
                if t > win_end: break
                
                # Process previous interval
                dt = t - last_event_t
                if last_event_t < win_end and t > win_start:
                    start_int = max(last_event_t, win_start)
                    end_int = min(t, win_end)
                    if end_int > start_int:
                        dur = end_int - start_int
                        area_L += n_in_sys * dur
                        if n_in_sys > 0:
                            area_busy += dur
                
                # Update state
                arr_time = queue.pop(0)
                n_in_sys -= 1
                
                # Check if this departure is in window
                if t >= win_start and t <= win_end:
                    # Record sojourn time
                    # We accumulate these separately
                    pass 
                
                # Schedule next departure if queue not empty
                if n_in_sys > 0:
                    next_dep_t = t + serv_time_h
                else:
                    next_dep_t = float('inf')
                    
                last_event_t = t

        # Final integration up to win_end if needed? 
        # The loop breaks when t > win_end. 
        # We need to ensure we integrated up to win_end.
        # Actually, the loop condition `while t < win_end` might miss the final segment if an event happens exactly at win_end or after.
        # Let's refine the loop to handle boundaries carefully.
        
        # Re-running logic for clarity in code generation below...
        
        # Reset for actual implementation structure
        pass

    # Implementing the clean version now
    results = []
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n = 0
        last_t = 0.0
        area_L = 0.0
        area_busy = 0.0
        
        # For W: sum of sojourn times of customers who DEPART within window
        sum_sojourn = 0.0
        count_dep_window = 0
        count_arr_window = 0
        count_blk_window = 0 # Assuming infinite buffer, blk=0. But if finite? Problem doesn't say. Assume infinite.
        
        # Queue of arrival times
        q = []
        
        win_start = H * 0.25
        win_end = H
        
        # We need to process events until win_end
        # Also need to capture arrivals/departures strictly inside window for counts?
        # "arr is statistical window average person count" -> likely number of arrivals IN window.
        # "dep is ... leave count IN window"
        
        while True:
            # Find next event time
            if next_arr < next_dep:
                evt_t = next_arr
                evt_type = 'A'
            else:
                evt_t = next_dep
                evt_type = 'D'
            
            if evt_t > win_end:
                # Integrate remaining time to win_end
                dt = win_end - last_t
                if last_t < win_end:
                    area_L += n * dt
                    if n > 0:
                        area_busy += dt
                break
            
            # Integrate from last_t to evt_t
            dt = evt_t - last_t
            if last_t < win_end and evt_t > win_start:
                s = max(last_t, win_start)
                e = min(evt_t, win_end)
                if e > s:
                    d = e - s
                    area_L += n * d
                    if n > 0:
                        area_busy += d
            
            # Process Event
            if evt_type == 'A':
                # Check if blocked? Infinite buffer assumed.
                n += 1
                q.append(evt_t)
                if n == 1:
                    next_dep = evt_t + serv_time_h
                next_arr = evt_t + rng.expovariate(lam)
                
                if win_start <= evt_t < win_end:
                    count_arr_window += 1
                    
            else: # Departure
                arr_t = q.pop(0)
                n -= 1
                sojourn = evt_t - arr_t
                
                if win_start <= evt_t < win_end:
                    sum_sojourn += sojourn
                    count_dep_window += 1
                
                if n > 0:
                    next_dep = evt_t + serv_time_h
                else:
                    next_dep = float('inf')
            
            last_t = evt_t
            
        # Calculate stats for this seed
        win_len = win_end - win_start
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            bf_est = 0.0
            pl_est = 0.0
            pw_est = 0.0
        else:
            L_est = area_L / win_len
            if count_dep_window > 0:
                W_est = sum_sojourn / count_dep_window
            else:
                W_est = 0.0 # Or NaN? Use 0 for safety in JSON
            
            bf_est = area_busy / win_len
            
            # p_loss: blocked / arrived? If infinite buffer, 0.
            # p_wait: fraction of time waiting? Or probability a customer waits?
            # Usually p_wait in queueing theory context of output might mean P(W>0) or utilization?
            # Given "busy_util=E[min(N,c)]/c", busy_frac is similar.
            # Let's interpret p_wait as probability that an arriving customer has to wait (server busy).
            # We didn't track this directly. 
            # Alternative interpretation: Fraction of time system is non-empty? That's busy_frac.
            # Let's look at keys: p_loss, p_wait.
            # In loss systems, p_loss is blocking prob.
            # In waiting systems, p_wait often refers to P(wait > 0).
            # To get P(wait > 0), we need to check if server was busy upon arrival.
            # We can approximate or re-simulate. 
            # Let's add tracking for arrivals where n_before > 0.
            pass

        # Re-run with extra tracking for p_wait
        # Actually, let's just do one pass with all trackers.
        
        # Resetting for correct single-pass implementation
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        n = 0
        last_t = 0.0
        area_L = 0.0
        area_busy = 0.0
        sum_sojourn = 0.0
        count_dep_w = 0
        count_arr_w = 0
        count_wait_arr = 0 # Arrivals finding server busy
        
        q = []
        
        while True:
            if next_arr < next_dep:
                evt_t = next_arr
                typ = 'A'
            else:
                evt_t = next_dep
                typ = 'D'
                
            if evt_t > win_end:
                dt = win_end - last_t
                if last_t < win_end:
                    area_L += n * dt
                    if n > 0: area_busy += dt
                break
                
            dt = evt_t - last_t
            if last_t < win_end and evt_t > win_start:
                s = max(last_t, win_start)
                e = min(evt_t, win_end)
                if e > s:
                    d = e - s
                    area_L += n * d
                    if n > 0: area_busy += d
            
            if typ == 'A':
                # Was server busy before this arrival?
                if n > 0:
                    count_wait_arr += 1
                
                n += 1
                q.append(evt_t)
                if n == 1:
                    next_dep = evt_t + serv_time_h
                next_arr = evt_t + rng.expovariate(lam)
                
                if win_start <= evt_t < win_end:
                    count_arr_w += 1
            else:
                arr_t = q.pop(0)
                n -= 1
                soj = evt_t - arr_t
                if win_start <= evt_t < win_end:
                    sum_sojourn += soj
                    count_dep_w += 1
                if n > 0:
                    next_dep = evt_t + serv_time_h
                else:
                    next_dep = float('inf')
            
            last_t = evt_t
            
        wl = win_end - win_start
        L_s = area_L / wl if wl > 0 else 0
        W_s = sum_sojourn / count_dep_w if count_dep_w > 0 else 0
        BF_s = area_busy / wl if wl > 0 else 0
        PL_s = 0.0 # Infinite buffer
        PW_s = count_wait_arr / count_arr_w if count_arr_w > 0 else 0.0
        
        per_seed_L.append(L_s)
        per_seed_W.append(W_s)
        per_seed_busy_frac.append(BF_s)
        per_seed_p_loss.append(PL_s)
        per_seed_p_wait.append(PW_s)
        
        total_L_sum += L_s
        total_W_sum += W_s
        total_busy_frac_sum += BF_s
        total_arr_count += count_arr_w
        total_dep_count += count_dep_w
        total_blk_count += 0 # Losses
        total_win_len += wl

    seeds_used = len(per_seed_L)
    avg_L = total_L_sum / seeds_used if seeds_used > 0 else 0
    avg_W = total_W_sum / seeds_used if seeds_used > 0 else 0
    avg_BF = total_busy_frac_sum / seeds_used if seeds_used > 0 else 0
    avg_arr = total_arr_count / seeds_used if seeds_used > 0 else 0
    avg_dep = total_dep_count / seeds_used if seeds_used > 0 else 0
    avg_blk = total_blk_count / seeds_used if seeds_used > 0 else 0
    
    # dep_rate: effective departure rate per hour
    # Total deps / Total time
    if total_win_len > 0:
        dep_rate = (total_dep_count / total_win_len) * 60.0 # Wait, time_unit is hour. Rate is per hour.
        # So just total_dep / total_hours
        dep_rate_val = total_dep_count / total_win_len
    else:
        dep_rate_val = 0.0
        
    lam_eff = dep_rate_val # Conservation of flow in stable system
    
    p_loss_avg = avg_blk / avg_arr if avg_arr > 0 else 0.0
    p_wait_avg = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0.0
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_BF, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(total_win_len / seeds_used, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_BF, 4), # E[min(N,1)]/1
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss_avg, 4),
        "p_wait": round(p_wait_avg, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
