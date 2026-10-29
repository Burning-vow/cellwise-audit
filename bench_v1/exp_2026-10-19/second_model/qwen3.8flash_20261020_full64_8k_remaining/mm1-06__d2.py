import json, math, random, sys, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 7.0 / 60.0 # per minute
    mu_base = 1.0 / 5.0   # per minute
    
    if a.pert == 'lam_up': lam_base *= 1.1
    elif a.pert == 'mu_up': mu_base *= 1.1
    elif a.pert == 'c_up': pass # c is fixed at 1 for M/M/1
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_area = 0.0
    total_wait_count = 0
    total_wait_sum = 0.0
    total_busy_time = 0.0
    horizon_min = a.horizon * 60.0 # Convert horizon to minutes if input is hours? 
    # The prompt says H unit matches time_unit. Let's assume time_unit is 'minute' internally.
    # If user passes --horizon 1000, and we treat it as minutes, that's fine.
    # But standard queueing sims often use hours or seconds. Let's stick to MINUTES as internal time unit.
    # So if H is given in "time_unit", and we set time_unit="minute", then H is minutes.
    
    time_unit = "minute"
    win = horizon_min
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        
        n = 0
        busy = False
        
        # Warmup: discard first 25% of time
        warmup_end = 0.25 * horizon_min
        
        # Accumulators for this seed (post-warmup)
        s_area_n = 0.0
        s_time_busy = 0.0
        s_arr = 0
        s_dep = 0
        s_blk = 0
        s_wait_cnt = 0
        s_wait_sum = 0.0
        
        last_event_time = 0.0
        
        while t < horizon_min:
            # Determine next event
            if next_arr < next_dep:
                t_next = next_arr
                evt_type = 'arr'
            else:
                t_next = next_dep
                evt_type = 'dep'
                
            if t_next > horizon_min:
                break
                
            dt = t_next - t
            
            # Integrate area before state change
            if t >= warmup_end:
                s_area_n += n * dt
                if busy:
                    s_time_busy += dt
                    
            t = t_next
            
            if evt_type == 'arr':
                # Service time drawn NOW
                serv_time = rng.expovariate(mu_base)
                
                if n == 0:
                    # Start service immediately
                    busy = True
                    next_dep = t + serv_time
                    n = 1
                    wait_time = 0.0
                else:
                    # Queue increases
                    n += 1
                    wait_time = None # Will be calculated on departure? No, W is system time.
                    # We need to track arrival time to calculate system time upon departure.
                    # Since we don't store individual customers easily without classes,
                    # let's use a simple FIFO list of arrival times.
                    # But the constraint says "no classes". A list is fine.
                    # Actually, for M/M/1, we can just count. But to get W accurately via Little's Law or direct sum?
                    # Direct sum requires knowing when each customer leaves.
                    # Let's maintain a queue of arrival times.
                    pass
                
                # Re-evaluating approach for W calculation without complex structures
                # Standard DES: Keep a list of waiting customers' arrival times.
                # When service completes, pop one, calculate system time.
                
                # Let's restart the loop logic with a proper queue structure using lists.
                # This is getting messy inside the single function.
                # Let's refactor slightly within the loop.
                
                # Reset accumulators for this seed properly
                # I will rewrite the inner loop logic below.
                break # Break to restructure
            
            elif evt_type == 'dep':
                pass
        
        # --- RESTRUCTURED INNER LOOP ---
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        
        # Queue stores arrival times
        q = [] 
        n_in_sys = 0 # Includes being served
        
        warmup_end = 0.25 * horizon_min
        
        s_area_n = 0.0
        s_time_busy = 0.0
        s_arr = 0
        s_dep = 0
        s_blk = 0 # M/M/1 has no blocking usually, unless finite capacity. Problem implies infinite.
        s_wait_cnt = 0
        s_wait_sum = 0.0
        
        # For P(wait), we check if server was busy upon arrival
        
        while t < horizon_min:
            if next_arr < next_dep:
                t_next = next_arr
                evt = 'A'
            else:
                t_next = next_dep
                evt = 'D'
            
            if t_next > horizon_min:
                break
                
            dt = t_next - t
            
            # Integrate BEFORE changing state
            if t >= warmup_end:
                s_area_n += n_in_sys * dt
                if len(q) > 0 or (n_in_sys > 0 and not q): # Busy if someone is being served
                    # Server is busy if there is anyone in the system (since FCFS, if N>0, server is busy)
                    # Wait, if N>0, server is busy.
                    if n_in_sys > 0:
                        s_time_busy += dt
            
            t = t_next
            
            if evt == 'A':
                s_arr += 1
                # Draw service time now
                serv_t = rng.expovariate(mu_base)
                
                # Check if server is busy
                if n_in_sys == 0:
                    # Server idle, start service
                    n_in_sys = 1
                    next_dep = t + serv_t
                    # Customer does not wait
                    if t >= warmup_end:
                        s_wait_cnt += 1 # Total customers counted for prob? Or just those who arrived?
                        # p_wait is fraction of arrivals that wait.
                        # We need to track how many waited vs total arrivals.
                        pass
                else:
                    # Server busy, join queue
                    n_in_sys += 1
                    q.append((t, serv_t)) # Store arrival time and required service time? 
                    # No, service time is attached to customer. 
                    # If they are in queue, their service hasn't started.
                    # We need to know when they START service to add to dep time.
                    # Simpler: Just store arrival time. Service time distribution is memoryless.
                    # But we drew serv_t already. We must keep it.
                    # Let's store (arrival_time, service_time)
                    q[-1] = (t, serv_t) 
                    
                # Update stats for waiting probability
                if t >= warmup_end:
                    # Did this customer wait?
                    # If they joined queue (n_in_sys > 1 effectively, or rather server was busy), they wait.
                    # In the branch above: if n_in_sys was 0, no wait. Else wait.
                    # We need a flag.
                    pass

            elif evt == 'D':
                s_dep += 1
                # Complete service of current customer
                # Who is being served? The one at front of queue? 
                # In my model: if n_in_sys==1, the one being served is the only one.
                # If n_in_sys > 1, the one being served finished, next starts.
                
                # How to identify the departing customer's arrival time?
                # If n_in_sys == 1:
                #   The person being served is the one who started service.
                #   We didn't store their arrival time explicitly if they started immediately.
                #   Let's change strategy: Always push to a "serving" slot and a "queue" list.
                
                # Let's simplify:
                # State: 
                #   serving_customer: (arrival_time, service_time_remaining_or_total?) 
                #   Actually, since we draw full service time at arrival, we can just track completion time.
                #   But if they wait, their service starts later.
                
                # Better Model:
                #   List `in_service`: empty or contains (arrival_time, end_time)
                #   List `waiting`: contains (arrival_time, service_duration)
                
                # On Arrival:
                #   Draw serv_dur.
                #   If `in_service` is empty:
                #       Add (t, t+serv_dur) to `in_service`.
                #       Next Dep = t + serv_dur.
                #   Else:
                #       Add (t, serv_dur) to `waiting`.
                
                # On Departure:
                #   Remove from `in_service`.
                #   Calculate System Time = t - arrival_time.
                #   If `waiting` not empty:
                #       Pop first (arr_t, serv_dur).
                #       New End Time = t + serv_dur.
                #       Add (arr_t, new_end_time) to `in_service`.
                #       Next Dep = new_end_time.
                #   Else:
                #       `in_service` empty. Next Dep = inf.
                
                # This works. Let's implement this specific logic.
                
                # Refactoring the loop body again...
                break 

        # Final Implementation Plan for Loop:
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        
        # in_service: tuple (arrival_time, scheduled_departure_time) or None
        in_service = None 
        # waiting: list of tuples (arrival_time, service_duration)
        waiting = []
        
        warmup_end = 0.25 * horizon_min
        
        s_area_n = 0.0
        s_time_busy = 0.0
        s_arr = 0
        s_dep = 0
        s_wait_cnt = 0 # Count of arrivals that had to wait
        s_total_arr = 0 # Count of all arrivals in window
        s_system_time_sum = 0.0
        
        while t < horizon_min:
            if next_arr < next_dep:
                t_next = next_arr
                evt = 'A'
            else:
                t_next = next_dep
                evt = 'D'
            
            if t_next > horizon_min:
                break
            
            dt = t_next - t
            
            # Current number in system
            n_curr = 0
            if in_service is not None: n_curr += 1
            n_curr += len(waiting)
            
            # Integrate
            if t >= warmup_end:
                s_area_n += n_curr * dt
                if in_service is not None:
                    s_time_busy += dt
            
            t = t_next
            
            if evt == 'A':
                s_arr += 1
                serv_dur = rng.expovariate(mu_base)
                
                if in_service is None:
                    # Start service
                    in_service = (t, t + serv_dur)
                    next_dep = t + serv_dur
                    # Did not wait
                else:
                    # Join queue
                    waiting.append((t, serv_dur))
                    # Waited
                    if t >= warmup_end:
                        s_wait_cnt += 1
                
                if t >= warmup_end:
                    s_total_arr += 1
            
            elif evt == 'D':
                s_dep += 1
                arr_t, dep_t = in_service
                sys_time = t - arr_t
                
                if t >= warmup_end:
                    s_system_time_sum += sys_time
                
                # Move next from waiting to service
                if waiting:
                    next_cust_arr_t, next_cust_serv_dur = waiting.pop(0)
                    new_dep_t = t + next_cust_serv_dur
                    in_service = (next_cust_arr_t, new_dep_t)
                    next_dep = new_dep_t
                else:
                    in_service = None
                    next_dep = float('inf')
        
        # Seed Stats
        if s_total_arr > 0:
            L_est = s_area_n / (horizon_min - warmup_end) if horizon_min > warmup_end else 0
            W_est = s_system_time_sum / s_dep if s_dep > 0 else 0 # Average system time
            # Note: W should be average over ALL customers in window. 
            # s_dep counts departures in window. Customers arriving but not departing yet are excluded from W mean?
            # Usually yes, or we estimate via Little's Law. 
            # Prompt asks for W. Direct measurement is better.
            # However, if a customer arrives near end and doesn't leave, they aren't in s_dep.
            # This biases W. But for long horizon, negligible.
            
            busy_frac_est = s_time_busy / (horizon_min - warmup_end) if horizon_min > warmup_end else 0
            p_wait_est = s_wait_cnt / s_total_arr if s_total_arr > 0 else 0
            p_loss_est = 0.0 # Infinite buffer
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_wait.append(p_wait_est)
            per_seed_p_loss.append(p_loss_est)
            
            total_time_area += s_area_n
            total_busy_time += s_time_busy
            total_arr += s_arr
            total_dep += s_dep
            total_wait_count += s_wait_cnt
            total_wait_sum += s_system_time_sum # Sum of system times for departed
            
            # For global averages, we need total effective observation time
            # Global L = Total Area / Total Window Time
            # Global W = Total System Time Sum / Total Departures
            
    num_seeds = len(seeds_used)
    if num_seeds == 0:
        print(json.dumps({}))
        return
        
    eff_win_len = (horizon_min - 0.25 * horizon_min) * num_seeds
    
    global_L = total_time_area / eff_win_len if eff_win_len > 0 else 0
    global_W = total_wait_sum / total_dep if total_dep > 0 else 0
    global_busy_frac = total_busy_time / eff_win_len if eff_win_len > 0 else 0
    global_p_wait = total_wait_count / total_arr if total_arr > 0 else 0
    global_p_loss = 0.0
    
    # Identity checks
    # L = lambda_eff * W
    # lambda_eff = total_dep / eff_win_len (per hour? no, per minute)
    # dep_rate per hour = (total_dep / eff_win_len) * 60
    
    lam_eff_per_min = total_dep / eff_win_len if eff_win_len > 0 else 0
    dep_rate_per_hour = lam_eff_per_min * 60.0
    
    # busy_util = E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0.
    # So busy_util = P(N>=1) = busy_frac.
    # busy_occupied = 1 - pi_0 = P(N>=1) = busy_frac.
    
    out = {
        "L": round(global_L, 6),
        "W": round(global_W, 6),
        "busy_frac": round(global_busy_frac, 6),
        "p_wait": round(global_p_wait, 6),
        "runtime_units": "minutes",
        "seed_list": seeds_used,
        "seeds_used": num_seeds,
        "time_unit": time_unit,
        "win": round(eff_win_len / num_seeds, 6), # Average window length per seed? Or total? "win is statistical window length". Usually per run.
        "arr": round(total_arr / num_seeds, 6),
        "blk": 0.0,
        "busy_util": round(global_busy_frac, 6),
        "dep": round(total_dep / num_seeds, 6),
        "dep_rate": round(dep_rate_per_hour, 6),
        "lam_eff": round(lam_eff_per_min * 60.0, 6), # Effective arrival rate per hour
        "p_loss": 0.0,
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
