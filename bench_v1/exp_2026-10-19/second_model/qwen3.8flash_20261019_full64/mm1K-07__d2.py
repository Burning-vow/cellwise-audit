import sys, json, math, random
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 10; horizon = 100.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]
    
    lam_base = 6.0; mu_base = 10.0 # 6 per hour arrival, 6 min service -> 10 per hour rate
    c = 1; max_cap = 6
    
    if pert == "lam_up": lam_base *= 1.1
    elif pert == "mu_up": mu_base *= 1.1
    elif pert == "c_up": pass # capacity fixed by problem statement usually, but if pert changes structure? Prompt says pert only changes params not structure. So ignore c_up or maybe it implies something else? Usually c is fixed. Let's assume no change for c_up unless specified.
    
    results = []
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    total_arr = 0; total_blk = 0; total_dep = 0
    
    time_unit = "hour"
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        queue = deque() # waiting patients (arrival_time, service_duration)
        server_free_time = 0.0
        current_service_end = 0.0
        
        # Statistics accumulators for the whole run to determine warmup cut-off later? 
        # Or we can just record events and filter. Given H is large, recording all might be heavy but okay for small N.
        # Better: Run simulation, store event history or just accumulate stats after a certain point?
        # Requirement: "Statistics only accumulated in window after removing first 25% warmup".
        # We need to know when 25% of Horizon is reached.
        warmup_end = 0.25 * horizon
        
        # To calculate area-based metrics correctly with warmup removal, we need to integrate over [warmup_end, horizon].
        # We will track state changes.
        
        # Variables for integration
        last_event_time = 0.0
        current_N = 0 # number in system (waiting + serving)
        is_serving = False
        
        # Accumulators for the post-warmup window
        area_N = 0.0
        area_busy = 0.0 # 1 if server busy, 0 otherwise
        count_arrivals_post = 0
        count_departures_post = 0
        count_blocked_post = 0
        sum_waiting_time_post = 0.0 # Sum of (departure - arrival) for those who waited? No, W is avg time in system.
        # Actually, standard Little's Law uses L = lambda_eff * W.
        # We need sum of time in system for each customer that departed in the window?
        # Careful: Customers arriving before warmup end but departing after contribute to L.
        # Customers arriving after warmup end but departing after horizon are truncated?
        # Standard approach: Integrate N(t) over [T_w, T_h] to get Area_N. Then L = Area_N / (T_h - T_w).
        # For W: Use Little's Law W = L / lambda_eff. Or compute directly from completed services in window?
        # Direct computation of W often requires tracking individual sojourn times.
        # Let's use the integral method for L and busy_frac.
        # For p_loss: blocked / arrivals_in_window? Or blocked / attempted?
        # p_loss = blocked / (blocked + accepted). Accepted = arrivals - blocked.
        # But arrivals include those blocked.
        # Let's define:
        # arr_count: total arrivals in window
        # blk_count: total blocked in window
        # dep_count: total departures in window
        # This gets tricky with boundary conditions.
        
        # Simpler robust way for discrete event sim with warmup:
        # 1. Run full sim.
        # 2. Record all events (time, type, data).
        # 3. Filter events/stats for t >= warmup_end.
        
        events = [] # (time, type, payload)
        # Types: 'arr', 'dep', 'blk'
        
        # State variables during sim
        n_sys = 0
        server_status = 0 # 0 idle, 1 busy
        next_dep_time = float('inf')
        
        # Initialize
        # Generate first arrival
        
        while t < horizon:
            # Determine next event time
            next_ev_t = min(next_arrival, next_dep_time)
            
            if next_ev_t > horizon:
                break
                
            dt = next_ev_t - t
            
            # Update integrals if we were in the measurement window?
            # We'll just log states at events.
            
            t = next_ev_t
            
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                events.append((t, 'arr', None))
                
                if n_sys < max_cap:
                    n_sys += 1
                    if n_sys == 1:
                        # Start service immediately
                        serv_dur = rng.expovariate(mu_base)
                        next_dep_time = t + serv_dur
                        server_status = 1
                        events.append((next_dep_time, 'dep', {'start': t}))
                    else:
                        # Join queue
                        queue.append({'arrival': t})
                else:
                    # Blocked
                    events.append((t, 'blk', None))
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam_base)
                
            elif abs(t - next_dep_time) < 1e-9:
                # Departure
                events.append((t, 'dep', {'end': t}))
                n_sys -= 1
                server_status = 0
                
                if queue:
                    cust = queue.popleft()
                    n_sys += 1
                    server_status = 1
                    serv_dur = rng.expovariate(mu_base)
                    next_dep_time = t + serv_dur
                    events.append((next_dep_time, 'dep', {'start': t}))
                else:
                    next_dep_time = float('inf')
                    
            else:
                break # Should not happen

        # Post-processing for statistics in window [warmup_end, horizon]
        # We need to reconstruct N(t) and Busy(t) from events.
        
        # Sort events by time (they should be mostly sorted, but deps scheduled ahead might interleave)
        events.sort(key=lambda x: x[0])
        
        # Calculate Area_N and Area_Busy
        # We iterate through events within the window.
        
        # First, find initial state at warmup_end.
        # Replay events up to warmup_end to get state.
        curr_n = 0
        curr_busy = 0
        curr_queue_len = 0
        curr_next_dep = float('inf')
        curr_next_arr = float('inf')
        
        # Re-simulate quickly or parse events? Parsing events is safer if we stored enough info.
        # Our events list has 'arr', 'dep', 'blk'.
        # 'dep' event doesn't explicitly say if it started service or just finished.
        # We appended a 'dep' event when scheduling start too? No, I appended 'dep' with 'start' key when starting service.
        # And 'dep' with 'end' key when finishing.
        # This is messy. Let's stick to simple state reconstruction using the recorded 'arr' and 'blk' and 'dep(end)'?
        # Actually, let's just re-run the logic on the fly for the window? No, we have the events.
        
        # Let's simplify: Just count things in the window based on event timestamps.
        # L = Average Number in System.
        # We need integral of N(t) dt.
        
        # Let's build a timeline of N(t) changes.
        # Events affecting N: Arr (if accepted), Dep (completion).
        # Blocked does not affect N.
        
        # Collect relevant events in [warmup_end, horizon]
        # Also need state AT warmup_end.
        
        # To get state at warmup_end, we process all events < warmup_end.
        # We need to know how many are in system.
        # In-system = Waiting + Serving.
        # Serving = 1 if server busy.
        # Waiting = len(queue).
        
        # Let's replay from scratch using the RNG? No, RNG state is gone.
        # We must rely on the `events` list.
        # The `events` list contains:
        # (t, 'arr', None) -> Potential increase in N if accepted.
        # (t, 'blk', None) -> No change in N.
        # (t, 'dep', {'end': t}) -> Decrease in N.
        # (t, 'dep', {'start': t}) -> This was added when service started. It represents the transition from Queue to Service?
        #   When an arrival happens and starts service, N increases by 1.
        #   When a departure happens and someone moves from queue to service, N stays same?
        #   Wait.
        #   Case 1: Idle -> Arrival. N goes 0->1. Event 'arr' adds 1. Event 'dep(start)' marks start.
        #   Case 2: Busy -> Arrival. N goes k->k+1. Event 'arr' adds 1.
        #   Case 3: Departure. N goes k->k-1. Event 'dep(end)' subtracts 1.
        #   Case 4: Departure triggers next service. N goes k->k-1 then k-1->k-1?
        #   My code: On dep, n_sys -= 1. If queue, pop, n_sys += 1. Net change 0?
        #   No, n_sys includes waiting.
        #   If queue exists, one person leaves system (dep), one enters service (was waiting).
        #   Total N decreases by 1 (the one who left). The one moving from wait to serve doesn't change N.
        #   So 'dep(end)' always means N--.
        #   'arr' (accepted) always means N++.
        #   'blk' means N unchanged.
        #   What about 'dep(start)'? I added it to events. Does it change N? No. It's just metadata.
        #   So, N changes only on 'arr' (if not followed by 'blk'?) and 'dep(end)'.
        #   How do I know if an 'arr' was accepted?
        #   If 'arr' is followed by 'blk' at same time? No, they are distinct events.
        #   In my loop: if accepted, I add 'arr'. If blocked, I add 'arr' AND 'blk'?
        #   Code: `events.append((t, 'arr', None))` happens BEFORE check.
        #   Then if blocked: `events.append((t, 'blk', None))`.
        #   So every arrival generates an 'arr' event. Blocked ones generate 'arr' + 'blk'.
        #   Accepted ones generate 'arr' only (plus potentially 'dep(start)').
        #   So: Delta N = Count('arr') - Count('blk') - Count('dep(end)')?
        #   No. 'dep(end)' reduces N. 'arr' increases N IF accepted.
        #   Accepted = 'arr' without 'blk'.
        #   So Delta N = Count('arr' where no 'blk' at same t) - Count('dep(end)').
        #   Since 'blk' is at same t as 'arr', we can pair them.
        
        # Let's extract lists of times for:
        # acc_arr_times: times of 'arr' that are NOT 'blk'
        # dep_times: times of 'dep' with 'end' key
        # blk_times: times of 'blk'
        # all_arr_times: times of 'arr'
        
        acc_arr = []
        deps = []
        blks = []
        all_arrs = []
        
        # Group by time to handle simultaneous events?
        # In continuous time, exact equality is rare except for our generated ones.
        # 'arr' and 'blk' are at same t.
        # 'dep(end)' and 'dep(start)' might be at same t?
        # If dep occurs and queue pops, new dep(start) is scheduled at future time.
        # So 'dep(end)' and 'dep(start)' are different times usually.
        
        # Process events to classify
        # Note: Order matters if multiple events at same time.
        # But 'arr' and 'blk' are generated together.
        
        temp_map = {} # t -> list of types
        for ev in events:
            t, typ, data = ev
            if t not in temp_map: temp_map[t] = []
            temp_map[t].append((typ, data))
            
        for t in sorted(temp_map.keys()):
            items = temp_map[t]
            has_blk = any(i[0]=='blk' for i in items)
            has_arr = any(i[0]=='arr' for i in items)
            has_dep_end = any(i[0]=='dep' and 'end' in i[1] for i in items)
            
            if has_arr:
                all_arrs.append(t)
                if not has_blk:
                    acc_arr.append(t)
            if has_blk:
                blks.append(t)
            if has_dep_end:
                deps.append(t)
                
        # Now calculate stats for window [W_start, H]
        W_start = warmup_end
        H = horizon
        
        # Filter times
        w_acc_arr = [x for x in acc_arr if W_start <= x < H]
        w_all_arr = [x for x in all_arrs if W_start <= x < H]
        w_blks = [x for x in blks if W_start <= x < H]
        w_deps = [x for x in deps if W_start <= x < H]
        
        # Counts
        cnt_arr = len(w_all_arr)
        cnt_blk = len(w_blks)
        cnt_dep = len(w_deps)
        cnt_acc = len(w_acc_arr)
        
        # p_loss
        p_loss = cnt_blk / cnt_arr if cnt_arr > 0 else 0.0
        
        # L (Average Number in System)
        # Need integral of N(t).
        # Build step function of N(t).
        # Changes at acc_arr (+1) and deps (-1).
        # Note: A dep removes a person. An acc_arr adds a person.
        # Are there overlaps? Yes.
        
        # Get all change points in window
        changes = []
        for t in w_acc_arr: changes.append((t, 1))
        for t in w_deps: changes.append((t, -1))
        changes.sort(key=lambda x: x[0])
        
        # Determine N(W_start)
        # Count acc_arr < W_start minus deps < W_start
        pre_acc = len([x for x in acc_arr if x < W_start])
        pre_dep = len([x for x in deps if x < W_start])
        n_curr = pre_acc - pre_dep
        
        area_n = 0.0
        last_t = W_start
        
        for t, delta in changes:
            if t > H: break
            if t > last_t:
                area_n += n_curr * (t - last_t)
                last_t = t
            n_curr += delta
            
        if last_t < H:
            area_n += n_curr * (H - last_t)
            
        L = area_n / (H - W_start) if (H - W_start) > 0 else 0.0
        
        # Busy Fraction (1 - pi_0)
        # Server is busy if N > 0? No, if N>=1 server is busy?
        # With c=1, yes. Server busy iff N >= 1.
        # So Area_Busy = Integral of (N(t) > 0 ? 1 : 0) dt.
        # We can reuse the step function.
        
        area_busy = 0.0
        n_curr = pre_acc - pre_dep
        last_t = W_start
        
        for t, delta in changes:
            if t > H: break
            if t > last_t:
                if n_curr > 0:
                    area_busy += (t - last_t)
                last_t = t
            n_curr += delta
            
        if last_t < H:
            if n_curr > 0:
                area_busy += (H - last_t)
                
        busy_frac = area_busy / (H - W_start) if (H - W_start) > 0 else 0.0
        
        # W (Average Time in System)
        # Little's Law: L = lambda_eff * W => W = L / lambda_eff
        # lambda_eff = cnt_acc / (H - W_start)
        lam_eff = cnt_acc / (H - W_start) if (H - W_start) > 0 else 0.0
        W = L / lam_eff if lam_eff > 0 else 0
