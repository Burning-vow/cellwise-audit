import argparse, json, math, random

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
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        service_times = {}
        dep_events = []
        
        # State variables for integration
        area_n = 0.0
        last_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        total_wait_time = 0.0
        busy_area = 0.0
        
        # We need to track when each customer arrives and their service time
        # For W calculation: sum of (departure - arrival) for customers who depart within window? 
        # Actually standard way: integrate N(t) over window / effective arrivals in window? 
        # Or use Little's law estimate from simulation directly.
        # Let's do: L = integral(N)/win_len, W = sum(w_i)/dep_count_in_window where w_i is sojourn time of those who departed in window.
        # But careful with boundary effects. Simpler: accumulate sojourn times for all completions during the whole run, but only count those that started after warmup? 
        # The prompt says "statistics only accumulated in window after removing first 25% warmup". Area-type quantities must be integrated before state change.
        
        # Let's restart logic properly:
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        # Store (arrival_time, service_time) for current in-system customers
        # When a departure happens, we know its arrival time.
        # We'll maintain a list of active customers with their arrival times.
        active_customers = []  # list of (arrival_time, remaining_service_or_completion_time?)
        # Better: schedule departures explicitly.
        # Each event: either arrival or departure.
        # On arrival: generate service time, add to system, schedule departure at t+service_time.
        # On departure: remove from system, record sojourn time = t - arrival_time.
        
        # Event queue approach might be cleaner but let's stick to simple loop since single server.
        # Next event time = min(next_arr, next_dep)
        next_dep = float('inf')
        # Need to map departure events to arrival times. Use a dict or list.
        # Since single server, only one departure can happen at a time? No, multiple could be scheduled if we pre-schedule, but here service starts immediately upon arrival if idle.
        # If server busy, new arrival waits. So only one service in progress.
        # So we just need to know when the current service ends.
        
        # Let's restructure:
        # State: n (number in system), server_free_at (time when current service finishes, inf if free)
        # But we need arrival times of waiting customers too.
        # Queue of arrival times for waiting customers.
        
        n = 0
        server_free_at = float('inf')
        wait_queue = []  # arrival times of waiting customers
        next_arr = rng.expovariate(lam)
        
        area_n = 0.0
        last_t = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        total_sojourn_win = 0.0
        busy_area_win = 0.0
        wait_count_win = 0  # number of customers who had to wait (arrived when server busy)
        
        # We also need counts for full run to compute averages correctly? 
        # Prompt: statistics only in window. So we reset accumulators at win_start? 
        # But area integration needs continuous tracking. 
        # Strategy: simulate entire horizon, but only accumulate stats for events/intervals intersecting [win_start, horizon].
        
        # Let's do it step by step.
        t = 0.0
        n = 0
        server_free_at = float('inf')
        wait_queue = []
        next_arr = rng.expovariate(lam)
        
        # Accumulators for the window
        area_n_win = 0.0
        busy_area_win = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        total_sojourn_win = 0.0
        wait_count_win = 0
        
        # To handle partial intervals at boundaries, we need to split intervals.
        # Instead, let's just simulate and check if interval overlaps with window.
        
        while t < horizon:
            # Determine next event
            next_dep = server_free_at if n > 0 else float('inf')
            if next_arr <= next_dep:
                # Arrival
                dt = next_arr - t
                # Integrate areas over [t, next_arr]
                if dt > 0:
                    overlap_start = max(t, win_start)
                    overlap_end = min(next_arr, horizon)
                    if overlap_start < overlap_end:
                        len_overlap = overlap_end - overlap_start
                        area_n_win += n * len_overlap
                        if n > 0:
                            busy_area_win += 1 * len_overlap
                t = next_arr
                # Process arrival
                if n == 0:
                    # Server idle
                    n = 1
                    st = rng.expovariate(mu)
                    server_free_at = t + st
                    # This customer does not wait
                    # Record arrival in window?
                    if t >= win_start:
                        arr_count_win += 1
                        # Sojourn will be recorded on departure
                else:
                    # Server busy
                    # Check if there's capacity? M/M/1 has infinite buffer, no blocking.
                    # So blk_count always 0 for M/M/1 unless specified otherwise.
                    # Prompt mentions blk, p_loss. For M/M/1, these are 0.
                    n += 1
                    wait_queue.append(t)
                    if t >= win_start:
                        arr_count_win += 1
                        wait_count_win += 1
            else:
                # Departure
                dt = next_dep - t
                if dt > 0:
                    overlap_start = max(t, win_start)
                    overlap_end = min(next_dep, horizon)
                    if overlap_start < overlap_end:
                        len_overlap = overlap_end - overlap_start
                        area_n_win += n * len_overlap
                        if n > 0:
                            busy_area_win += 1 * len_overlap
                t = next_dep
                # Process departure
                # Who leaves? The one being served.
                # In our model, server_free_at corresponds to the completion of the service that started when server became free.
                # But we didn't store which arrival time corresponds to this service.
                # Problem: when server was idle and an arrival came, we set server_free_at. That customer's arrival time is known (it was t at that moment).
                # When server was busy and another arrived, they went to wait_queue.
                # Upon departure, the next customer from wait_queue (if any) starts service.
                
                # We need to track the arrival time of the currently served customer.
                # Let's add a variable: current_service_arrival_time
                
                # I missed this in initialization. Let me rewrite the loop more carefully.
                pass
            
        # The above logic got tangled. Let me restart with clearer state.
        # State: 
        #   n: number in system
        #   current_arrival_time: arrival time of customer in service (None if idle)
        #   server_free_at: time when current service ends (inf if idle)
        #   wait_queue: list of arrival times of waiting customers
        
        # Reset and redo
        t = 0.0
        n = 0
        current_arrival_time = None
        server_free_at = float('inf')
        wait_queue = []
        next_arr = rng.expovariate(lam)
        
        area_n_win = 0.0
        busy_area_win = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        total_sojourn_win = 0.0
        wait_count_win = 0
        
        while t < horizon:
            next_dep = server_free_at if n > 0 else float('inf')
            
            if next_arr <= next_dep:
                dt = next_arr - t
                if dt > 0:
                    os = max(t, win_start)
                    oe = min(next_arr, horizon)
                    if os < oe:
                        lo = oe - os
                        area_n_win += n * lo
                        if n > 0:
                            busy_area_win += lo
                t = next_arr
                if n == 0:
                    n = 1
                    st = rng.expovariate(mu)
                    server_free_at = t + st
                    current_arrival_time = t
                    if t >= win_start:
                        arr_count_win += 1
                else:
                    n += 1
                    wait_queue.append(t)
                    if t >= win_start:
                        arr_count_win += 1
                        wait_count_win += 1
            else:
                dt = next_dep - t
                if dt > 0:
                    os = max(t, win_start)
                    oe = min(next_dep, horizon)
                    if os < oe:
                        lo = oe - os
                        area_n_win += n * lo
                        if n > 0:
                            busy_area_win += lo
                t = next_dep
                # Customer leaves
                n -= 1
                if current_arrival_time is not None:
                    sojourn = t - current_arrival_time
                    if t >= win_start:
                        dep_count_win += 1
                        total_sojourn_win += sojourn
                    current_arrival_time = None
                
                if wait_queue:
                    next_arr_time = wait_queue.pop(0)
                    n += 1  # Wait, n was decremented, now one moves from queue to service
                    # Actually n already includes the waiting ones. When one leaves, n decreases. Then one from queue enters service, n stays same? 
                    # No: n is total in system. One left -> n-1. One from queue starts service -> still in system, so n remains n-1? 
                    # Let's trace: 
                    # Before departure: n customers in system (1 in service, n-1 waiting).
                    # After departure: 1 leaves, so n-1 remain.
                    # If n-1 > 0, one starts service. Total in system is still n-1.
                    # So n should become n-1.
                    # My code did n-=1 then if wait_queue: n+=1? That would restore n. Wrong.
                    # Correction:
                    # n -= 1
                    # if wait_queue:
                    #     start service for next
                    #     n remains as is (since one left, one moved from queue to service, total unchanged from post-decrement value)
                    #     Actually: initial n. One leaves. New n = old n - 1.
                    #     If queue non-empty, one starts service. They were already counted in "old n - 1" because they were waiting.
                    #     So n is correct as old n - 1.
                    #     We just need to set up the new service.
                    
                    # Let's fix the logic:
                    # n -= 1
                    # if wait_queue:
                    #     arr_t = wait_queue.pop(0)
                    #     st = rng.expovariate(mu)
                    #     server_free_at = t + st
                    #     current_arrival_time = arr_t
                    # else:
                    #     server_free_at = float('inf')
                    #     current_arrival_time = None
                    
                    # But I already did n-=1 above. Now handle transition.
                    if wait_queue:
                        arr_t = wait_queue.pop(0)
                        st = rng.expovariate(mu)
                        server_free_at = t + st
                        current_arrival_time = arr_t
                    else:
                        server_free_at = float('inf')
                        current_arrival_time = None
                else:
                    server_free_at = float('inf')
                    current_arrival_time = None
        
        # Compute metrics for this seed
        if win_len > 0:
            L_est = area_n_win / win_len
            W_est = total_sojourn_win / dep_count_win if dep_count_win > 0 else 0.0
            busy_frac_est = busy_area_win / win_len
            p_wait_est = wait_count_win / arr_count_win if arr_count_win > 0 else 0.0
            p_loss_est = blk_count_win / arr_count_win if arr_count_win > 0 else 0.0
            dep_rate_est = dep_count_win / win_len * 60.0  # per hour, since time_unit is minute? 
            # Wait, what is time_unit? 
            # lam=6/hour, mu=10/hour (avg 6 min => 10/hr). 
            # If I use minutes internally:
            # lam_min = 6/60 = 0.1/min
            # mu_min = 10/60 = 1/6/min
            # I used lam=6.0, mu=10.0 in expovariate. That implies time unit is hours!
            # Because expovariate(rate) gives mean 1/rate. If rate=6/hr, mean interarrival=1/6 hr=10 min. Correct.
            # If rate=10/hr, mean service=1/10 hr=6 min. Correct.
            # So internal time unit is HOURS.
            # But output requires W in MINUTES.
            # So W_est is in hours. Multiply by 60.
            # dep_rate_est: dep_count_win / win_len (hours) => per hour. Already correct.
            # L is dimensionless.
            # busy_frac is dimensionless.
            
            W_est_min = W_est * 60.0
            dep_rate_per_hr = dep_count_win / win_len  # since win_len is in hours
            lam_eff = arr_count_win / win_len  # per hour
            
            # busy_util = E[min(N,c)]/c. c=1. E[N]/1 = L. So busy_util = L? 
            # No, busy_util usually means utilization = fraction of time server busy = busy_frac.
            # Prompt: busy_util=E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0. So E[min(N,1)] = P(N>=1) = busy_frac.
            # So busy_util = busy_frac.
            # busy_occupied = 1 - pi_0 = busy_frac.
            # They are identical for c=1.
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est_min)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            
            all_L.append(L_est)
            all_W.append(W_est_min)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arr_count_win)
            all_dep.append(dep_count_win)
            all_blk.append(blk_count_win)
            all_busy_util.append(busy_frac_est)
            all_busy_occupied.append(busy_frac_est)
            all_lam_eff.append(lam_eff)
            all_p_loss.append(p_loss_est)
            all_dep_rate.append(dep_rate_per_hr)
            seed_list.append(seed)
    
    seeds_used = len(per_seed_L)
    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occupied = sum(all_busy_occupied) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(avg_busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
