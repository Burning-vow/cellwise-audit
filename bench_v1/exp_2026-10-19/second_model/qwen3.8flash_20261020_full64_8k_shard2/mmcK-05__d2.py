import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 5.0 # 12 min = 0.2 hr -> rate 5/hr
    c = 3
    K = 4 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
        K = 5
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
    all_lam_eff = []
    all_dep_rate = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # State: list of (departure_time, arrival_time) for cars in system
        # We need to track who is waiting and who is being served.
        # Since it's a toll booth with 3 lanes, we assume FCFS within the system? 
        # Or parallel servers? "3 lanes" usually implies parallel servers.
        # If parallel servers, a car enters a lane immediately if free.
        # If no lane free but space available, it waits? 
        # Problem says "station front can hold 4 cars (including passing)".
        # This implies a queueing system with c=3 servers and total capacity K=4.
        # So max queue length = K - c = 1.
        
        # Let's model as M/M/c/K with FCFS discipline for simplicity unless specified otherwise.
        # Usually toll booths are parallel queues or single queue multiple servers.
        # Given "3 lanes", let's assume single queue, 3 servers (M/M/3/4).
        
        # Events: Arrival, Departure
        # We need to know when servers become free.
        # Instead of complex event scheduling, we can simulate step-by-step or use priority queue.
        # Priority queue for departures.
        
        import heapq
        
        # Queue of customers waiting for service (arrival times)
        wait_queue = []
        # List of departure times for currently served customers
        served_departures = [] # heap
        
        # Statistics accumulators (for area integration)
        # We need to integrate L(t) over time.
        # L(t) = number of customers in system at time t.
        # We track last_event_time and current_N.
        
        last_t = 0.0
        current_N = 0
        integral_L = 0.0
        integral_busy_time = 0.0 # Time where N > 0? No, busy_frac is 1-pi_0, so time N>0.
        # Wait, definition: busy_frac = station not empty time proportion = 1 - pi_0.
        # So we integrate indicator(N > 0).
        
        # For W: sum of sojourn times / number of completions.
        # But we only count completions that happened within the window?
        # Standard practice: Count completions in window, sum their sojourn times.
        # However, customers arriving before warmup might leave after.
        # Warmup: discard first 25%.
        
        horizon_end = H
        warmup_end = 0.25 * H
        
        # To handle warmup correctly with area integrals:
        # We run simulation from 0 to H.
        # We record events.
        # Then we calculate stats on [warmup_end, H].
        # But state at warmup_end depends on history.
        # Better: Run full sim, store timeline of changes? Too much memory.
        # Alternative: Run sim, but reset accumulators at warmup_end?
        # Problem: A customer present at warmup_end has partial sojourn time counted?
        # Usually, for steady-state estimates, we just start accumulating stats after warmup.
        # For L (area), we integrate N(t) from warmup_end to H.
        # For W, we take customers who DEPARTED between warmup_end and H.
        # Their sojourn time is full time spent in system.
        # For p_loss, arrivals rejected between warmup_end and H.
        
        # Let's collect raw data points or process on fly with care.
        # Processing on fly is hard because we don't know warmup_end until we start?
        # We do know it.
        
        # Strategy:
        # Simulate from 0 to H.
        # Maintain current time t, next arrival, heap of departures.
        # Keep track of N(t).
        # When an event occurs at t_event:
        #   Add to integral_L: N_old * (t_event - t_last) IF t_last >= warmup_end?
        #   Actually, we need to split intervals crossing warmup boundary.
        
        # Let's simplify: Store all events?
        # Number of events ~ lam * H. If H=100, lam=6, ~600 events. Manageable.
        
        events = [] # (time, type, data)
        # type: 'arr', 'dep'
        
        # Simulation loop
        t = 0.0
        next_arr_time = rng.expovariate(lam)
        dep_heap = [] # (dep_time, arr_time)
        wait_q = [] # arr_times
        
        # We need to know which server is free? 
        # With M/M/c, we just need count of busy servers.
        # If len(dep_heap) < c, new arrival starts service immediately.
        # Else, joins wait_q if len(dep_heap)+len(wait_q) < K.
        
        while t < horizon_end:
            # Determine next event time
            next_dep_time = dep_heap[0][0] if dep_heap else float('inf')
            
            if next_arr_time <= next_dep_time:
                # Arrival
                t = next_arr_time
                if t > horizon_end: break
                
                # Check capacity
                n_in_sys = len(dep_heap) + len(wait_q)
                
                if n_in_sys < K:
                    # Accept
                    events.append((t, 'arr', None))
                    if len(dep_heap) < c:
                        # Start service
                        dur = rng.expovariate(mu)
                        heapq.heappush(dep_heap, (t + dur, t))
                    else:
                        # Join queue
                        wait_q.append(t)
                else:
                    # Reject
                    events.append((t, 'blk', None))
                    
                next_arr_time += rng.expovariate(lam)
            else:
                # Departure
                t = next_dep_time
                if t > horizon_end: break
                
                dep_time, arr_time = heapq.heappop(dep_heap)
                events.append((t, 'dep', arr_time))
                
                # Move one from wait_q to service if any
                if wait_q:
                    w_arr = wait_q.pop(0)
                    dur = rng.expovariate(mu)
                    heapq.heappush(dep_heap, (t + dur, w_arr))
        
        # Now process events to compute stats in [warmup_end, H]
        
        # Reconstruct N(t) trajectory?
        # Easier: Iterate through events, maintain N.
        # But we need to integrate N over time.
        
        # Let's sort events by time (they should be mostly sorted, but blk/arr/dep interleaved)
        # Our generation was chronological.
        
        # Stats variables
        num_arr_win = 0
        num_blk_win = 0
        num_dep_win = 0
        sum_sojourn_win = 0.0
        
        # For L and Busy Fraction, we need time-weighted average.
        # We iterate through time segments defined by events.
        
        # First, filter events to those relevant for counting?
        # No, we need to know N(t) throughout.
        
        # Let's rebuild the timeline of N changes.
        # Initial N at t=0 is 0.
        
        curr_N = 0
        prev_t = 0.0
        
        int_L_win = 0.0
        int_Busy_win = 0.0 # Time where N > 0
        
        # We need to handle the warmup boundary carefully.
        # If an interval [prev_t, t] crosses warmup_end, we split it.
        
        for ev in events:
            etype = ev[1]
            etime = ev[0]
            
            # Process time segment [prev_t, etime]
            dt = etime - prev_t
            if dt > 0:
                # Overlap with [warmup_end, H]
                seg_start = max(prev_t, warmup_end)
                seg_end = min(etime, horizon_end)
                overlap = max(0, seg_end - seg_start)
                
                if overlap > 0:
                    int_L_win += curr_N * overlap
                    if curr_N > 0:
                        int_Busy_win += overlap
            
            # Update N based on event
            if etype == 'arr':
                curr_N += 1
                num_arr_win += 1 if etime >= warmup_end else 0
            elif etype == 'blk':
                num_blk_win += 1 if etime >= warmup_end else 0
            elif etype == 'dep':
                curr_N -= 1
                arr_t = ev[2]
                if etime >= warmup_end:
                    num_dep_win += 1
                    sum_sojourn_win += (etime - arr_t)
            
            prev_t = etime
            
        # Final segment to H
        dt = horizon_end - prev_t
        if dt > 0:
            seg_start = max(prev_t, warmup_end)
            seg_end = horizon_end
            overlap = max(0, seg_end - seg_start)
            if overlap > 0:
                int_L_win += curr_N * overlap
                if curr_N > 0:
                    int_Busy_win += overlap
        
        win_len = horizon_end - warmup_end
        
        if win_len <= 0:
            continue
            
        L_est = int_L_win / win_len
        busy_frac_est = int_Busy_win / win_len
        
        if num_dep_win > 0:
            W_est = sum_sojourn_win / num_dep_win
        else:
            W_est = 0.0
            
        total_attempts = num_arr_win + num_blk_win
        if total_attempts > 0:
            p_loss_est = num_blk_win / total_attempts
        else:
            p_loss_est = 0.0
            
        # p_wait: probability of waiting? 
        # Usually P(Wait) = fraction of accepted customers who had to wait.
        # Accepted = num_arr_win.
        # Who waited? Those who arrived when all servers were busy.
        # We didn't track this explicitly in the simple pass above.
        # Let's re-evaluate or approximate.
        # In M/M/c, P_wait is Erlang C formula related, but here finite capacity.
        # Let's count during simulation?
        # I'll add a flag in events or recount.
        # Recounting requires knowing state at arrival.
        # Let's modify the event processing to check state BEFORE adding arrival.
        
        # Re-run logic for p_wait specifically?
        # Or store more info in events.
        # Let's just recalculate p_wait roughly:
        # It's the fraction of arrivals that joined the queue (wait_q) instead of starting service.
        # During sim, if len(dep_heap) >= c upon arrival, they wait.
        
        # I need to go back to the simulation loop to capture this.
        # Let's restart the per-seed block with better instrumentation.
        
        # --- Restarting per-seed logic with better tracking ---
        
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        dep_heap = []
        wait_q = []
        
        # Trackers for window stats
        # We will collect lists of (time, type, extra) again but with 'wait' flag
        
        events = []
        
        while t < horizon_end:
            next_dep_time = dep_heap[0][0] if dep_heap else float('inf')
            
            if next_arrival <= next_dep_time:
                t = next_arrival
                if t > horizon_end: break
                
                n_in_sys = len(dep_heap) + len(wait_q)
                
                if n_in_sys < K:
                    did_wait = (len(dep_heap) >= c)
                    events.append((t, 'arr', {'wait': did_wait}))
                    if not did_wait:
                        dur = rng.expovariate(mu)
                        heapq.heappush(dep_heap, (t + dur, t))
                    else:
                        wait_q.append(t)
                else:
                    events.append((t, 'blk', {}))
                    
                next_arrival += rng.expovariate(lam)
            else:
                t = next_dep_time
                if t > horizon_end: break
                
                dep_time, arr_time = heapq.heappop(dep_heap)
                events.append((t, 'dep', {'arr_time': arr_time}))
                
                if wait_q:
                    w_arr = wait_q.pop(0)
                    dur = rng.expovariate(mu)
                    heapq.heappush(dep_heap, (t + dur, w_arr))
        
        # Process events for stats
        curr_N = 0
        prev_t = 0.0
        int_L_win = 0.0
        int_Busy_win = 0.0
        
        num_arr_win = 0
        num_blk_win = 0
        num_dep_win = 0
        sum_sojourn_win = 0.0
        num_wait_win = 0 # Arrivals that waited
        
        for ev in events:
            etype = ev[1]
            etime = ev[0]
            data = ev[2]
            
            dt = etime - prev_t
            if dt > 0:
                seg_start = max(prev_t, warmup_end)
                seg_end = min(etime, horizon_end)
                overlap = max(0, seg_end - seg_start)
                if overlap > 0:
                    int_L_win += curr_N * overlap
                    if curr_N > 0:
                        int_Busy_win += overlap
            
            if etype == 'arr':
                curr_N += 1
                if etime >= warmup_end:
                    num_arr_win += 1
                    if data['wait']:
                        num_wait_win += 1
            elif etype == 'blk':
                if etime >= warmup_end:
                    num_blk_win += 1
            elif etype == 'dep':
                curr_N -= 1
                if etime >= warmup_end:
                    num_dep_win += 1
                    sum_sojourn_win += (etime - data['arr_time'])
            
            prev_t = etime
            
        dt = horizon_end - prev_t
        if dt > 0:
            seg_start = max(prev_t, warmup_end)
            seg_end = horizon_end
            overlap = max(0, seg_end - seg_start)
            if overlap > 0:
                int_L_win += curr_N * overlap
                if curr_N > 0:
                    int_Busy_win += overlap
        
        win_len = horizon_end - warmup_end
        
        L_est = int_L_win / win_len
        busy_frac_est = int_Busy_win / win_len
        
        W_est = sum_sojourn_win / num_dep_win if num_dep_win > 0 else 0.0
        
        total_att = num_arr_win + num_blk_win
        p_loss_est = num_blk_win / total_att if total_att > 0 else 0.0
        
        p_wait_est = num_wait_win / num_arr_win if num_arr_win > 0 else 0.0
        
        # busy_util = E[min(N,c)]/c
        # Need to integrate min(N(t), c)
        # We didn't track this in the loop above easily without another pass or storing N history.
        # Let's do a quick second pass or modify loop.
        # Modifying loop is cleaner.
        
        # Reset and redo for busy_util?
        # Or calculate analytically? No, simulation.
        # Let's just add int_minNc to the previous loop.
        
        # I will rewrite the processing part to include int_minNc.
        
        curr_N = 0
        prev_t = 0.0
        int_L_win = 0.0
        int_Busy_win = 0.0
        int_MinNC_win = 0.0
        
        num_arr_win = 0
        num_blk_win = 0
        num_dep_win = 0
        sum_sojourn_win = 0.0
        num_wait_win = 0
        
        for ev in events:
            etype = ev[1]
            etime = ev[0]
            data = ev[2]
            
            dt = etime - prev_t
            if dt > 0:
                seg_start = max(prev_t, warmup_end)
                seg_end = min(etime, horizon_end)
                overlap = max(0, seg_end - seg_start)
                if overlap > 0:
                    int_L_win += curr_N * overlap
                    if curr_N > 0:
                        int_Busy_win += overlap
                    int_MinNC_win += min(curr_N, c) * overlap
            
            if etype == 'arr':
                curr_N += 1
                if etime >= warmup_end:
                    num_arr_win += 1
                    if data['wait']:
                        num_wait_win += 1
            elif etype == 'blk':
                if etime >= warmup_end:
                    num_blk_win += 1
            elif etype == 'dep':
                curr_N -= 1
                if etime >= warmup_end:
                    num_dep_win += 1
                    sum_sojourn_win += (etime - data['arr_time'])
            
            prev_t = etime
            
        dt = horizon_end - prev_t
        if dt > 0:
            seg_start = max(prev_t, warmup_end)
            seg_end = horizon_end
            overlap = max(0, seg_end - seg_start)
            if overlap > 0:
                int_L_win += curr_N * overlap
                if curr_N > 0:
                    int_Busy_win += overlap
                int_MinNC_win += min(curr_N, c) * overlap
        
        L_est = int_L_win / win_len
        busy_frac_est = int_Busy_win / win_len
        busy_util_est = (int_MinNC_win / win_len) / c
        
        W_est = sum_sojourn_win / num_dep_win if num_dep_win > 0 else 0.0
        p_loss_est = num_blk_win / (num_arr_win + num_blk_win) if (num_arr_win + num_blk_win) > 0 else 0.0
        p_wait_est = num_wait_win / num_arr_win if num_arr_win > 0 else 0.0
        
        dep_rate_est = num_dep_win / win_len # per hour
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(num_arr_win)
        all_blk.append(num_blk_win)
        all_dep.append(num_dep_win)
        all_busy_util.append(busy_util_est)
        all_lam_eff.append(num_arr_win / win_len)
        all_dep_rate.append(dep_rate_est)

    seeds_used = len(all_L)
    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hours",
        "seed_list": [S_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H - 0.25*H, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
