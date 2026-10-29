import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    args = p.parse_args()
    N = args.seeds; H = args.horizon; S = args.seed_start; pert = args.pert
    lam_base = 7.0; mu_base = 10.0 # per hour
    if pert == "lam_up": lam_base *= 1.2
    elif pert == "mu_up": mu_base *= 1.2
    elif pert == "c_up": pass
    
    time_unit = "hour"
    seeds_used = 0
    L_sum = 0.0; W_sum = 0.0; busy_frac_sum = 0.0; p_wait_sum = 0.0
    arr_sum = 0; blk_sum = 0; dep_sum = 0; busy_util_sum = 0.0; busy_occ_sum = 0.0
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = [] # list of arrival times
        service_end = None
        n_in_sys = 0
        total_time_n = 0.0
        total_time_busy = 0.0
        total_wait_time = 0.0
        count_arr = 0; count_dep = 0; count_blk = 0; count_wait = 0
        
        # We need to track state changes for integration
        last_event_t = 0.0
        current_n = 0
        is_busy = False
        
        while t < H:
            # Determine next event time
            events = []
            if next_arr <= H: events.append(('arr', next_arr))
            if service_end is not None and service_end <= H: events.append(('dep', service_end))
            
            if not events: break
            
            etype, etime = min(events, key=lambda x: x[1])
            
            # Integrate area from last_event_t to etime
            dt = etime - last_event_t
            if last_event_t >= H * warmup_ratio:
                total_time_n += current_n * dt
                if is_busy: total_time_busy += dt
            
            t = etime
            last_event_t = t
            
            if etype == 'arr':
                count_arr += 1
                # Generate service time now
                svc_time = rng.expovariate(mu_base)
                
                if len(queue) == 0 and not is_busy:
                    # Start service immediately
                    is_busy = True
                    service_end = t + svc_time
                    current_n += 1
                else:
                    # Join queue or blocked? M/M/1/K usually has finite capacity. 
                    # Problem says "system stable", implies infinite buffer or high enough. 
                    # Standard M/M/1 assumes infinite buffer unless K specified. 
                    # But "blk" suggests blocking. Let's assume infinite buffer -> blk=0 always?
                    # Or maybe finite capacity? The prompt doesn't specify K. 
                    # However, it asks for blk. If infinite, blk is 0.
                    # Let's assume infinite buffer as standard M/M/1.
                    queue.append((t, svc_time))
                    current_n += 1
                    if len(queue) > 0: # Waited
                        pass 
                    # Actually, if server busy, they wait.
                    # Check if they waited: if server was busy when they arrived
                    if is_busy:
                         count_wait += 1
                         # Store arrival time for wait calc later? 
                         # We stored (t, svc_time). Need original arrival time for wait.
                         # Let's store (arrival_time, service_duration)
                         queue[-1] = (t, svc_time)
                
                next_arr = t + rng.expovariate(lam_base)
                
            elif etype == 'dep':
                count_dep += 1
                # Calculate wait time for the departing customer
                # Who departed? The one at head of queue or the one being served?
                # In M/M/1 FCFS, the one being served departs.
                # We need to know who was being served.
                # My previous logic: if server free, start service. Else queue.
                # When dep happens, we finish the current service.
                # Then check queue.
                
                # Wait, I didn't track who is currently in service separately from queue properly for wait time.
                # Let's refine:
                # State: Server Busy? Service End Time. Queue List.
                # On Arrival:
                #   If Server Free: Set Busy, ServiceEnd = t + svc. Add to system count.
                #   If Server Busy: Add to Queue. System Count++.
                # On Departure:
                #   System Count--.
                #   If Queue Not Empty: Pop front. Set Busy, ServiceEnd = t + svc_of_popped.
                #   Else: Set Idle.
                
                # To calculate W, we need sum of (departure_time - arrival_time) for all customers.
                # I need to store arrival time of the person currently in service.
                
                # Correction in loop structure needed.
                pass

        # Re-implementing loop with correct tracking
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = [] # stores (arrival_time, service_duration)
        service_end = None
        current_service_arrival = None # arrival time of person in service
        
        n_in_sys = 0
        total_time_n = 0.0
        total_time_busy = 0.0
        total_so_journey = 0.0 # Sum of (dep - arr)
        count_arr = 0; count_dep = 0; count_blk = 0; count_wait = 0
        
        last_event_t = 0.0
        current_n = 0
        is_busy = False
        
        while t < H:
            events = []
            if next_arr <= H: events.append(('arr', next_arr))
            if service_end is not None and service_end <= H: events.append(('dep', service_end))
            
            if not events: break
            
            etype, etime = min(events, key=lambda x: x[1])
            
            dt = etime - last_event_t
            if last_event_t >= H * warmup_ratio:
                total_time_n += current_n * dt
                if is_busy: total_time_busy += dt
            
            t = etime
            last_event_t = t
            
            if etype == 'arr':
                count_arr += 1
                svc_dur = rng.expovariate(mu_base)
                
                if not is_busy:
                    is_busy = True
                    service_end = t + svc_dur
                    current_service_arrival = t
                    current_n += 1
                else:
                    queue.append((t, svc_dur))
                    current_n += 1
                    count_wait += 1 # They will wait
                
                next_arr = t + rng.expovariate(lam_base)
                
            elif etype == 'dep':
                count_dep += 1
                # Customer leaves
                journey_time = t - current_service_arrival
                if last_event_t - dt >= H * warmup_ratio: # Approximate check, better to check if departure is in window
                     # Actually, we should only accumulate stats for customers whose entire stay or relevant part is in window?
                     # Usually Little's Law uses average over window. 
                     # W = Total Time in System / Number of Arrivals (in window)? 
                     # Or Total Time in System (integrated) / Average N?
                     # Prompt says: "area-type quantities must be integrated before changing state".
                     # And "statistics accumulated only in window after removing first 25% warmup".
                     
                     # For W: It's an average of individual sojourn times.
                     # Should we include a customer who arrived before warmup but left during window?
                     # Standard practice: Only count customers arriving in the steady-state window.
                     # So if arrival_time < warmup_end, ignore their contribution to W numerator/denominator?
                     # But N(t) integral includes them.
                     # Let's stick to: 
                     # L = Integral(N(t)) / Window_Length
                     # W = Sum(Sojourn_Times_of_Customers_Arriving_In_Window) / Count_Arrivals_In_Window
                     # This ensures consistency with Little's Law L = lambda_eff * W.
                     
                     if current_service_arrival >= H * warmup_ratio:
                         total_so_journey += journey_time
                         # Note: count_arr used for denominator should also be filtered?
                         # Yes, let's keep separate counters for window stats.
                         pass
                
                # Next customer
                if queue:
                    arr_t, dur = queue.pop(0)
                    current_service_arrival = arr_t
                    service_end = t + dur
                    # is_busy remains True
                else:
                    is_busy = False
                    service_end = None
                    current_service_arrival = None
                    current_n -= 1 # Decrease because one left, none entered service from queue? 
                    # Wait, if queue empty, server becomes idle. N decreases by 1.
                    # If queue not empty, N stays same (one leaves, one enters service).
                    # My current_n increment/decrement logic:
                    # Arr: current_n++
                    # Dep: if queue empty, current_n--. If queue not empty, current_n unchanged (one out, one in service).
                    
                    # Let's fix current_n update on Dep:
                    if not queue:
                        current_n -= 1
                    # If queue had items, we popped one into service, so N remains same.
        
        # Post-process for this seed
        # Recalculate window-specific counts
        # I need to re-run or track carefully. 
        # Tracking inside loop is messy for "Arrivals in Window".
        # Let's use lists to record arrivals and departures.
        
        # Restart simulation for clean data collection
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        current_service_arrival = None
        
        arrivals = [] # (time, svc_dur)
        departures = [] # (time, arrival_time)
        
        last_event_t = 0.0
        current_n = 0
        is_busy = False
        n_history = [] # (time, n)
        busy_history = [] # (time, is_busy)
        
        while t < H:
            events = []
            if next_arr <= H: events.append(('arr', next_arr))
            if service_end is not None and service_end <= H: events.append(('dep', service_end))
            if not events: break
            
            etype, etime = min(events, key=lambda x: x[1])
            
            # Record state change history
            n_history.append((etime, current_n))
            busy_history.append((etime, is_busy))
            
            t = etime
            last_event_t = t
            
            if etype == 'arr':
                svc_dur = rng.expovariate(mu_base)
                arrivals.append((t, svc_dur))
                
                if not is_busy:
                    is_busy = True
                    service_end = t + svc_dur
                    current_service_arrival = t
                    current_n += 1
                else:
                    queue.append((t, svc_dur))
                    current_n += 1
                
                next_arr = t + rng.expovariate(lam_base)
                
            elif etype == 'dep':
                departures.append((t, current_service_arrival))
                
                if queue:
                    arr_t, dur = queue.pop(0)
                    current_service_arrival = arr_t
                    service_end = t + dur
                    # current_n unchanged
                else:
                    is_busy = False
                    service_end = None
                    current_service_arrival = None
                    current_n -= 1
        
        # Final state
        n_history.append((H, current_n))
        busy_history.append((H, is_busy))
        
        # Compute Integrals over [warmup, H]
        w_start = H * warmup_ratio
        w_end = H
        w_len = w_end - w_start
        
        int_n = 0.0
        int_busy = 0.0
        
        # Process N
        prev_t = 0.0
        prev_n = 0
        for k in range(len(n_history)):
            curr_t, curr_n_val = n_history[k]
            if curr_t > w_start:
                seg_start = max(prev_t, w_start)
                seg_end = min(curr_t, w_end)
                if seg_end > seg_start:
                    int_n += prev_n * (seg_end - seg_start)
            prev_t = curr_t
            prev_n = curr_n_val
            
        # Process Busy
        prev_t = 0.0
        prev_b = False
        for k in range(len(busy_history)):
            curr_t, curr_b_val = busy_history[k]
            if curr_t > w_start:
                seg_start = max(prev_t, w_start)
                seg_end = min(curr_t, w_end)
                if seg_end > seg_start:
                    if prev_b: int_busy += (seg_end - seg_start)
            prev_t = curr_t
            prev_b = curr_b_val
            
        L_est = int_n / w_len if w_len > 0 else 0.0
        busy_frac_est = int_busy / w_len if w_len > 0 else 0.0
        
        # Stats for customers arriving in window
        custs_in_win = [(a, s) for a, s in arrivals if a >= w_start]
        num_custs = len(custs_in_win)
        
        # Match departures
        # Since we have global departures list, filter those where arrival >= w_start
        # And ensure departure <= H (they might leave after H? Simulation stops at H. 
        # If they haven't left, do we count them? 
        # Usually, we only count completed journeys.
        # But Little's law holds for open systems too if we account for unfinished work?
        # Simpler: Only count customers who arrived AND departed within [w_start, H]?
        # Or arrived in [w_start, H] and departed anywhere?
        # If they depart after H, we don't have their departure time.
        # Given H is horizon, we assume steady state. 
        # Let's count only those who departed by H.
        
        dep_map = {d_arr: d_time for d_time, d_arr in departures}
        
        total_journey = 0.0
        valid_count = 0
        wait_count = 0
        
        for a, s in custs_in_win:
            if a in dep_map:
                d = dep_map[a]
                if d <= H:
                    total_journey += (d - a)
                    valid_count += 1
                    # Did they wait?
                    # If there was any other customer ahead of them when they arrived?
                    # Or simply: if server was busy at arrival time.
                    # We can check busy_history at time a.
                    # Find last busy state before a.
                    b_state = False
                    for bt, bv in busy_history:
                        if bt <= a: b_state = bv
                        else: break
                    if b_state:
                        wait_count += 1
                        
        W_est = total_journey / valid_count if valid_count > 0 else 0.0
        p_wait_est = wait_count / valid_count if valid_count > 0 else 0.0
        p_loss_est = 0.0 # Infinite buffer
        
        # Utilization E[min(N,c)]/c = busy_frac for c=1
        # 1 - pi_0 = fraction of time N>0.
        # In M/M/1, P(N=0) = 1-rho. Busy frac = rho.
        # Are they identical? Yes.
        # But prompt asks for busy_util and busy_occupied separately.
        # busy_util = E[min(N,1)]/1 = P(N>=1) = busy_frac.
        # busy_occupied = 1 - pi_0 = P(N>=1) = busy_frac.
        # They are the same number.
        
        L_sum += L_est
        W_sum += W_est
        busy_frac_sum += busy_frac_est
        p_wait_sum += p_wait_est
        arr_sum += num_custs # Arrivals in window
        dep_sum += valid_count # Departures in window (completed)
        blk_sum += 0
        busy_util_sum += busy_frac_est
        busy_occ_sum += busy_frac_est
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        seeds_used += 1

    avg_L = L_sum / seeds_used if seeds_used else 0
    avg_W = W_sum / seeds_used if seeds_used else 0
    avg_busy = busy_frac_sum / seeds_used if seeds_used else 0
    avg_pw = p_wait_sum / seeds_used if seeds_used else 0
    avg_arr
