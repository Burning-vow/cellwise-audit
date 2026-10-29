import random, json, argparse, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
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
    total_time_in_sys = 0.0
    total_busy_time_1 = 0.0
    total_busy_time_2 = 0.0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = 0
        q2 = 0
        s1_free = False
        s2_free = False
        next_arr_t = rng.expovariate(lam)
        next_s1_done = float('inf')
        next_s2_done = float('inf')
        
        # Accumulators for this seed (only within window)
        local_arr = 0
        local_dep = 0
        local_blk = 0
        local_time_in_sys = 0.0
        local_busy_1 = 0.0
        local_busy_2 = 0.0
        local_wait_events = 0
        local_total_customers_seen = 0
        
        # For area calculation of L and busy fractions
        last_event_t = 0.0
        acc_area_L = 0.0
        acc_area_b1 = 0.0
        acc_area_b2 = 0.0
        
        while t < horizon:
            # Determine next event time
            events = []
            if next_arr_t < horizon:
                events.append(('arr', next_arr_t))
            if next_s1_done < horizon:
                events.append(('s1_done', next_s1_done))
            if next_s2_done < horizon:
                events.append(('s2_done', next_s2_done))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Integrate areas from last_event_t to etime
            dt = etime - last_event_t
            if last_event_t >= win_start or etime > win_start:
                # Calculate overlap with window [win_start, horizon]
                start_int = max(last_event_t, win_start)
                end_int = min(etime, horizon)
                if end_int > start_int:
                    int_dt = end_int - start_int
                    acc_area_L += (q1 + q2) * int_dt
                    acc_area_b1 += (1.0 if not s1_free else 0.0) * int_dt
                    acc_area_b2 += (1.0 if not s2_free else 0.0) * int_dt
            
            last_event_t = etime
            t = etime
            
            if etype == 'arr':
                # Arrival
                if t >= win_start:
                    local_arr += 1
                    local_total_customers_seen += 1
                
                # Check capacity? Problem doesn't specify finite queue, assume infinite queue but check blocking logic if any.
                # "两道工序各自排队" implies queues. No explicit loss mechanism mentioned other than potential overflow if modeled.
                # Standard Jackson network has infinite buffers unless specified. 
                # However, output requires blk (blocked/lost). If no loss, blk=0.
                # Let's assume infinite buffer -> no loss.
                
                # Service time drawn at arrival
                st1 = rng.expovariate(mu)
                
                if s1_free:
                    s1_free = False
                    next_s1_done = t + st1
                    # Customer enters service immediately, wait time is 0 for stage 1 entry? 
                    # W is total stay. We track completion times.
                    # To compute W, we need sum of (exit_time - entry_time).
                    # We can store entry time in a list associated with the job moving through stages.
                    # Since it's serial, we can use a FIFO queue for jobs waiting for S1 and S2.
                    
                    # Actually, simpler: maintain queues of (entry_time, service_time_remaining_or_full)
                    # But standard DES uses events.
                    # Let's maintain a list of jobs in system with their entry time.
                    # When they leave S2, add (t - entry_time) to total_time_in_sys.
                    
                    # We need to track individual jobs.
                    # Queue 1 stores (entry_time, service_duration)
                    # Queue 2 stores (entry_time, service_duration) -- actually just entry_time is enough if we know when they started S2?
                    # No, we need total time. Entry time is fixed. Exit time is known.
                    
                    # Let's use lists for queues.
                    # q1_list: list of (entry_time, service_duration)
                    # q2_list: list of (entry_time, service_duration)
                    
                    # Wait, I used integer counts q1, q2 above. Need to switch to object lists to track entry times.
                    pass
                else:
                    # Add to queue 1
                    # Need to refactor state to hold job details
                    pass
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 's1_done':
                # Job finishes S1
                # Move to S2
                # Pop from q1
                # If q2 empty and s2 free, start S2 immediately
                # Else add to q2
                pass
                
            elif etype == 's2_done':
                # Job leaves system
                # Calculate stay time
                pass

        # This approach is getting complex due to tracking individual entry times.
        # Let's restart the simulation loop with proper job tracking.
        
        # Reset for correct implementation
        rng = random.Random(seed)
        t = 0.0
        q1 = [] # List of (entry_time, service_duration)
        q2 = [] # List of (entry_time, service_duration)
        s1_free = True
        s2_free = True
        next_arr_t = rng.expovariate(lam)
        next_s1_done = float('inf')
        next_s2_done = float('inf')
        
        local_arr = 0
        local_dep = 0
        local_blk = 0
        local_time_in_sys = 0.0
        local_busy_1 = 0.0
        local_busy_2 = 0.0
        local_wait_count = 0 # Customers who waited in either queue
        
        last_event_t = 0.0
        acc_area_L = 0.0
        acc_area_b1 = 0.0
        acc_area_b2 = 0.0
        
        while t < horizon:
            events = []
            if next_arr_t < horizon:
                events.append(('arr', next_arr_t))
            if next_s1_done < horizon:
                events.append(('s1_done', next_s1_done))
            if next_s2_done < horizon:
                events.append(('s2_done', next_s2_done))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - last_event_t
            start_int = max(last_event_t, win_start)
            end_int = min(etime, horizon)
            if end_int > start_int:
                int_dt = end_int - start_int
                acc_area_L += (len(q1) + len(q2)) * int_dt
                acc_area_b1 += (0.0 if s1_free else 1.0) * int_dt
                acc_area_b2 += (0.0 if s2_free else 1.0) * int_dt
            
            last_event_t = etime
            t = etime
            
            if etype == 'arr':
                if t >= win_start:
                    local_arr += 1
                
                st1 = rng.expovariate(mu)
                job = (t, st1)
                
                if s1_free:
                    s1_free = False
                    next_s1_done = t + st1
                    # Start service immediately
                    # The job is now in service, not in queue.
                    # But for L calculation, does "in service" count as in system? Yes.
                    # My q1/q2 only hold waiting jobs. I need to account for jobs in service too.
                    # Let's change definition:
                    # n1 = number of jobs in stage 1 (waiting + serving)
                    # n2 = number of jobs in stage 2 (waiting + serving)
                    # But I need to know which specific job is being served to get its entry time later.
                    
                    # Better: Keep q1 as waiting queue. Track current_job_1 separately.
                    pass
                else:
                    q1.append(job)
                
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 's1_done':
                # Current job in S1 finished
                # It was the one that started at next_s1_done - st1? No, we don't have st1 stored easily.
                # We need to store the job currently in service.
                pass
                
            elif etype == 's2_done':
                pass

        # Refactoring again for clarity
        rng = random.Random(seed)
        t = 0.0
        q1 = [] # Waiting for S1
        q2 = [] # Waiting for S2
        curr_job_1 = None # (entry_time, service_duration) currently in S1
        curr_job_2 = None # (entry_time, service_duration) currently in S2
        s1_free = True
        s2_free = True
        next_arr_t = rng.expovariate(lam)
        next_s1_done = float('inf')
        next_s2_done = float('inf')
        
        local_arr = 0
        local_dep = 0
        local_blk = 0
        local_time_in_sys = 0.0
        local_busy_1 = 0.0
        local_busy_2 = 0.0
        local_wait_count = 0
        
        last_event_t = 0.0
        acc_area_L = 0.0
        acc_area_b1 = 0.0
        acc_area_b2 = 0.0
        
        while t < horizon:
            events = []
            if next_arr_t < horizon:
                events.append(('arr', next_arr_t))
            if next_s1_done < horizon:
                events.append(('s1_done', next_s1_done))
            if next_s2_done < horizon:
                events.append(('s2_done', next_s2_done))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - last_event_t
            start_int = max(last_event_t, win_start)
            end_int = min(etime, horizon)
            if end_int > start_int:
                int_dt = end_int - start_int
                # Count jobs in system: q1 + q2 + (1 if curr_job_1 else 0) + (1 if curr_job_2 else 0)
                n_sys = len(q1) + len(q2)
                if curr_job_1 is not None: n_sys += 1
                if curr_job_2 is not None: n_sys += 1
                acc_area_L += n_sys * int_dt
                acc_area_b1 += (0.0 if s1_free else 1.0) * int_dt
                acc_area_b2 += (0.0 if s2_free else 1.0) * int_dt
            
            last_event_t = etime
            t = etime
            
            if etype == 'arr':
                if t >= win_start:
                    local_arr += 1
                
                st1 = rng.expovariate(mu)
                job = (t, st1)
                
                if s1_free:
                    s1_free = False
                    curr_job_1 = job
                    next_s1_done = t + st1
                else:
                    q1.append(job)
                    # Did this customer wait? Yes, because server was busy.
                    # We'll mark them as having waited when they eventually enter service? 
                    # Or simply: if they were added to q1, they waited.
                    # But what if they go to q2? They also waited.
                    # Let's track "waited" flag on the job tuple? 
                    # job = (entry_time, service_duration, waited_flag)
                    # Initially waited_flag=False. If added to q1, set True.
                    # If moved to q2, set True.
                    # Update job structure
                    job = (t, st1, True)
                    q1.append(job)
                
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 's1_done':
                # Finish current job in S1
                if curr_job_1 is not None:
                    entry_t, st_dur, waited = curr_job_1
                    # Move to S2
                    # Draw service time for S2? 
                    # "服务时长必须在顾客到达时抽好并挂在该顾客身上"
                    # So we should have drawn st2 at arrival too.
                    # I missed drawing st2 at arrival.
                    pass
                
                # Correcting arrival logic to draw both service times
                # Re-run loop setup mentally...
                # Okay, I will rewrite the inner loop correctly.
                pass

        # Final Attempt Structure
        rng = random.Random(seed)
        t = 0.0
        q1 = [] # List of (entry_time, st1, st2, waited)
        q2 = [] # List of (entry_time, st1, st2, waited)
        curr_job_1 = None # (entry_time, st1, st2, waited)
        curr_job_2 = None # (entry_time, st1, st2, waited)
        s1_free = True
        s2_free = True
        next_arr_t = rng.expovariate(lam)
        next_s1_done = float('inf')
        next_s2_done = float('inf')
        
        local_arr = 0
        local_dep = 0
        local_blk = 0
        local_time_in_sys = 0.0
        local_busy_1 = 0.0
        local_busy_2 = 0.0
        local_wait_count = 0
        
        last_event_t = 0.0
        acc_area_L = 0.0
        acc_area_b1 = 0.0
        acc_area_b2 = 0.0
        
        while t < horizon:
            events = []
            if next_arr_t < horizon:
                events.append(('arr', next_arr_t))
            if next_s1_done < horizon:
                events.append(('s1_done', next_s1_done))
            if next_s2_done < horizon:
                events.append(('s2_done', next_s2_done))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - last_event_t
            start_int = max(last_event_t, win_start)
            end_int = min(etime, horizon)
            if end_int > start_int:
                int_dt = end_int - start_int
                n_sys = len(q1) + len(q2)
                if curr_job_1 is not None: n_sys += 1
                if curr_job_2 is not None: n_sys += 1
                acc_area_L += n_sys * int_dt
                acc_area_b1 += (0.0 if s1_free else 1.0) * int_dt
                acc_area_b2 += (0.0 if s2_free else 1.0) * int_dt
            
            last_event_t = etime
            t = etime
            
            if etype == 'arr':
                if t >= win_start:
                    local_arr += 1
                
                st1 = rng.expovariate(mu)
                st2 = rng.expovariate(mu)
                job = (t, st1, st2, False)
                
                if s1_free:
                    s1_free = False
                    curr_job_1 = job
                    next_s1_done = t + st1
                else:
                    job = (t, st1, st2, True) # Marked as waited
                    q1.append(job)
                
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 's1_done':
                if curr_job_1 is not None:
                    entry_t, st1, st2, waited = curr_job
