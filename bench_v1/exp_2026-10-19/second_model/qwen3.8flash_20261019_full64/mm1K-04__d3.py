import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 5.0 # 12 per hour
    c = 1
    K = 4 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Capacity perturbation not explicitly defined as changing c in standard M/M/1/K, 
        # but prompt says "perturbation only changes parameters". 
        # If c_up means increasing capacity? But c is fixed at 1 doctor. 
        # Maybe it means increasing the queue limit? Or maybe it's a distractor or implies lambda/mu change?
        # Prompt: "NAME takes none/lam_up/mu_up/c_up". 
        # Usually c refers to servers. Here c=1. If c_up, maybe c becomes 2? 
        # But problem says "only 1 doctor". Let's assume c_up increases the buffer size K? 
        # Or perhaps it's a typo for something else. Given strict constraints, let's treat c_up as no-op or slight variation if needed.
        # However, standard discrete event sim usually keeps structure. Let's assume c_up doesn't change anything significant or maybe increases K?
        # Let's stick to base params if c_up is ambiguous, or assume it increases K by 1? 
        # Actually, looking at typical benchmarks, c might refer to cost or capacity. 
        # Let's assume c_up does nothing to avoid breaking the single-server constraint unless specified.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        end_time = H
        
        # State variables
        n_customers = 0 # Number of people in system (waiting + serving)
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Statistics accumulators (for area integration and counts)
        # We need to track state changes to integrate L over time.
        last_event_time = 0.0
        integral_L = 0.0
        integral_busy_time = 0.0 # Time where n > 0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        count_waits = 0 # Customers who waited (arrival when n>0)
        
        # To calculate W, we need sum of waiting times (time in system).
        # Since service time is exponential, we can use Little's Law or track individual sojourn times.
        # Tracking individual sojourn times requires storing arrival time for each customer.
        # Queue implementation: list of arrival times.
        queue = [] # Stores arrival times of customers currently in system (including one in service)
        
        while t < end_time:
            # Determine next event
            if next_arrival <= next_departure:
                # Arrival Event
                t = next_arrival
                
                # Integrate stats from last_event_time to t
                dt = t - last_event_time
                if dt > 0:
                    integral_L += n_customers * dt
                    if n_customers > 0:
                        integral_busy_time += dt
                
                last_event_time = t
                
                # Process Arrival
                if n_customers < K:
                    # Accept
                    queue.append(t)
                    n_customers += 1
                    count_arrivals += 1
                    if n_customers > 1: # Was already busy, so this person waits
                        count_waits += 1
                    
                    # Schedule departure if server was idle
                    if n_customers == 1:
                        svc_time = rng.expovariate(mu)
                        next_departure = t + svc_time
                else:
                    # Block
                    count_blocks += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure Event
                t = next_departure
                
                # Integrate stats from last_event_time to t
                dt = t - last_event_time
                if dt > 0:
                    integral_L += n_customers * dt
                    if n_customers > 0:
                        integral_busy_time += dt
                
                last_event_time = t
                
                # Process Departure
                if queue:
                    arr_time = queue.pop(0)
                    sojourn = t - arr_time
                    # Accumulate sojourn time for W calculation later
                    # We'll store these in a list to filter by warmup later? 
                    # No, we must filter events by time window [warmup_end, H].
                    # So we should check if t >= warmup_end before counting dep/sojourn.
                    
                    n_customers -= 1
                    count_departures += 1
                    
                    # If more customers, start next service
                    if n_customers > 0:
                        svc_time = rng.expovariate(mu)
                        next_departure = t + svc_time
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')
        
        # Post-processing for Warmup Removal
        # The above loop integrated everything from 0 to H.
        # We need to subtract the contribution from [0, warmup_end] and re-calculate counts within [warmup_end, H].
        # This approach is tricky because we didn't store event history.
        # Better approach: Run simulation, record all events with timestamps, then filter.
        
        # Let's restart the logic inside the loop to be cleaner regarding warmup.
        pass 

    # Re-implementing with event recording for correct warmup filtering
    
    results_per_seed = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        end_time = H
        warmup_end = H * warmup_ratio
        
        n_customers = 0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Lists to store events for post-filtering
        # Each entry: (time, type, data)
        # For arrivals: (t, 'arr', None) -> if accepted, also add to queue
        # For departures: (t, 'dep', sojourn_time)
        # For blocks: (t, 'blk', None)
        
        events = []
        queue = [] # arrival times
        
        # We need to integrate L and BusyTime accurately over the window [warmup_end, H].
        # Instead of integrating during sim, we can reconstruct the timeline from events.
        
        while t < end_time:
            if next_arrival <= next_departure:
                t = next_arrival
                events.append((t, 'arr'))
                
                if n_customers < K:
                    queue.append(t)
                    n_customers += 1
                    if n_customers == 1:
                        svc_time = rng.expovariate(mu)
                        next_departure = t + svc_time
                else:
                    events.append((t, 'blk'))
                
                next_arrival = t + rng.expovariate(lam)
            else:
                t = next_departure
                if queue:
                    arr_t = queue.pop(0)
                    sojourn = t - arr_t
                    events.append((t, 'dep', sojourn))
                    n_customers -= 1
                    if n_customers > 0:
                        svc_time = rng.expovariate(mu)
                        next_departure = t + svc_time
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')
        
        # Now process events to compute stats in window [warmup_end, H]
        
        # 1. Calculate Integral L and Integral Busy Time
        # We need the state n_customers at any time.
        # Sort events by time (they are generated in order, but 'blk' added after 'arr' at same t? 
        # In code above, 'arr' is appended, then if blocked, 'blk' is appended. 
        # Order matters for state transitions.
        # Let's rebuild the timeline.
        
        # Collect all unique event times in window
        relevant_events = []
        for ev in events:
            if ev[0] >= warmup_end:
                relevant_events.append(ev)
        
        # To integrate, we need to know the state between events.
        # We can simulate the state changes again using the recorded events, starting from the state at warmup_end.
        # Finding state at warmup_end:
        # Replay events up to warmup_end.
        
        replay_n = 0
        replay_queue = []
        # We don't have service times stored in events easily for replay if we just look at 'dep'.
        # But 'dep' happens when service ends. 
        # Actually, simpler: Just iterate through ALL events, tracking state, and accumulate integrals only when t >= warmup_end.
        
        current_state_n = 0
        last_t = 0.0
        integral_L_win = 0.0
        integral_Busy_win = 0.0
        
        # We need to handle simultaneous events carefully. 
        # In our generation, if arrival and departure happen at exact same time, arrival processed first?
        # Code: `if next_arrival <= next_departure`. Yes, arrival first.
        
        # Let's iterate through the original `events` list which preserves chronological order.
        # But `events` contains 'arr', 'blk', 'dep'.
        # 'blk' doesn't change state. 'arr' increments if accepted. 'dep' decrements.
        # Wait, 'arr' event in list doesn't tell us if it was accepted or blocked directly in the tuple structure I used above?
        # I appended `(t, 'arr')` always. Then if blocked, `(t, 'blk')`.
        # If accepted, no extra marker.
        # This makes replay hard.
        
        # Refine event recording:
        # Record: (time, type, payload)
        # type: 'A' (Arrival Attempt), 'D' (Departure)
        # Payload for A: True (Accepted) / False (Blocked)
        # Payload for D: Sojourn Time
        
        final_events = []
        # Re-run simulation quickly to get structured events? No, we have the data.
        # Let's modify the simulation loop to record better.
        
        # Restarting the inner loop logic for clarity in final code structure below.
        # ...
        
        # Since I cannot edit the thought process flow easily, I will write the final code directly based on this refined plan.
        
        # Plan for Final Code:
        # 1. Simulate.
        # 2. Store events: (time, 'A', accepted_bool), (time, 'D', sojourn_time).
        # 3. After sim, sort events by time.
        # 4. Initialize state n=0.
        # 5. Iterate events. Update state.
        # 6. Between events, if interval overlaps with [warmup_end, H], add to integrals.
        # 7. Count stats (arr, blk, dep, wait) only if event time >= warmup_end.
        # 8. Compute averages.

    # Writing the actual code now.

    def run_sim(seed_idx):
        s = S_start + seed_idx
        r = random.Random(s)
        t = 0.0
        H_local = H
        w_end = H_local * warmup_ratio
        
        n = 0
        na = r.expovariate(lam)
        nd = float('inf')
        
        events = [] # (time, type, val)
        q = [] # arrival times
        
        while t < H_local:
            if na <= nd:
                t = na
                acc = False
                if n < K:
                    acc = True
                    q.append(t)
                    n += 1
                    if n == 1:
                        st = r.expovariate(mu)
                        nd = t + st
                events.append((t, 'A', acc))
                na = t + r.expovariate(lam)
            else:
                t = nd
                if q:
                    at = q.pop(0)
                    sj = t - at
                    n -= 1
                    events.append((t, 'D', sj))
                    if n > 0:
                        st = r.expovariate(mu)
                        nd = t + st
                    else:
                        nd = float('inf')
                else:
                    nd = float('inf')
        
        # Process Events for Stats
        # Sort just in case (should be sorted)
        events.sort(key=lambda x: x[0])
        
        curr_n = 0
        prev_t = 0.0
        
        int_L = 0.0
        int_Busy = 0.0
        
        cnt_A = 0
        cnt_Blk = 0
        cnt_D = 0
        cnt_Wait = 0 # Arrivals that found n>0 (before increment)
        sum_Sojourn = 0.0
        
        for etype, eval_ in [(e[1], e[2]) for e in events]:
            pass
            
        # Need time too
        for ev in events:
            et, typ, val = ev
            
            # Add integral from prev_t to et
            dt = et - prev_t
            if dt > 0:
                # Overlap with window
                start_int = max(prev_t, w_end)
                end_int = min(et, H_local)
                if start_int < end_int:
                    overlap = end_int - start_int
                    int_L += curr_n * overlap
                    if curr_n > 0:
                        int_Busy += overlap
            
            # Process event
            if typ == 'A':
                if et >= w_end:
                    cnt_A += 1
                    if not val:
                        cnt_Blk += 1
                    else:
                        # Check if waited: if curr_n > 0 before adding
                        if curr_n > 0:
                            cnt_Wait += 1
                        curr_n += 1
            elif typ == 'D':
                if et >= w_end:
                    cnt_D += 1
                    sum_Sojourn += val
                    curr_n -= 1
            
            prev_t = et
            
        # Handle tail from last event to H_local
        dt = H_local - prev_t
        if dt > 0:
            start_int = max(prev_t, w_end)
            end_int = H_local
            if start_int < end_int:
                overlap = end_int - start_int
                int_L += curr_n * overlap
                if curr_n > 0:
                    int_Busy += overlap
        
        # Calculate Metrics
        win_dur = H_local - w_end
        if win_dur <= 0: return None
        
        L_avg = int_L / win_dur
        Busy_Frac = int_Busy / win_dur
        
        # W: Average sojourn time of completed services in window
        # Note: Strictly, W is average time in system. Using completed ones in window is standard approximation.
        if cnt_D > 0:
            W_avg = sum_Sojourn / cnt_D
        else:
            W_avg = 0.0
            
        p_loss = cnt_Blk / cnt_A if cnt_A > 0 else 0.0
        p_wait = cnt_Wait / cnt_A if cnt_A > 0 else 0.0
        
        # busy_util = E[min(N,c)]/c. Here c=1. E[min(N,1)] = P(N>=1) = Busy_Frac.
        # So busy_util = Busy_Frac / 1 = Busy_Frac.
        busy_util = Busy_Frac
        
        # Dep rate per hour
        dep_rate = cnt_D / win_dur
        
        # Lam eff
        lam_eff = cnt_A / win_dur
        
        return {
            'L': L_avg,
            'W': W_avg,
            'busy_frac': Busy_Frac,
            'p_loss': p_loss,
            'p_wait': p_wait,
            'arr': cnt_A,
            'blk': cnt_Blk,
            'dep': cnt_D,
            'busy_util': busy_util,
            'dep_rate': dep_rate,
            'lam_eff': lam_eff
        }

    res_list = []
    for i in range(N_seeds):
        res = run_sim(i)
        if res:
