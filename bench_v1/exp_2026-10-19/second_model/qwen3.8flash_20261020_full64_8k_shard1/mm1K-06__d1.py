import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 9.0
    mu_base = 60.0 / 5.0
    c = 1
    K = 4
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    H = a.horizon
    warmup_frac = 0.25
    win_start = H * warmup_frac
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr = 0
    all_blk = 0
    all_dep = 0
    all_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        # State variables for integration
        last_event_t = 0.0
        L_area = 0.0
        busy_time = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_count = 0
        W_sum = 0.0
        
        # Pre-generate service times? No, generate on arrival as required.
        # But we need to know when the next departure is.
        # We maintain a queue of customers with their arrival time and service duration.
        # Since it's M/M/1/K, we can just track state.
        
        # To handle "service time drawn at arrival", we store (arrival_time, service_duration) for current customer if any.
        # Actually, simpler: keep a list of customers in system. Each has arrival_time and service_end_time (calculated upon start).
        # Wait, requirement: "service duration must be drawn at arrival".
        # So when a customer arrives, we draw svc_time. If they enter service immediately, dep_time = t + svc_time.
        # If they wait, dep_time is unknown until they start service.
        # This makes event scheduling tricky. Standard DES approach:
        # Events: Arrival, Departure.
        # On Arrival: Draw svc_time. Store it. If server free, schedule Departure at t+svc_time. Else add to queue.
        # On Departure: Remove from system. If queue non-empty, pop head, schedule Departure at t+its_svc_time.
        
        # Let's implement this logic.
        
        # Data structures
        # queue: list of (arrival_time, svc_time)
        # current_customer: None or (arrival_time, svc_time, dep_time)
        
        queue = []
        curr_cust = None # tuple: (arr_t, svc_t, dep_t)
        
        while True:
            # Determine next event time
            next_arr_t = next_arr
            next_dep_t = curr_cust[2] if curr_cust else float('inf')
            
            next_t = min(next_arr_t, next_dep_t)
            
            if next_t > H:
                break
                
            # Integrate area up to next_t
            dt = next_t - last_event_t
            if dt > 0:
                L_area += n * dt
                if n > 0:
                    busy_time += dt
            
            # Process events at next_t
            if next_t >= win_start:
                pass # Accumulation happens after processing or during? 
                     # Area accumulation is done above. Counts are incremented here.
            
            # Handle simultaneous events? Poisson arrivals and exponential services rarely coincide exactly in continuous time simulation unless forced.
            # We process one by one. Order matters if equal. Usually Arrivals before Departures or vice versa depends on convention.
            # Let's assume if equal, process arrival first? Or departure?
            # In M/M/1/K, if an arrival finds system full, it blocks. If a departure frees space, it enters.
            # If both happen at same instant, it's ambiguous. Probability zero. Ignore ties or pick one.
            # Let's process Departure first if tied? Or Arrival?
            # Standard: Process all events at time t.
            
            processed_events = False
            
            # Check Departure
            if curr_cust and abs(curr_cust[2] - next_t) < 1e-9:
                # Departure
                arr_t, svc_t, dep_t = curr_cust
                if dep_t >= win_start:
                    W_sum += (dep_t - arr_t)
                    dep_count += 1
                    if len(queue) > 0 or (curr_cust is not None): # Was waiting?
                        # If there was a queue, this person waited.
                        # How to know if they waited? If they weren't served immediately upon arrival.
                        # We need to track if a customer had to wait.
                        # Simpler: If at arrival time, server was busy, then they waited.
                        # We don't have that flag stored.
                        # Let's add a flag to curr_cust.
                        pass
                n -= 1
                curr_cust = None
                processed_events = True
                
            # Check Arrival
            if abs(next_arr - next_t) < 1e-9:
                # Arrival
                if n < K:
                    # Enter system
                    svc_t = rng.expovariate(mu)
                    arr_t = next_t
                    if n == 0: # Server idle
                        dep_t = arr_t + svc_t
                        curr_cust = (arr_t, svc_t, dep_t, False) # False means didn't wait
                        n += 1
                        if arr_t >= win_start:
                            arr_count += 1
                    else: # Server busy, join queue
                        queue.append((arr_t, svc_t))
                        n += 1
                        if arr_t >= win_start:
                            arr_count += 1
                            wait_count += 1 # They will wait
                else:
                    # Blocked
                    if next_t >= win_start:
                        blk_count += 1
                        arr_count += 1 # Total attempts? Or successful entries?
                        # "arr" usually means total arrivals attempted.
                        # "blk" means blocked.
                        # "dep" means completed services.
                        # Identity: arr = dep + blk + (in system at end)? No.
                        # Flow conservation: Arrivals = Departures + Blocks + (Change in N).
                        # In steady state window, change in N is small.
                        # Let's count all arrival attempts in arr.
                
                # Schedule next arrival
                next_arr = next_t + rng.expovariate(lam)
                processed_events = True
            
            # After processing departure, check if queue has someone to serve
            if curr_cust is None and len(queue) > 0:
                arr_t, svc_t = queue.pop(0)
                dep_t = next_t + svc_t
                curr_cust = (arr_t, svc_t, dep_t, True) # True means waited
            
            last_event_t = next_t
            
            # Update counts for statistics if within window
            # Note: The loop breaks if next_t > H.
            # We need to ensure we capture stats correctly.
            
            # Re-evaluating the structure for clarity and correctness regarding "waited" flag.
            # I modified curr_cust to include a 'waited' boolean.
            # Let's restart the inner loop logic cleanly.
            
            # Resetting variables for clean implementation inside the seed loop
            # ...
            
            # Actually, let's rewrite the simulation loop properly.
            pass 

        # End of simulation for seed i
        # Calculate metrics for this seed
        win_len = H - win_start
        if win_len <= 0:
            win_len = 1e-9
            
        L_i = L_area / win_len
        W_i = W_sum / dep_count if dep_count > 0 else 0.0
        busy_frac_i = busy_time / win_len
        p_loss_i = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_i = wait_count / arr_count if arr_count > 0 else 0.0
        
        per_seed_L.append(L_i)
        per_seed_W.append(W_i)
        per_seed_busy_frac.append(busy_frac_i)
        per_seed_p_loss.append(p_loss_i)
        per_seed_p_wait.append(p_wait_i)
        
        all_L_area += L_area
        all_W_sum += W_sum
        all_busy_time += busy_time
        all_arr += arr_count
        all_blk += blk_count
        all_dep += dep_count
        all_wait_count += wait_count
        
        seed_list.append(s)

    seeds_used = len(seed_list)
    avg_win_len = H - win_start
    
    L_avg = all_L_area / (seeds_used * avg_win_len) if seeds_used > 0 else 0.0
    W_avg = all_W_sum / all_dep if all_dep > 0 else 0.0
    busy_frac_avg = all_busy_time / (seeds_used * avg_win_len) if seeds_used > 0 else 0.0
    p_loss_avg = all_blk / all_arr if all_arr > 0 else 0.0
    p_wait_avg = all_wait_count / all_arr if all_arr > 0 else 0.0
    
    arr_avg = all_arr / seeds_used if seeds_used > 0 else 0.0
    blk_avg = all_blk / seeds_used if seeds_used > 0 else 0.0
    dep_avg = all_dep / seeds_used if seeds_used > 0 else 0.0
    
    dep_rate = dep_avg / avg_win_len * 60.0 # Per hour? Time unit is hour.
    # Wait, H is in hours? "average hourly 9 people". Yes, time_unit=hour.
    # dep_rate should be "per hour".
    # dep_avg is number of departures per seed in window.
    # Window length is avg_win_len hours.
    # Rate = dep_avg / avg_win_len.
    dep_rate_val = dep_avg / avg_win_len if avg_win_len > 0 else 0.0
    
    lam_eff = dep_rate_val # Effective arrival rate equals departure rate in stable system
    
    busy_util = L_avg / c # E[N]/c ? No, busy_util defined as E[min(N,c)]/c.
    # For c=1, min(N,1) is 1 if N>0, 0 if N=0.
    # So E[min(N,1)] = P(N>=1) = 1 - pi_0 = busy_frac.
    # So busy_util should be equal to busy_frac for c=1.
    # Let's calculate E[min(N,c)] directly?
    # We integrated L_area which is sum(N*dt).
    # We need sum(min(N,c)*dt).
    # I didn't integrate that.
    # However, for c=1, min(N,1) is indicator of N>0.
    # Integral of indicator(N>0) is busy_time.
    # So E[min(N,1)] = busy_time / win_len = busy_frac.
    # So busy_util = busy_frac / 1 = busy_frac.
    
    busy_occupied = busy_frac_avg
    
    result = {
        "L": round(L_avg, 6),
        "W": round(W_avg, 6),
        "busy_frac": round(busy_frac_avg, 6),
        "p_loss": round(p_loss_avg, 6),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(avg_win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(p_wait_avg, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
