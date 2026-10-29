import sys, json, random, math
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[k] = v
            i += 2
        else:
            i += 1
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 100.0)) # hours
    S = int(args.get('seed-start', 42))
    pert = args.get('pert', 'none')
    
    lam_base = 6.0 # per hour
    mu1_base = 60.0 / 7.5 # per hour
    mu2_base = 60.0 / 5.0 # per hour
    
    lam = lam_base
    mu1 = mu1_base
    mu2 = mu2_base
    
    if pert == 'lam_up': lam *= 1.1
    elif pert == 'mu_up': mu1 *= 1.1; mu2 *= 1.1
    elif pert == 'c_up': pass # Cost not used in this metric calculation directly
    
    time_unit = "hour"
    horizon_hours = H
    warmup_ratio = 0.25
    start_stat_time = horizon_hours * warmup_ratio
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_arr_count = 0
    all_dep_count = 0
    all_blk_count = 0
    all_busy1_time = 0.0
    all_busy2_time = 0.0
    all_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for s_idx in range(N):
        current_seed = S + s_idx
        rng = random.Random(current_seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue1 = deque() # (arrival_time, service_time)
        queue2 = deque() # (arrival_time_to_q2, service_time)
        server1_free_at = 0.0
        server2_free_at = 0.0
        
        # Statistics accumulators for this seed
        local_L_area = 0.0
        local_W_sum = 0.0
        local_arr_count = 0
        local_dep_count = 0
        local_blk_count = 0
        local_busy1_time = 0.0
        local_busy2_time = 0.0
        local_wait_count = 0
        
        last_event_time = 0.0
        current_in_system = 0 # L(t) approximation via area integration
        
        # We need to track events. 
        # Events: Arrival, Service Complete 1, Service Complete 2
        
        # Helper to add event to priority queue? 
        # Since we only have 3 types of future events potentially active, 
        # we can just compare times. But queues grow. 
        # Better: Use a heap or simple list of scheduled events.
        # Given single servers, at most 1 completion event per server is pending.
        # So max 3 events in the system timeline: Next Arrival, Next Comp1, Next Comp2.
        
        events = [] # (time, type, data)
        # Type 0: Arrival, 1: Comp1, 2: Comp2
        
        def push_event(time, typ, data=None):
            events.append((time, typ, data))
            
        push_event(next_arrival, 0)
        
        while t < horizon_hours:
            if not events: break
            
            # Find next event
            events.sort(key=lambda x: x[0])
            next_t, ev_type, ev_data = events.pop(0)
            
            if next_t > horizon_hours:
                break
                
            dt = next_t - t
            
            # Update Area for L (Number in system)
            # Number in system = len(queue1) + len(queue2) + (1 if server1 busy else 0) + (1 if server2 busy else 0)
            # But we need to know who is currently being served.
            # Let's maintain counts explicitly.
            
            n_sys = len(queue1) + len(queue2)
            if t >= server1_free_at and t < server1_free_at + 1e-9: # Just finished? No, check state before update
                 pass
            
            # Recalculate n_sys based on current state BEFORE processing event
            # Server 1 is busy if there is someone in service. 
            # We don't store "in-service" separately, it's implicit.
            # If queue1 is empty but server1_free_at > t, someone is in service.
            # Actually, simpler: Track number of jobs in system.
            
            # Let's restart logic with explicit job tracking.
            # Jobs are objects/dicts.
            
            # Reset loop structure for clarity within seed
            pass 

        # Re-implementing simulation loop cleanly inside seed loop
        
        # State
        t = 0.0
        q1 = deque() # Jobs waiting for S1
        q2 = deque() # Jobs waiting for S2
        job_s1 = None # Job currently in S1
        job_s2 = None # Job currently in S2
        
        next_arr_t = rng.expovariate(lam)
        comp1_t = float('inf')
        comp2_t = float('inf')
        
        # Stats
        l_area = 0.0
        w_sum = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        b1_time = 0.0
        b2_time = 0.0
        wait_cnt = 0
        
        prev_t = 0.0
        
        while t < horizon_hours:
            # Determine next event time
            candidates = [next_arr_t, comp1_t, comp2_t]
            min_t = min(candidates)
            
            if min_t > horizon_hours:
                # Advance to end
                dt = horizon_hours - t
                # Calculate L during this interval
                n_now = len(q1) + len(q2) + (1 if job_s1 else 0) + (1 if job_s2 else 0)
                l_area += n_now * dt
                t = horizon_hours
                break
            
            dt = min_t - t
            if dt > 0:
                n_now = len(q1) + len(q2) + (1 if job_s1 else 0) + (1 if job_s2 else 0)
                l_area += n_now * dt
                
                # Accumulate busy times
                if job_s1: b1_time += dt
                if job_s2: b2_time += dt
                
            t = min_t
            
            # Process Event
            if abs(t - next_arr_t) < 1e-9:
                # Arrival
                arr_cnt += 1
                # Generate service times immediately
                st1 = rng.expovariate(mu1)
                st2 = rng.expovariate(mu2)
                job = {'arr_t': t, 'st1': st1, 'st2': st2}
                
                if job_s1 is None:
                    job_s1 = job
                    comp1_t = t + st1
                else:
                    q1.append(job)
                    
                next_arr_t = t + rng.expovariate(lam)
                
            elif abs(t - comp1_t) < 1e-9:
                # Completion of Stage 1
                job = job_s1
                job_s1 = None
                comp1_t = float('inf')
                
                # Move to Stage 2
                if job_s2 is None:
                    job_s2 = job
                    comp2_t = t + job['st2']
                else:
                    q2.append(job)
                    
                # Start next from Q1 if available
                if q1:
                    next_job = q1.popleft()
                    job_s1 = next_job
                    comp1_t = t + next_job['st1']
                    
            elif abs(t - comp2_t) < 1e-9:
                # Completion of Stage 2
                job = job_s2
                job_s2 = None
                comp2_t = float('inf')
                
                # Departure
                dep_cnt += 1
                stay_time = t - job['arr_t']
                w_sum += stay_time
                
                # Check if waited (simplified: if arrived and didn't go straight to service? 
                # Or if queue was non-empty upon arrival? 
                # Definition of p_wait usually implies probability that an arriving customer has to wait.
                # We tracked this at arrival. Let's fix arrival logic to count waits.)
                
                # Start next from Q2 if available
                if q2:
                    next_job = q2.popleft()
                    job_s2 = next_job
                    comp2_t = t + next_job['st2']
        
        # Post-process stats for this seed
        win_len = horizon_hours - start_stat_time
        if win_len <= 0: win_len = 1e-9
        
        # Filter by window? The problem says "statistics accumulated only after removing first 25% warmup".
        # My loop above accumulates over full horizon. I need to reset accumulators at start_stat_time.
        # Refactoring needed: Run simulation, but only record stats when t >= start_stat_time.
        
        # Let's re-run the inner loop logic with conditional accumulation.
        
        # Reset for correct windowing
        l_area_w = 0.0
        w_sum_w = 0.0
        arr_cnt_w = 0
        dep_cnt_w = 0
        blk_cnt_w = 0
        b1_time_w = 0.0
        b2_time_w = 0.0
        wait_cnt_w = 0
        
        # Need to replay or simulate again? Simulating again is safer/cleaner code-wise given constraints.
        # But efficiency... N is small. Let's just do one pass with checks.
        
        # Restart simulation state for this seed properly with windowing
        t = 0.0
        q1.clear(); q2.clear()
        job_s1 = None; job_s2 = None
        next_arr_t = rng.expovariate(lam) # New RNG stream? No, reuse same rng sequence? 
        # To ensure reproducibility per seed, I should use a fresh RNG instance or save state.
        # Using fresh Random(current_seed) is best.
        
        rng = random.Random(current_seed)
        t = 0.0
        q1 = deque()
        q2 = deque()
        job_s1 = None
        job_s2 = None
        next_arr_t = rng.expovariate(lam)
        comp1_t = float('inf')
        comp2_t = float('inf')
        
        l_area_w = 0.0
        w_sum_w = 0.0
        arr_cnt_w = 0
        dep_cnt_w = 0
        blk_cnt_w = 0
        b1_time_w = 0.0
        b2_time_w = 0.0
        wait_cnt_w = 0
        
        while t < horizon_hours:
            candidates = [next_arr_t, comp1_t, comp2_t]
            min_t = min(candidates)
            
            if min_t > horizon_hours:
                dt = horizon_hours - t
                if t >= start_stat_time:
                    n_now = len(q1) + len(q2) + (1 if job_s1 else 0) + (1 if job_s2 else 0)
                    l_area_w += n_now * dt
                    if job_s1: b1_time_w += dt
                    if job_s2: b2_time_w += dt
                t = horizon_hours
                break
            
            dt = min_t - t
            if dt > 0 and t >= start_stat_time:
                n_now = len(q1) + len(q2) + (1 if job_s1 else 0) + (1 if job_s2 else 0)
                l_area_w += n_now * dt
                if job_s1: b1_time_w += dt
                if job_s2: b2_time_w += dt
            
            t = min_t
            
            if abs(t - next_arr_t) < 1e-9:
                if t >= start_stat_time:
                    arr_cnt_w += 1
                    # Did they wait?
                    if job_s1 is not None or len(q1) > 0:
                        wait_cnt_w += 1
                
                st1 = rng.expovariate(mu1)
                st2 = rng.expovariate(mu2)
                job = {'arr_t': t, 'st1': st1, 'st2': st2}
                
                if job_s1 is None:
                    job_s1 = job
                    comp1_t = t + st1
                else:
                    q1.append(job)
                    
                next_arr_t = t + rng.expovariate(lam)
                
            elif abs(t - comp1_t) < 1e-9:
                job = job_s1
                job_s1 = None
                comp1_t = float('inf')
                
                if job_s2 is None:
                    job_s2 = job
                    comp2_t = t + job['st2']
                else:
                    q2.append(job)
                    
                if q1:
                    next_job = q1.popleft()
                    job_s1 = next_job
                    comp1_t = t + next_job['st1']
                    
            elif abs(t - comp2_t) < 1e-9:
                job = job_s2
                job_s2 = None
                comp2_t = float('inf')
                
                if t >= start_stat_time:
                    dep_cnt_w += 1
                    stay_time_min = (t - job['arr_t']) * 60.0 # Convert hours to minutes
                    w_sum_w += stay_time_min
                    
                if q2:
                    next_job = q2.popleft()
                    job_s2 = next_job
                    comp2_t = t + next_job['st2']

        # Calculate metrics for this seed
        win_duration = horizon_hours - start_stat_time
        if win_duration <= 0: win_duration = 1e-9
        
        avg_L = l_area_w / win_duration
        avg_W = w_sum_w / dep_cnt_w if dep_cnt_w > 0 else 0.0
        
        busy_frac_1 = b1_time_w / win_duration
        busy_frac_2 = b2_time_w / win_duration
        avg_busy_frac = (busy_frac_1 + busy_frac_2) / 2.0 # Or sum? Usually utilization per server. 
        # Output key is busy_frac. Ambiguous. Let's assume average utilization across servers or total?
        # Standard is often per-server. But key is singular. Let's provide average of both.
        
        p_loss = blk_cnt_w / arr_cnt_w if arr_cnt_w > 0 else 0.0
        p_wait = wait_cnt_w / arr_cnt_w if arr_cnt_w > 0 else 0.0
        
        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W)
        per_seed_busy_frac.append(avg_busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)
        seed_list.append(current_seed)
        
        all_L_area += l_area_w
        all_W_sum += w_sum_w
        all_arr_count += arr_cnt_w
        all_dep_count += dep_cnt_w
        all_blk_count += blk_cnt_w
        all_busy1_time += b1_time_w
        all_busy2_time += b2_time_w
        all_wait_count += wait_cnt_w

    # Global Aggregation
    total_win_time = N * (horizon_hours - start_stat_time)
    if total_win_time <= 0: total_win_time = 1e-9
    
    global_L = all_L_area / total_win_time
    global_W = all_W_sum / all_dep_count if all_dep_count > 0 else 0.0
    
    global_busy_frac = (all_busy1_time + all_busy2_time) / (2 * total_win_time)
    global_p_loss = all_blk_count / all_arr_count if all_arr_count > 0 else 0.0
    global_p_wait = all_wait_count / all_arr_count if all_arr_count > 0 else 0.0
    
    dep_rate = all_dep_count / total_win_time # per hour
    
    result = {
        "L": round(global_L, 4),
        "W": round(global_W, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(horizon_hours - start_stat_time, 4),
        "arr": round(all_arr_count / N, 4),
        "blk": round(all_blk_count / N, 4),
        "busy_frac": round(global_busy_frac, 4),
        "busy_util": round(global_busy_frac, 4),
        "dep": round(all_dep_count / N, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(all_dep_count / total_win_time, 4),
        "p_loss": round(global_p_loss, 4),
        "p_wait": round(global_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in
