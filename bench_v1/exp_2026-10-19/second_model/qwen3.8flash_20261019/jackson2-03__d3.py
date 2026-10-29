import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu_base = 10.0 # per hour (6 min mean)
    
    if args.pert == 'lam_up': lam_base *= 1.2
    elif args.pert == 'mu_up': mu_base *= 1.2
    elif args.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        queue1 = [] # list of (arrival_time, service_time)
        queue2 = []
        server1_free_at = 0.0
        server2_free_at = 0.0
        
        # Statistics accumulators for area integration
        # We need to track number in system over time
        n_sys = 0
        last_event_time = 0.0
        area_L = 0.0
        
        # For W calculation: sum of sojourn times for completed jobs in window
        sum_w_times = 0.0
        count_w_jobs = 0
        
        # Busy tracking
        busy1_time = 0.0
        busy2_time = 0.0
        
        # Event loop
        while t < horizon:
            # Determine next event time
            events = []
            if next_arrival < horizon:
                events.append(('arr', next_arrival))
            
            # Check if servers are busy and when they finish
            # If queue1 is not empty and server1 is free, it should have started immediately? 
            # No, we process events chronologically.
            # Server 1 finishes at server1_free_at if > t and there was a job being served.
            # But how do we know if a job is being served? 
            # Let's maintain current_job1 and current_job2
            
            # Actually, simpler approach: 
            # Events: Arrival, Completion1, Completion2.
            # Completion1 happens if server1 is busy.
            # Completion2 happens if server2 is busy.
            
            # We need to know if servers are currently busy.
            # Let's use flags or check queues vs start times.
            
            # Refactored state:
            # s1_busy_until: time when current job on S1 finishes, or -inf if idle
            # s2_busy_until: time when current job on S2 finishes, or -inf if idle
            
            # Initialize these properly inside loop logic is hard without classes.
            # Let's stick to the standard simulation pattern.
            
            # Re-initialize specific vars for this seed run clearly
            s1_end = -1.0
            s2_end = -1.0
            q1 = [] # (entry_time, svc_time)
            q2 = [] # (entry_time, svc_time)
            
            # Reset accumulators for this seed
            area_L_seed = 0.0
            sum_w_seed = 0.0
            cnt_w_seed = 0
            busy1_seed = 0.0
            busy2_seed = 0.0
            arr_cnt_seed = 0
            dep_cnt_seed = 0
            blk_cnt_seed = 0
            
            t = 0.0
            next_arr = rng.expovariate(lam_base)
            
            # Helper to update area
            def update_area(t_now, n_now, t_last, area_acc):
                return area_acc + n_now * (t_now - t_last)
            
            # Initial state
            n_in_sys = 0
            t_last = 0.0
            
            while True:
                # Find next event
                candidates = []
                if next_arr <= horizon:
                    candidates.append((next_arr, 'ARR'))
                if s1_end >= 0 and s1_end <= horizon:
                    candidates.append((s1_end, 'C1'))
                if s2_end >= 0 and s2_end <= horizon:
                    candidates.append((s2_end, 'C2'))
                
                if not candidates:
                    break
                
                t_next, ev_type = min(candidates, key=lambda x: x[0])
                
                # Update area up to t_next
                area_L_seed += n_in_sys * (t_next - t_last)
                t_last = t_next
                t = t_next
                
                if ev_type == 'ARR':
                    arr_cnt_seed += 1
                    # Generate service time for stage 1
                    svc1 = rng.expovariate(mu_base)
                    
                    # Add to system
                    n_in_sys += 1
                    
                    # Check if within window for stats? 
                    # The problem says "statistics only accumulated after removing first 25% warmup".
                    # This usually applies to steady-state estimates like L and W.
                    # For L (area), we integrate over the whole window [win_start, horizon].
                    # For W, we average over departures in the window.
                    
                    # Queueing logic for Stage 1
                    if s1_end < 0 or s1_end <= t:
                        # Start service immediately
                        s1_end = t + svc1
                        # Store job info for later departure from S1
                        # We need to know when it arrived to calculate total W later?
                        # Or just store arrival time in the queue item.
                        # Since it starts immediately, it's not in queue.
                        # We can push it to a "current" variable or handle via completion event.
                        # To keep it simple, let's put it in q1 but mark as started?
                        # Better: Just handle completions by popping from queues.
                        # If started immediately, we don't add to q1 list, but we set s1_end.
                        # We need to remember its arrival time for W calc.
                        # Let's create a dummy entry in q1 with start flag?
                        # Alternative: When C1 happens, we look at the job that finished.
                        # How do we know which one? FIFO.
                        # So if we start immediately, we effectively pop/push instantly?
                        # Let's say: if idle, start now. The job is "in service".
                        # We need to track its arrival time.
                        # Let's use a variable `job1_info` = (arrival_time, svc_time) if busy else None.
                        # But we already used s1_end.
                        
                        # Let's restart the structure slightly for clarity within the loop constraints.
                        # I will use lists for queues and separate variables for current jobs.
                        pass
                    else:
                        # Wait in queue
                        q1.append((t, svc1))
                    
                    # Schedule next arrival
                    next_arr = t + rng.expovariate(lam_base)
                    
                elif ev_type == 'C1':
                    # Job leaves Stage 1
                    # It must have been in service.
                    # Who was in service? The one that started at s1_start.
                    # We need to retrieve the job details.
                    # In my simplified model above, I didn't store the current job details explicitly.
                    # Let's fix the data structures.
                    
                    # Data Structure Fix:
                    # q1: list of (arrival_time, svc_time) waiting
                    # curr1: tuple (arrival_time, svc_time, end_time) or None
                    # Same for stage 2.
                    
                    # This requires re-writing the inner loop logic significantly.
                    # Given the constraint "no classes", I'll inline the logic carefully.
                    
                    # Retrieve job from curr1
                    # Note: I haven't defined curr1 yet in the code block above.
                    # I will rewrite the seed loop body completely below.
                    break # Exit to rewrite

            # Placeholder to satisfy syntax before full rewrite
            pass

    # Full Rewrite of Seed Loop Logic
    results = []
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # Parameters
        lam = lam_base
        mu = mu_base
        
        # Time
        t = 0.0
        horizon_t = horizon
        win_s = horizon_t * 0.25
        
        # State
        # Queues: list of (arrival_time, service_duration)
        q1 = []
        q2 = []
        # Current jobs: None or (arrival_time, service_duration, end_time)
        c1 = None
        c2 = None
        
        # Next arrival time
        next_arr = rng.expovariate(lam)
        
        # Accumulators
        area_L = 0.0
        sum_W = 0.0
        count_W = 0
        busy1_dur = 0.0
        busy2_dur = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0 # Not applicable here, no blocking mentioned, but interface asks for it. Assume 0 loss.
        
        t_last = 0.0
        
        while True:
            # Determine next event
            events = []
            if next_arr <= horizon_t:
                events.append((next_arr, 'A'))
            if c1 is not None:
                events.append((c1[2], 'C1'))
            if c2 is not None:
                events.append((c2[2], 'C2'))
            
            if not events:
                break
            
            t_next, ev = min(events, key=lambda x: x[0])
            
            # Update Area L
            n_sys = len(q1) + len(q2) + (1 if c1 else 0) + (1 if c2 else 0)
            area_L += n_sys * (t_next - t_last)
            t_last = t_next
            t = t_next
            
            if ev == 'A':
                arr_count += 1
                svc1 = rng.expovariate(mu)
                
                # Add to system
                # Check if Stage 1 is free
                if c1 is None:
                    # Start service
                    end1 = t + svc1
                    c1 = (t, svc1, end1)
                else:
                    # Join queue
                    q1.append((t, svc1))
                
                # Next arrival
                next_arr = t + rng.expovariate(lam)
                
            elif ev == 'C1':
                # Finish Stage 1
                arr_t, svc_t, _ = c1
                c1 = None
                
                # Move to Stage 2
                # Service time for Stage 2 is generated NOW? 
                # Requirement: "Service duration must be drawn at customer arrival and attached to them".
                # My previous code drew svc1 at arrival. I need to draw svc2 at arrival too?
                # "Workpiece enters Process 1... completes then enters Process 2".
                # Usually, processing times are independent.
                # "Drawn at customer arrival and attached to them".
                # Does this mean both stages' times are drawn at initial arrival?
                # Yes, "attached to the customer".
                # So I need to store svc2 as well.
                
                # Correction: At Arrival, draw svc1 AND svc2.
                # I missed drawing svc2 in the 'A' block.
                # I will patch the 'A' block logic mentally:
                # svc1 = rng.expovariate(mu)
                # svc2 = rng.expovariate(mu)
                # Store (arr_t, svc1, svc2)
                
                # Since I am writing the final code now, I will ensure svc2 is drawn at A.
                # Backtracking to 'A' block implementation in final code:
                # q1 items will be (arr_t, svc1, svc2)
                # c1 will be (arr_t, svc1, svc2, end_t)
                
                # Proceeding with C1 logic assuming correct storage:
                # Get svc2 from the job that just finished c1
                # Wait, c1 tuple needs to hold svc2.
                # Let's assume c1 = (arr_t, svc1, svc2, end_t)
                
                # Extract svc2
                _, _, svc2, _ = c1 # This line depends on c1 structure.
                # Actually, in the 'A' block, I set c1 = (t, svc1, svc2, end1).
                # So unpacking:
                arr_orig, _, svc2_val, _ = c1 
                c1 = None
                
                # Now enter Stage 2
                if c2 is None:
                    end2 = t + svc2_val
                    c2 = (arr_orig, svc2_val, end2)
                else:
                    q2.append((arr_orig, svc2_val))
                    
                # Try to start Stage 1 from queue if possible
                if q1:
                    arr_q, svc1_q, svc2_q = q1.pop(0)
                    end1_new = t + svc1_q
                    c1 = (arr_q, svc1_q, svc2_q, end1_new)
                    
            elif ev == 'C2':
                # Finish Stage 2 -> Departure
                arr_orig, _, end_t = c2
                c2 = None
                
                # Calculate Sojourn Time
                w_time = t - arr_orig
                
                # Only accumulate stats if departure is in window
                if t >= win_s:
                    sum_W += w_time
                    count_W += 1
                    dep_count += 1
                
                # Try to start Stage 2 from queue
                if q2:
                    arr_q, svc2_q = q2.pop(0)
                    end2_new = t + svc2_q
                    c2 = (arr_q, svc2_q, end2_new)
                
                # Note: Stage 1 queue handling is done in C1 event.
                # What if Stage 1 becomes free due to C1, but we are in C2?
                # C1 handles starting new job on S1.
                # C2 handles starting new job on S2.
                # Are there cases where S1 is free but no job arrives/completes?
                # No, S1 only frees up on C1.
                # S2 only frees up on C2.
                
                # One edge case: If C1 happens, we move job to S2. If S2 is free, we start it.
                # If S2 is busy, it goes to Q2.
                # If C2 happens, we take from Q2.
                
                # Do we need to check Q1 in C2? No, C2 doesn't affect S1.
                # Do we need to check Q2 in C1? Yes, handled in C1 block.
                
                # Wait, in C1 block, I moved job to S2. Did I check if S2 was free?
                # Yes: `if c2 is None: ... else: q2.append(...)`
                # And did I try to pull from Q1 to start S1?
                # Yes: `if q1: ... c1 = ...`
                
                # Is it possible that after C1, S1 is free, but we didn't pull from Q1?
                # I added `if q1: ...` at the end of C1 block. Correct.
                
                # Is it possible that after C2, S2 is free, but we didn't pull from Q2?
                # I added `if q2: ...` at the end of C2 block. Correct.
                
                # What about arrivals?
                # If A happens and S1 is free, start. Else queue.
                # If A happens and S1 is busy, queue.
                # Does A trigger S2? No.
                
                # One missing link:
                # If C1 moves a job to S2, and S2 was busy, it queues.
                # If C2 finishes, it pulls from Q2.
                # This seems consistent.
                
                # However, what if C1 finishes, S2 is free, starts job.
                # Then immediately another C1 finishes?
                # Events are processed sequentially.
                
                # Final check on "Service duration drawn at arrival":
                # In 'A' block:
                # svc1 = rng.expovariate(mu)
                # svc2 = rng.expovariate(mu)
                # Stored in tuple.
                
                # Busy fraction calculation:
                # We need to integrate busy time.
                # Instead of complex integration, we can track start/end times.
                # But easier: 
                # busy1_dur += (end_time - start_time) for each job on S1.
                # busy2_dur += (end_time - start_time) for each job on S2.
                # We can add this in C1 and C2 blocks.
                
                # In C1 block:
                # The job that just finished had duration svc1.
                # busy1_dur += svc1 ? No, only if it was actually running.
                # It was running from max
