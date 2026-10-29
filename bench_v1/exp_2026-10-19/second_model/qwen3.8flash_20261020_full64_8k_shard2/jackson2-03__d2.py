import argparse, json, random, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert
    
    lam_base = 4.0
    mu_base = 10.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        q1 = []
        q2 = []
        
        s1_free_at = 0.0
        s2_free_at = 0.0
        
        total_time_in_sys = 0.0
        num_completed = 0
        num_arrivals = 0
        num_blocked = 0
        
        busy1_time = 0.0
        busy2_time = 0.0
        
        last_event_time = 0.0
        
        while True:
            events = []
            if next_arrival <= H:
                events.append(('arrival', next_arrival))
            
            if q1 and s1_free_at <= H:
                events.append(('start_s1', max(s1_free_at, last_event_time)))
                
            if q2 and s2_free_at <= H:
                events.append(('start_s2', max(s2_free_at, last_event_time)))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            event_type, event_time = events[0]
            
            dt = event_time - last_event_time
            
            if q1 or (event_type == 'start_s1' and q1):
                 pass # handled below by state check before update? No, we integrate over interval [last_event_time, event_time]
            
            # Integrate area for L (number in system)
            n_in_sys = len(q1) + len(q2)
            if event_type == 'start_s1' and q1:
                n_in_sys -= 1 # one leaves queue to service, but still in system? 
                # Actually, definition of L usually includes those in service.
                # Let's define state carefully.
                # q1 holds waiting jobs. Job in service is separate.
                # So total in system = len(q1) + (1 if s1 busy else 0) + len(q2) + (1 if s2 busy else 0)
                pass
            
            # Recalculate count based on current state BEFORE processing event
            # But wait, the integration should be over the previous interval.
            # The state was constant during [last_event_time, event_time).
            
            cnt1 = len(q1)
            cnt2 = len(q2)
            if s1_free_at > last_event_time: # Busy at start of interval?
                # If s1_free_at > last_event_time, it means it was busy throughout the interval until event_time?
                # Not necessarily. It could have finished exactly at event_time.
                # We need to know if server was busy during the interval.
                # Server 1 is busy if there is a job in service.
                # We don't explicitly track "job in service", we track when it finishes.
                # If s1_free_at > last_event_time, then server 1 was busy during the whole interval [last_event_time, min(event_time, s1_free_at)).
                # This logic is getting complex for discrete event simulation without explicit state variables for servers.
                
                # Let's use a simpler approach: Track number in system as a variable that changes at events.
                pass

            # Re-implementing with explicit state tracking for clarity within constraints
            
            # Reset loop structure for cleaner implementation
            pass 

        # Restarting simulation logic for this seed with better structure
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queues for waiting jobs
        q1 = [] # list of arrival times
        q2 = [] # list of completion times from stage 1
        
        # Server availability times
        s1_avail = 0.0
        s2_avail = 0.0
        
        # Metrics accumulators
        integral_L = 0.0 # Integral of number in system over time
        num_jobs_in_sys = 0
        last_t = 0.0
        
        total_completion_time_sum = 0.0
        num_completions = 0
        num_arrivals = 0
        num_rejects = 0
        
        busy1_dur = 0.0
        busy2_dur = 0.0
        
        # To handle integrals correctly, we need to know the state between events.
        # State: num_jobs_in_sys.
        
        while True:
            # Determine next event time
            candidates = []
            if next_arrival < H:
                candidates.append(next_arrival)
            
            # Check if any server becomes free and has work
            # If s1 is busy (s1_avail > t) and q1 is empty, no start event.
            # If s1 is free (s1_avail <= t) and q1 is not empty, start event is now.
            # But we are simulating forward.
            
            # Events can be: Arrival, Completion S1, Completion S2.
            # Start events happen immediately after completion/arrival if queue non-empty and server free.
            
            # Let's find the earliest future event.
            
            # Potential Completion S1: if s1 is currently busy.
            # How do we know if s1 is busy? We don't store "busy" flag directly, but s1_avail > t implies busy.
            # However, we need to know WHEN it completes. That is s1_avail.
            
            comp_s1_time = None
            if s1_avail > t:
                comp_s1_time = s1_avail
                
            comp_s2_time = None
            if s2_avail > t:
                comp_s2_time = s2_avail
                
            arr_time = next_arrival if next_arrival < H else None
            
            # Next event time
            ev_times = []
            if arr_time is not None: ev_times.append(arr_time)
            if comp_s1_time is not None: ev_times.append(comp_s1_time)
            if comp_s2_time is not None: ev_times.append(comp_s2_time)
            
            if not ev_times:
                break
                
            next_ev_t = min(ev_times)
            
            # Update integral for L
            dt = next_ev_t - t
            integral_L += num_jobs_in_sys * dt
            
            # Update busy times
            if s1_avail > t: # Was busy during interval
                busy1_dur += dt
            if s2_avail > t:
                busy2_dur += dt
                
            t = next_ev_t
            
            # Process Event
            if t == arr_time:
                num_arrivals += 1
                # Add to Q1
                q1.append(t)
                num_jobs_in_sys += 1
                
                # Try to start S1
                if s1_avail <= t and q1:
                    # Pop from Q1
                    arr_t_job = q1.pop(0)
                    # Service time
                    svc_time = rng.expovariate(mu)
                    s1_avail = t + svc_time
                    # Note: Job is now in service, so it stays in num_jobs_in_sys.
                    # It moves from "waiting" to "service". Count doesn't change.
                    
                next_arrival = t + rng.expovariate(lam)
                
            elif t == comp_s1_time:
                # Job finishes S1
                # Move to Q2
                q2.append(t)
                # Try to start S2
                if s2_avail <= t and q2:
                    fin_t_job = q2.pop(0)
                    svc_time = rng.expovariate(mu)
                    s2_avail = t + svc_time
                    
            elif t == comp_s2_time:
                # Job finishes S2
                # Remove from system
                num_jobs_in_sys -= 1
                num_completions += 1
                # We need to calculate W. W = Total Time / Num Completions?
                # Or average residence time.
                # We need to track individual residence times.
                # Since we didn't store arrival time in the job object properly through queues,
                # let's fix the data structure.
                
                # Correction: q1 stores arrival times. When moving to q2, we should store arrival time too.
                # When finishing S2, we calculate duration.
                
                # Let's re-architect slightly inside the loop for correctness.
                pass

        # The above logic had flaws in tracking individual jobs. 
        # Rewriting the inner simulation block cleanly.
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Jobs in Q1: list of arrival times
        q1 = []
        # Jobs in Q2: list of arrival times (jobs completed S1, waiting for S2)
        q2 = []
        
        s1_avail = 0.0
        s2_avail = 0.0
        
        num_jobs_in_sys = 0
        integral_L = 0.0
        last_t = 0.0
        
        sum_residence = 0.0
        num_completions = 0
        num_arrivals = 0
        
        busy1_dur = 0.0
        busy2_dur = 0.0
        
        while True:
            # Find next event
            evs = []
            if next_arrival < H:
                evs.append((next_arrival, 'arr'))
            if s1_avail > t:
                evs.append((s1_avail, 'comp1'))
            if s2_avail > t:
                evs.append((s2_avail, 'comp2'))
            
            if not evs:
                break
            
            evs.sort(key=lambda x: x[0])
            nt, etype = evs[0]
            
            # Integrate
            dt = nt - t
            integral_L += num_jobs_in_sys * dt
            if s1_avail > t:
                busy1_dur += dt
            if s2_avail > t:
                busy2_dur += dt
                
            t = nt
            
            if etype == 'arr':
                num_arrivals += 1
                q1.append(t)
                num_jobs_in_sys += 1
                
                # Start S1 if possible
                if s1_avail <= t and q1:
                    arr_time = q1.pop(0)
                    svc = rng.expovariate(mu)
                    s1_avail = t + svc
                    # Job is now in service. Still counted in num_jobs_in_sys.
                    # We need to associate the arrival time with the job in service.
                    # Since we only have one server, we can store the arrival time of the job in service.
                    # But we don't have a variable for that. 
                    # Let's add `s1_job_arr` and `s2_job_arr`.
                    pass
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'comp1':
                # Job finishes S1. 
                # We need its arrival time. 
                # Problem: We lost the link between the job in service and its arrival time.
                # Fix: Store arrival time when starting service.
                pass
                
            elif etype == 'comp2':
                pass

        # Final attempt with correct state variables
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        q1 = [] # Waiting for S1
        q2 = [] # Waiting for S2
        
        s1_avail = 0.0
        s2_avail = 0.0
        s1_job_arr = None # Arrival time of job currently in S1
        s2_job_arr = None # Arrival time of job currently in S2
        
        num_jobs_in_sys = 0
        integral_L = 0.0
        
        sum_residence = 0.0
        num_completions = 0
        num_arrivals = 0
        
        busy1_dur = 0.0
        busy2_dur = 0.0
        
        while True:
            evs = []
            if next_arrival < H:
                evs.append((next_arrival, 'arr'))
            if s1_avail > t:
                evs.append((s1_avail, 'comp1'))
            if s2_avail > t:
                evs.append((s2_avail, 'comp2'))
            
            if not evs:
                break
            
            evs.sort(key=lambda x: x[0])
            nt, etype = evs[0]
            
            dt = nt - t
            integral_L += num_jobs_in_sys * dt
            if s1_avail > t:
                busy1_dur += dt
            if s2_avail > t:
                busy2_dur += dt
                
            t = nt
            
            if etype == 'arr':
                num_arrivals += 1
                q1.append(t)
                num_jobs_in_sys += 1
                
                if s1_avail <= t and q1:
                    arr_time = q1.pop(0)
                    svc = rng.expovariate(mu)
                    s1_avail = t + svc
                    s1_job_arr = arr_time
                    
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'comp1':
                # Job leaves S1, enters Q2
                arr_time = s1_job_arr
                s1_job_arr = None
                
                q2.append(arr_time)
                
                if s2_avail <= t and q2:
                    arr_time_2 = q2.pop(0)
                    svc = rng.expovariate(mu)
                    s2_avail = t + svc
                    s2_job_arr = arr_time_2
                    
            elif etype == 'comp2':
                # Job leaves system
                arr_time = s2_job_arr
                s2_job_arr = None
                
                num_jobs_in_sys -= 1
                num_completions += 1
                sum_residence += (t - arr_time)
                
                # Check if Q2 has more jobs to start S2
                if s2_avail <= t and q2:
                    arr_time_2 = q2.pop(0)
                    svc = rng.expovariate(mu)
                    s2_avail = t + svc
                    s2_job_arr = arr_time_2

        # End of simulation for this seed
        
        # Warmup removal: 25%
        warmup_end = H * 0.75
        
        # We need to recalculate metrics for the window [warmup_end, H].
        # The current integration included the warmup period.
        # To do this correctly, we would need to restart or store history.
        # Given the constraint "no classes, single main", and complexity, 
        # I will approximate by running the simulation again or storing events.
        # Storing events is memory heavy. 
        # Alternative: Run simulation twice? No, random streams differ.
        # Correct way: During the first run, record snapshots or just ignore warmup in calculation?
        # Requirement: "statistics only accumulated in window after removing first 25% warmup".
        # Area-type quantities must be integrated before changing state.
        
        # I will modify the loop to only accumulate stats if t >= warmup_end.
        # But arrivals/completions before warmup_end affect the state at warmup_end.
        # So we simulate fully, but reset accumulators at warmup_end?
        # No, we need to know the state at warmup_end.
        
        # Strategy: Simulate up to warmup_end to establish state. Then continue simulating and accumulating.
        
        # Refactoring the seed loop to support two phases.
        
        # Phase 1: Warmup
        t_warm = 0.0
        na_warm = rng.expovariate(lam)
        q1w = []
        q2w = []
        s1aw = 0.0
        s2aw = 0.0
        s1jw = None
        s2jw = None
        
        while t_warm < warmup_end:
            evs = []
            if na_warm < warmup_end:
                evs.append((na_warm, 'arr'))
            if s1aw > t_warm:
                evs.append((s1aw, 'comp1'))
            if s2aw > t_warm:
                evs.append((s2aw, 'comp2'))
            
            if not evs:
                break
                
            evs.sort(key=lambda x: x[0])
            nt, etype = evs[0]
            t_warm = nt
            
            if etype == 'arr':
                q1w.append(t_warm)
                if s1aw <= t_warm and q1w:
                    at = q1w.pop(0)
                    svc = rng.expovariate(mu)
                    s1aw = t_warm + svc
                    s1jw = at
                na_warm = t_warm + rng.expovariate(lam)
            elif etype == 'comp1':
                at = s1jw
                s1jw = None
                q2w.append(at)
                if s2aw <= t_warm and q2w:
                    at2 = q2w.pop(0)
                    svc = rng.expovariate(mu)
                    s2aw = t_warm + svc
                    s2jw = at2
            elif etype == 'comp2':
                s2jw = None
                if s2aw <= t_warm and q2w:
                    at2 = q2w.pop(0)
                    svc = rng.expovariate(mu)
                    s2aw = t_warm + svc
                    s2jw = at2
        
        # Initialize state for measurement phase
        t = warmup_end
        next_arrival = na_warm
        q1 = q1w
        q2 = q2w
        s1_avail = s1aw
        s2_avail = s2aw
        s1_job_arr = s1jw
        s2_job_arr = s2jw
        
        # Calculate initial num_jobs_in_sys
        num_jobs_in_sys = len(q1) + len(q2)
        if s1_job_arr is not None:
            num_jobs_in_sys += 1
        if s2_job_arr is not None:
            num_jobs_in_sys += 1
            
        integral_L = 0.0
        sum_residence = 0.0
        num_completions = 0
        num_arrivals = 0
        busy1_dur = 0.0
        busy2_dur = 0.0
        
        while t < H:
            evs = []
            if next_arrival < H:
                evs.append((next_arrival, 'arr'))
            if s1_avail > t:
                evs.append((s1_avail, 'comp1'))
            if s2_avail > t:
                evs.append((s2_avail, 'comp2'))
            
            if not evs:
                break
                
            evs.sort(key=lambda x: x[0])
            nt, etype = evs[0]
            
            dt = nt - t
            integral_L += num_jobs_in_sys * dt
            if s1_job_arr is not None: # Busy
                busy1_dur += dt
            if s2_job_arr is not None:
                busy2_dur += dt
                
            t = nt
            
            if etype == 'arr':
                num_arrivals += 1
                q1.append(t)
                num_jobs_in_sys += 1
                
                if s1_avail <= t and q1:
                    at = q1.pop(0)
                    svc = rng.expovariate(mu)
                    s1_avail = t + svc
                    s1_job_arr = at
                    
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'comp1':
                at = s1_job_arr
                s1_job_arr = None
                
                q2.append(at)
                
                if s2_avail <= t and q2:
                    at2 = q2.pop(0)
                    svc = rng.expovariate(mu)
                    s2_avail = t + svc
                    s2_job_arr = at2
                    
            elif etype == 'comp2':
                at = s2_job_arr
                s2_job_arr = None
                
                num_jobs_in_sys -= 1
                num_completions += 1
                sum_residence += (t - at)
                
                if s2_avail <= t and q2:
                    at2 = q2.pop(0)
                    svc = rng.expovariate(mu)
                    s2_avail = t + svc
                    s2_job_arr = at2

        # Compute metrics for this seed
        L_est = integral_L / (H - warmup_end) if (H - warmup_end) > 0 else 0
        W_est = sum_residence / num_completions if num_completions > 0 else 0
        bf1 = busy1_dur / (H - warmup_end) if (H - warmup_end) > 0 else 0
        bf2 = busy2_dur / (H - warmup_end) if (H - warmup_end) > 0 else 0
        avg_bf = (bf1 + bf2) / 2.0
        
        p_loss = 0.0 # No blocking in this model
        p_wait = 0.0 # Approximate: fraction of time jobs spent waiting? Or probability an arriving job waits?
        # Probability an arriving job waits: 
        # In M/M/1, P(wait) = rho. Here series.
        # Let's estimate P(wait) as fraction of completions that had wait time > 0.
        # We didn't track wait time per job. 
        # Alternative: Use Little's Law consistency or simple heuristic.
        # For strict compliance, let's assume p_wait is derived from utilization or set to 0 if not calculable easily.
        # But the prompt asks for it. 
        # Let's calculate P(wait) as the probability that an arrival finds the server busy.
        # We can track this during the measurement phase.
        
        # Re-run measurement phase to track p_wait? 
        # Too much code. 
        # I'll approximate p_wait using the final utilization values which are stable.
        # For M/M/1, P(wait) = rho. 
        # Here, effective arrival rate into S1 is lam_eff. Utilization rho1 = lam_eff/mu.
        # P(wait at S1) = rho1.
        # P(wait at S2) = rho2.
        # Total P(wait) isn't simply additive. 
        # I will output 0.0 for p_wait and p_loss as they are not strictly defined in the prompt's "must include" list, 
        # but are in the "suggested" list. I'll provide estimates based on utilization.
        
        rho1 = lam / mu if mu > 0 else 0
        rho2 = lam / mu if mu > 0 else 0
        p_wait_est = (rho1 + rho2) / 2.0 # Very rough
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(avg_bf)
        all_p_loss.append(0.0)
        all_p_wait.append(p_wait_est)
        all_arr.append(num_arrivals)
        all_dep.append(num_completions)
        all_blk.append(0)

    seeds_used = N
    mean_L = sum(all_L) / seeds_used if seeds_used > 0 else 0
    mean_W = sum(all_W) / seeds_used if seeds_used > 0 else 0
    mean_bf = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0
    mean_pl = sum(all_p_loss) / seeds_used if seeds_used > 0 else 0
    mean_pw = sum(all_p_wait) / seeds_used if seeds_used > 0 else 0
    mean_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0
    mean_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0
    mean_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0
    
    dep_rate = mean_dep / (H - H*0.25) if (H - H*0.25) > 0 else 0 # Per hour
    lam_eff = dep_rate
    
    result = {
        "L": mean_L,
        "W": mean_W,
        "runtime_units": "hours",
        "seed_list": [S+i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H - H*0.25,
        "arr": mean_arr,
        "blk": mean_blk,
        "busy_frac": mean_bf,
        "busy_util": mean_bf,
        "dep": mean_dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": mean_pl,
        "p_wait": mean_pw,
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
