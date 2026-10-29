import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    # Arrival rate: 6 jobs/hour -> lambda = 6 /hr
    # Service time 1: mean 7.5 min = 0.125 hr -> mu1 = 8 /hr
    # Service time 2: mean 6 min = 0.1 hr -> mu2 = 10 /hr
    
    lam_base = 6.0
    mu1_base = 8.0
    mu2_base = 10.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
        mu1 = mu1_base
        mu2 = mu2_base
    elif pert == 'mu_up':
        lam = lam_base
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        # Cost perturbation doesn't affect timing stats directly in this model unless we track cost, 
        # but prompt says "perturbation only changes parameters not structure". 
        # Since no cost parameter was defined in base model description affecting flow, 
        # we treat c_up as no change to rates or perhaps a slight variation if implied. 
        # Given strict adherence to described stochastic model, c_up likely implies no change to arrival/service rates.
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
        
    time_unit = 'hour'
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queue lengths (number of items waiting + being served? No, standard queue length is waiting. 
        # But for L (in-system), we need count in system.
        # Let's track:
        # n1: number in station 1 (waiting + serving)
        # n2: number in station 2 (waiting + serving)
        # server1_free_time: time when server 1 becomes free
        # server2_free_time: time when server 2 becomes free
        
        n1 = 0
        n2 = 0
        s1_free = 0.0
        s2_free = 0.0
        
        # For integration of L (area under curve)
        area_L = 0.0
        last_event_time = 0.0
        
        # For W calculation: sum of sojourn times / number of completions
        total_sojourn = 0.0
        num_completions = 0
        
        # Busy times for utilization
        busy1_time = 0.0
        busy2_time = 0.0
        
        # Counts for statistics
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0 # In infinite buffer, blocking is usually 0 unless finite capacity specified. 
                              # Problem says "each has its own queue", implying infinite buffers. 
                              # So p_loss should be 0.
        
        # Warmup period: first 25% of horizon
        warmup_end = 0.25 * horizon_hours
        
        # We need to simulate until horizon.
        # Events: Arrival at 1, Completion at 1, Completion at 2.
        
        while t < horizon_hours:
            # Determine next event time
            events = []
            if next_arrival < horizon_hours:
                events.append(('arr', next_arrival))
            
            # If server 1 is busy, completion time is s1_free
            if s1_free > t:
                events.append(('comp1', s1_free))
                
            if s2_free > t:
                events.append(('comp2', s2_free))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Integrate L up to etime
            dt = etime - last_event_time
            current_L = n1 + n2
            area_L += current_L * dt
            
            # Update busy times if servers were busy during dt
            # Server 1 is busy if n1 > 0 (since single server, if n1>0 it's working on one)
            # Actually, strictly speaking, if n1 > 0, server 1 is busy.
            if n1 > 0:
                busy1_time += dt
            if n2 > 0:
                busy2_time += dt
                
            t = etime
            last_event_time = t
            
            if etype == 'arr':
                # Arrival at Station 1
                if t >= warmup_end:
                    arrivals_in_window += 1
                
                # Draw service time for Station 1 immediately upon arrival
                st1 = rng.expovariate(mu1)
                
                # Add to system
                n1 += 1
                
                # Check if server 1 is free
                if s1_free <= t:
                    # Start service immediately
                    s1_free = t + st1
                    # Store departure time from 1 in a list associated with the job?
                    # We need to know when this specific job leaves 1 to enter 2.
                    # Since we don't have explicit job objects in simple counter simulation,
                    # we need to manage queues properly to link arrival to departure.
                    # Simple FIFO assumption.
                    # We need a queue for station 1 holding (arrival_time, service_time).
                    pass
                else:
                    # Wait in queue
                    pass
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # To handle linking, let's use lists for queues
                # q1: list of (arrival_time, service_duration)
                # q2: list of (arrival_time_at_2, service_duration)
                
                # Re-initialize state structures for proper tracking
                # This approach requires restructuring slightly to keep per-job data.
                
                # Let's restart the loop logic with proper queues.
                break # Break to restructure below? No, just implement correctly now.
                
            elif etype == 'comp1':
                # Completion at Station 1
                # Pop from q1
                if q1:
                    arr_t, svc_t = q1.pop(0)
                    n1 -= 1
                    
                    # Move to Station 2
                    # Draw service time for Station 2
                    st2 = rng.expovariate(mu2)
                    
                    # Add to q2
                    q2.append((t, st2)) # t is time entering station 2
                    n2 += 1
                    
                    # Check if server 2 is free
                    if s2_free <= t:
                        s2_free = t + st2
                    # Else it waits in q2 (n2 already incremented)
                    
                    # Update busy1_time? Already handled by integration step above based on n1>0.
                    # But wait, if n1 became 0 after pop, the server stops being busy at t.
                    # The integration added dt where n1 was old value. Correct.
                    
            elif etype == 'comp2':
                # Completion at Station 2
                if q2:
                    arr_t2, svc_t2 = q2.pop(0)
                    n2 -= 1
                    
                    # Calculate sojourn time
                    # Need original arrival time at system.
                    # We lost it in q1->q2 transfer if we didn't store it.
                    # Fix: q1 stores (sys_arr_time, svc1_dur). When moving to q2, store (sys_arr_time, svc2_dur).
                    # And q2 needs to know when it entered station 2? No, just sys_arr_time for W.
                    # But we need to know when it started service at 2? No, W is total time in system.
                    # So we just need sys_arr_time.
                    
                    # Let's refine data structures.
                    pass

        # The above inline attempt got messy. Let's write clean code.
        # Reset for clean implementation inside the seed loop.
        
        # Clean Implementation Start
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queues: 
        # q1: list of [sys_arr_time, svc1_duration]
        # q2: list of [sys_arr_time, svc2_duration]
        q1 = []
        q2 = []
        
        # Server availability times
        s1_free = 0.0
        s2_free = 0.0
        
        # Stats accumulators for this seed
        area_L = 0.0
        last_t = 0.0
        total_sojourn = 0.0
        num_dep = 0
        busy1 = 0.0
        busy2 = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        warmup = 0.25 * horizon_hours
        
        while t < horizon_hours:
            # Find next event
            candidates = []
            if next_arrival < horizon_hours:
                candidates.append(('A', next_arrival))
            if s1_free > t and len(q1) > 0: # Only if there is work or server is currently processing
                # Note: s1_free represents end of current service. If q1 is empty and s1_free > t, 
                # it means server is idle? No, if server is idle, s1_free <= t.
                # If server is busy, s1_free > t.
                candidates.append(('C1', s1_free))
            if s2_free > t and len(q2) > 0:
                candidates.append(('C2', s2_free))
            
            if not candidates:
                # Jump to next arrival if any, or end
                if next_arrival < horizon_hours:
                    # Integrate idle time
                    dt = next_arrival - t
                    # L is 0
                    # Busy is 0
                    t = next_arrival
                    last_t = t
                    continue
                else:
                    break
            
            candidates.sort(key=lambda x: x[1])
            etype, etime = candidates[0]
            
            # Integrate
            dt = etime - last_t
            L_curr = len(q1) + len(q2)
            area_L += L_curr * dt
            
            # Update busy times
            # Server 1 is busy if it is currently serving someone.
            # How do we know if it's serving? 
            # If s1_free > last_t, it was busy during the interval?
            # Better: Track if server is active.
            # Active if s1_free > last_t (meaning the current service ends after the interval start)
            # AND there was a job in service.
            # Simpler: If s1_free > last_t, then server 1 was busy for the whole dt?
            # Not necessarily. If s1_free falls within (last_t, etime), it becomes idle.
            # But our event etime IS s1_free in that case. So if etype=='C1', s1_free==etime.
            # So during (last_t, etime), s1_free > last_t is true.
            # Is it possible s1_free < last_t? Yes, if idle.
            # So: if s1_free > last_t: busy1 += dt
            #     if s2_free > last_t: busy2 += dt
            
            if s1_free > last_t:
                busy1 += dt
            if s2_free > last_t:
                busy2 += dt
                
            t = etime
            last_t = t
            
            if etype == 'A':
                if t >= warmup:
                    arr_count_win += 1
                
                # Sample service time 1
                svc1 = rng.expovariate(mu1)
                q1.append([t, svc1])
                
                # Schedule completion if server free
                if s1_free <= t:
                    s1_free = t + svc1
                # Else, it joins queue. The head of queue determines next C1?
                # Our logic uses s1_free as the time the CURRENT service finishes.
                # When C1 happens, we pop q1, check if new head exists, set s1_free.
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'C1':
                # Complete service at 1
                # Pop head of q1
                if q1:
                    item = q1.pop(0)
                    sys_arr_time, _ = item
                    
                    # Move to Station 2
                    svc2 = rng.expovariate(mu2)
                    q2.append([sys_arr_time, svc2])
                    
                    # Set s2_free if server 2 is available
                    if s2_free <= t:
                        s2_free = t + svc2
                        
                    # Set s1_free for next job in q1 if any
                    if q1:
                        # Next job starts now
                        _, next_svc1 = q1[0]
                        s1_free = t + next_svc1
                    else:
                        s1_free = t # Idle
                        
            elif etype == 'C2':
                # Complete service at 2
                if q2:
                    item = q2.pop(0)
                    sys_arr_time, _ = item
                    
                    # Record departure
                    if t >= warmup:
                        dep_count_win += 1
                        total_sojourn += (t - sys_arr_time)
                        num_dep += 1
                        
                    # Set s2_free for next job in q2 if any
                    if q2:
                        _, next_svc2 = q2[0]
                        s2_free = t + next_svc2
                    else:
                        s2_free = t
        
        # Final integration to horizon?
        # Loop breaks when t >= horizon or no events.
        # If loop broke due to no events before horizon, we need to integrate remaining time.
        if t < horizon_hours:
            dt = horizon_hours - t
            L_curr = len(q1) + len(q2)
            area_L += L_curr * dt
            if s1_free > last_t:
                busy1 += dt
            if s2_free > last_t:
                busy2 += dt
            t = horizon_hours
            
        # Calculate metrics for this seed
        win_len = horizon_hours - warmup
        if win_len <= 0:
            win_len = 1e-9
            
        L_est = area_L / horizon_hours # Average over full horizon? Or window?
        # Prompt: "statistics only accumulated in window after removing first 25% warmup"
        # "Area-type quantities must be integrated before changing state"
        # Usually L is average over the observation window.
        # So L = Area_in_Window / Window_Length.
        # My area_L accumulated over FULL horizon. I need to subtract warmup area.
        
        # Correction: I need to track area specifically in the window.
        # Let's re-run logic mentally: I can just calculate L using the window portion.
        # Easier: Keep two accumulators or reset at warmup.
        # Since I already ran the loop, I'll assume the code above needs modification to separate warmup.
        # However, for brevity and correctness in final output, I will rewrite the inner loop to track window stats separately.
        
        # Re-implementing seed loop cleanly with window separation
        pass 

    # Due to complexity of rewriting twice, I will provide the corrected single-pass code below.
    # It tracks area_L_win, busy1_win, etc.

    results = []
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        q1 = [] # [sys_arr_time, svc1_dur]
        q2 = [] # [sys_arr_time, svc2_dur]
        
        s1_free = 0.0
        s2_free = 0.0
        
        warmup = 0.25 * horizon_hours
        
        # Window accumulators
        area_L_win = 0.0
        busy1_win = 0.0
        busy2_win = 0.0
        total_sojourn_win = 0.0
        num_dep_win = 0
        num_arr_win = 0
        
        last_t = 0.0
        
        while t < horizon_hours:
            candidates = []
            if next_arrival < horizon_hours:
                candidates.append(('A', next_arrival))
            if s1_free > t and len(q1) > 0:
                candidates.append(('C1', s1_free))
