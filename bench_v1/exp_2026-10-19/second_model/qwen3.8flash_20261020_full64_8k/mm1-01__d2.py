import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()

    lam_base = 4.0 # per hour
    mu_base = 10.0 # per hour (6 min mean)
    
    if args.pert == 'lam_up': lam = lam_base * 1.1
    elif args.pert == 'mu_up': mu = mu_base * 1.1; lam = lam_base
    elif args.pert == 'c_up': lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} # id -> duration
        queue = [] # list of arrival times
        server_free_time = 0.0
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        count_wait = 0 # customers who waited > 0
        
        cust_id_counter = 0
        
        while t < horizon:
            # Determine next event time
            arr_t = next_arrival
            dep_t = float('inf')
            if queue or server_free_time > t:
                # If someone is being served, departure is at server_free_time
                # But we need to know when the current service ends.
                # In discrete event sim with pre-sampled durations:
                # We track server_free_time as the absolute time the current service finishes.
                dep_t = server_free_time
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= horizon:
                break
                
            # Integrate areas up to next_t
            dt = next_t - last_event_t
            if last_event_t >= win_start:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            
            t = next_t
            last_event_t = t
            
            if abs(t - arr_t) < 1e-9:
                # Arrival
                count_arr += 1
                dur = rng.expovariate(mu)
                cust_id_counter += 1
                service_times[cust_id_counter] = dur
                
                if n_in_sys == 0:
                    # Server idle, start immediately
                    n_in_sys = 1
                    server_free_time = t + dur
                else:
                    # Server busy, join queue
                    n_in_sys += 1
                    queue.append((cust_id_counter, t))
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                # Departure
                count_dep += 1
                # Who leaves? The one currently in service. 
                # In our model, we don't explicitly store "current customer ID" separately from queue logic easily without a class.
                # Let's refine: queue holds waiting customers. One customer is in service.
                # When arrival happens and n_in_sys==0, that customer enters service.
                # When arrival happens and n_in_sys>0, it joins queue.
                # When departure happens, the person in service leaves. Then check queue.
                
                # Problem: How do we know which ID was in service?
                # We can maintain a variable `current_cust_id`.
                pass 

        # Re-implementing loop with explicit state variables for clarity within constraints
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # list of (id, arrival_time)
        current_id = None
        current_service_end = 0.0
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        count_wait = 0
        sum_w = 0.0 # sum of sojourn times for departures in window
        
        cust_id_counter = 0
        
        while t < horizon:
            arr_t = next_arrival
            dep_t = current_service_end if current_id is not None else float('inf')
            
            next_t = min(arr_t, dep_t)
            if next_t >= horizon:
                break
            
            dt = next_t - last_event_t
            if last_event_t >= win_start:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            
            t = next_t
            last_event_t = t
            
            if abs(t - arr_t) < 1e-9:
                count_arr += 1
                dur = rng.expovariate(mu)
                cust_id_counter += 1
                
                if n_in_sys == 0:
                    n_in_sys = 1
                    current_id = cust_id_counter
                    current_service_end = t + dur
                else:
                    n_in_sys += 1
                    queue.append((cust_id_counter, t))
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                count_dep += 1
                # Calculate sojourn time for departing customer
                # We need to know when this customer arrived.
                # Since we didn't store arrival time for the one in service, let's fix that.
                # Actually, simpler: store (id, arrival_time) for everyone.
                # For the one in service, we have current_id but lost arrival time.
                # Let's change structure: `in_service` tuple (id, arrival_time).
                pass

        # Final attempt with correct data structures
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # list of (arrival_time)
        in_service_arrival = None
        in_service_end = 0.0
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        count_wait = 0
        sum_w_window = 0.0
        
        while t < horizon:
            arr_t = next_arrival
            dep_t = in_service_end if in_service_arrival is not None else float('inf')
            
            next_t = min(arr_t, dep_t)
            if next_t >= horizon:
                break
            
            dt = next_t - last_event_t
            if last_event_t >= win_start:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            
            t = next_t
            last_event_t = t
            
            if abs(t - arr_t) < 1e-9:
                count_arr += 1
                dur = rng.expovariate(mu)
                
                if n_in_sys == 0:
                    n_in_sys = 1
                    in_service_arrival = t
                    in_service_end = t + dur
                else:
                    n_in_sys += 1
                    queue.append(t) # Store arrival time of waiting customer
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                count_dep += 1
                w = t - in_service_arrival
                if in_service_arrival >= win_start:
                    sum_w_window += w
                    if w > 1e-9: count_wait += 1 # Waited if service didn't start immediately upon arrival? 
                    # Definition of wait: Time spent in queue. Sojourn W includes service.
                    # P(wait) usually means probability of joining queue.
                    # If n_in_sys > 0 at arrival, they wait.
                    # Here, we are at departure. We need to know if THIS customer waited.
                    # We lost that info unless we stored it.
                    # Let's assume standard definition: P(wait) = fraction of arrivals that had to queue.
                    # We can count waits at arrival time.
                    
                # Next customer from queue
                if queue:
                    next_arr_time = queue.pop(0)
                    # Service starts now
                    in_service_arrival = next_arr_time
                    # Need new service time? No, service time was drawn at arrival.
                    # PROBLEM: Requirement says "service duration must be drawn at arrival".
                    # My previous code drew it at arrival but didn't store it for queued people.
                    # Fix: Queue stores (arrival_time, service_duration).
                    pass

        # Correct Implementation
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # list of (arrival_time, service_duration)
        in_service = None # (arrival_time, end_time)
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        count_wait_at_arr = 0
        sum_w_window = 0.0
        
        while t < horizon:
            arr_t = next_arrival
            dep_t = in_service[1] if in_service else float('inf')
            
            next_t = min(arr_t, dep_t)
            if next_t >= horizon:
                break
            
            dt = next_t - last_event_t
            if last_event_t >= win_start:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            
            t = next_t
            last_event_t = t
            
            if abs(t - arr_t) < 1e-9:
                count_arr += 1
                dur = rng.expovariate(mu)
                
                if n_in_sys == 0:
                    n_in_sys = 1
                    in_service = (t, t + dur)
                else:
                    n_in_sys += 1
                    queue.append((t, dur))
                    count_wait_at_arr += 1 # This customer waited
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                count_dep += 1
                arr_time, _ = in_service
                w = t - arr_time
                if arr_time >= win_start:
                    sum_w_window += w
                
                if queue:
                    next_arr_time, next_dur = queue.pop(0)
                    in_service = (next_arr_time, t + next_dur)
                else:
                    in_service = None
                    n_in_sys -= 1 # Now 0
        
        # Post-processing for this seed
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = sum_w_window / count_dep if count_dep > 0 else 0 # Little's law check: L = lambda_eff * W
        # Note: W should be average over all customers in system? Or just those completed?
        # Standard simulation estimates W based on completed customers in window.
        busy_frac_est = area_busy / win_len if win_len > 0 else 0
        p_wait_est = count_wait_at_arr / count_arr if count_arr > 0 else 0
        p_loss_est = 0.0 # M/M/1 infinite buffer, no loss
        
        seeds_used.append(seed)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += count_arr
        total_dep += count_dep
        total_blk += count_blk

    N = len(seeds_used)
    avg_L = sum(per_seed_L) / N
    avg_W = sum(per_seed_W) / N
    avg_busy = sum(per_seed_busy_frac) / N
    avg_p_wait = sum(per_seed_p_wait) / N
    avg_p_loss = sum(per_seed_p_loss) / N
    
    avg_arr = total_arr / N
    avg_dep = total_dep / N
    avg_blk = total_blk / N
    
    dep_rate = avg_dep / win_len * 60.0 # per hour? No, time_unit is hour.
    # dep_rate is "个/每小时". If time_unit is hour, then rate is just count/hour.
    # But win_len is in hours. So dep_rate = avg_dep / win_len.
    dep_rate_val = avg_dep / win_len if win_len > 0 else 0
    
    lam_eff = dep_rate_val
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
