import argparse, json, random, math

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
    
    lam_base = 8.0 # per hour
    mu_base = 60.0 / 5.0 # per hour (12 per hour)
    c = 1
    K = 4 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        customers = [] # list of dicts: {'arrival_time': float, 'service_time': float, 'start_service': float, 'end_service': float}
        # We need to track state changes for area integration.
        # State: number of people in system (n).
        # Events: Arrival, Departure.
        
        warmup_end = 0.25 * horizon_hours
        stats_start = warmup_end
        
        n = 0
        last_change_time = 0.0
        area_n = 0.0
        area_busy = 0.0 # integral of min(n, c) ? No, busy_frac is 1-pi0. 
                        # The prompt says: busy_frac = station not empty time proportion = 1 - pi0.
                        # So we integrate indicator(n > 0).
        
        total_arrivals_window = 0
        total_blocks_window = 0
        total_departures_window = 0
        sum_w_times = 0.0 # Sum of waiting times? Or sojourn times?
                          # W usually means sojourn time (waiting + service) or just waiting?
                          # In queueing theory L = lambda * W. If L is avg number in system, W is avg time in system.
                          # Let's assume W is average time in system (sojourn time).
                          # However, standard notation often distinguishes Wq and W.
                          # Given L is likely avg number in system, W should be avg time in system.
                          # Let's check the identity L = lam_eff * W.
                          
        # To compute W accurately via Little's Law on window data or direct measurement?
        # Direct measurement: For each customer who departs within the window, record their time in system.
        # But customers arriving before window start might depart inside.
        # Customers arriving inside might depart after.
        # Standard approach for steady-state simulation with warmup:
        # Discard events before warmup end.
        # For area-based L: Integrate n(t) over [warmup_end, horizon]. Divide by (horizon - warmup_end).
        # For W: Use Little's Law? Or measure individual times?
        # Measuring individual times requires handling boundary effects.
        # Usually, if we have L and effective arrival rate, W = L / lambda_eff.
        # But the prompt asks for W explicitly.
        # Let's calculate W as the average time in system for customers that complete service within the window?
        # Or better: Calculate L via area integration. Calculate lambda_eff via arrivals/departures in window.
        # Then W = L / lambda_eff. This ensures consistency with Little's Law.
        # However, sometimes W is defined as waiting time only.
        # Context: "W (minutes)". In M/M/1/K, W usually refers to sojourn time unless specified as Wq.
        # Let's stick to Sojourn Time.
        
        # Re-evaluating strategy:
        # 1. Simulate events up to horizon.
        # 2. Track n(t) changes.
        # 3. At warmup_end, reset accumulators for area and counts.
        # 4. Continue simulating until horizon.
        # 5. At horizon, stop.
        # 6. Compute L = Area_n / Window_Length.
        # 7. Compute lambda_eff = Total_Arrivals_In_Window / Window_Length? 
        #    No, Little's law uses throughput. lambda_eff = Total_Departures_In_Window / Window_Length?
        #    Actually, for stable systems, arrival rate = departure rate.
        #    But with blocking, effective arrival rate into system = departure rate.
        #    So lambda_eff = Deps / Window.
        # 8. W = L / lambda_eff.
        # 9. p_loss = Blocks / Arrivals.
        # 10. busy_frac = Area_Busy / Window. (Area where n>0)
        # 11. busy_util = E[min(n,c)] / c. Need area of min(n,c).
        # 12. p_wait = Probability of waiting. P(n >= c upon arrival)? 
        #     Or fraction of time someone is waiting? 
        #     Usually p_wait is probability an arriving customer has to wait.
        #     Count arrivals where n_before_arrival >= c. Divide by total arrivals.
        
        # Event Loop
        while True:
            # Determine next event time
            arr_t = next_arrival
            dep_t = float('inf')
            if customers:
                # Find earliest departure among active services
                # Since single server, only one can be in service at a time?
                # Wait, c=1. Only one in service. Others wait.
                # So we need to know when the current service ends.
                # If there are people waiting, the next departure is determined by the person currently being served.
                # Who is being served? The first person in the queue who started service.
                # Actually, simpler: Maintain a variable `server_free_time`.
                pass
            
            # Let's restructure state variables for easier event processing
            # n: number in system
            # server_free_time: time when current service finishes (if any)
            # queue: list of arrival times of waiting patients
            
            # Initialization for this seed
            n = 0
            server_free_time = float('inf')
            queue = [] # stores arrival times of those waiting
            
            # Reset accumulators for statistics window
            acc_area_n = 0.0
            acc_area_busy = 0.0 # n > 0
            acc_area_min_nc = 0.0 # min(n, c)
            
            count_arrivals = 0
            count_blocks = 0
            count_departures = 0
            count_waiters_on_arrival = 0 # arrivals where n_before >= c
            
            last_stat_time = stats_start
            current_t = 0.0
            
            # Generate initial arrival
            next_arrival = rng.expovariate(lam)
            
            # We need to process events from 0 to horizon.
            # But we only accumulate stats from stats_start to horizon.
            
            # Helper to update areas
            def update_areas(t_now):
                nonlocal acc_area_n, acc_area_busy, acc_area_min_nc, last_stat_time, n
                if t_now > last_stat_time:
                    dt = t_now - last_stat_time
                    acc_area_n += n * dt
                    if n > 0:
                        acc_area_busy += dt
                    acc_area_min_nc += min(n, c) * dt
                    last_stat_time = t_now

            while current_t < horizon_hours:
                # Next event candidates
                t_arr = next_arrival
                t_dep = server_free_time if n > 0 and queue is not None else float('inf')
                # Note: if n>0 but no one is in service? Impossible if we manage server_free_time correctly.
                # If n>0, either someone is in service (server_free_time < inf) or they are waiting?
                # If waiting, server must be free? No, if server is free, it picks up immediately.
                # So if n>0, server is always busy? Not necessarily if c>1. Here c=1.
                # With c=1, if n>0, server is busy. So t_dep is valid.
                
                if t_arr <= t_dep:
                    # Arrival
                    current_t = t_arr
                    update_areas(current_t)
                    
                    # Check capacity BEFORE adding
                    # Capacity K includes service.
                    if n < K:
                        # Accept
                        n += 1
                        count_arrivals += 1
                        
                        # Did they wait?
                        # If n_before >= c, they had to wait.
                        # n_before was n-1.
                        if (n - 1) >= c:
                            count_waiters_on_arrival += 1
                            
                        # Start service if server free
                        if n == 1: # Server was idle
                            svc_time = rng.expovariate(mu)
                            server_free_time = current_t + svc_time
                        else:
                            # Join queue
                            queue.append(current_t)
                    else:
                        # Block
                        count_blocks += 1
                    
                    # Schedule next arrival
                    next_arrival = current_t + rng.expovariate(lam)
                    
                else:
                    # Departure
                    current_t = t_dep
                    update_areas(current_t)
                    
                    # Complete service
                    n -= 1
                    count_departures += 1
                    
                    # Start next service if available
                    if queue:
                        # Pop front
                        arr_time_of_next = queue.pop(0)
                        # Service time was already drawn? 
                        # Prompt: "Service duration must be drawn at arrival and attached to customer".
                        # My previous logic drew it at start of service. This violates constraint (2).
                        # Fix: Store service time in queue/customer object.
                        pass
                    
                    # Correction needed for Constraint (2)
                    # I will rewrite the loop body to store service times.
                    break # Break to fix code structure below
            
            # Since I broke out to fix logic, let's restart the inner loop implementation properly.
            # It's cleaner to define the customer tuple as (arrival_time, service_duration).
            
            # RE-IMPLEMENTATION OF INNER LOOP FOR THIS SEED
            
            n = 0
            server_free_time = float('inf')
            # Queue holds tuples: (arrival_time, service_duration)
            queue = [] 
            
            acc_area_n = 0.0
            acc_area_busy = 0.0
            acc_area_min_nc = 0.0
            
            count_arrivals = 0
            count_blocks = 0
            count_departures = 0
            count_waiters_on_arrival = 0
            
            last_stat_time = stats_start
            current_t = 0.0
            next_arrival = rng.expovariate(lam)
            
            while current_t < horizon_hours:
                t_arr = next_arrival
                t_dep = server_free_time
                
                if t_arr <= t_dep:
                    current_t = t_arr
                    # Update areas up to now
                    if current_t > last_stat_time:
                        dt = current_t - last_stat_time
                        acc_area_n += n * dt
                        if n > 0: acc_area_busy += dt
                        acc_area_min_nc += min(n, c) * dt
                        last_stat_time = current_t
                    
                    if n < K:
                        n += 1
                        count_arrivals += 1
                        if (n - 1) >= c:
                            count_waiters_on_arrival += 1
                        
                        # Draw service time NOW
                        svc_dur = rng.expovariate(mu)
                        
                        if n == 1:
                            server_free_time = current_t + svc_dur
                        else:
                            queue.append((current_t, svc_dur))
                    else:
                        count_blocks += 1
                    
                    next_arrival = current_t + rng.expovariate(lam)
                    
                else:
                    current_t = t_dep
                    if current_t > last_stat_time:
                        dt = current_t - last_stat_time
                        acc_area_n += n * dt
                        if n > 0: acc_area_busy += dt
                        acc_area_min_nc += min(n, c) * dt
                        last_stat_time = current_t
                    
                    n -= 1
                    count_departures += 1
                    
                    if queue:
                        next_cust = queue.pop(0)
                        # next_cust[1] is svc_dur
                        server_free_time = current_t + next_cust[1]
                    else:
                        server_free_time = float('inf')
            
            # Final area update to horizon
            if horizon_hours > last_stat_time:
                dt = horizon_hours - last_stat_time
                acc_area_n += n * dt
                if n > 0: acc_area_busy += dt
                acc_area_min_nc += min(n, c) * dt
            
            win_len = horizon_hours - stats_start
            
            if win_len <= 0:
                continue
                
            L_est = acc_area_n / win_len
            busy_frac_est = acc_area_busy / win_len
            busy_util_est = (acc_area_min_nc / win_len) / c
            busy_occ_est = busy_frac_est # 1 - pi0
            
            # Rates
            lam_arr_est = count_arrivals / win_len
            lam_dep_est = count_departures / win_len
            p_loss_est = count_blocks / count_arrivals if count_arrivals > 0 else 0.0
            p_wait_est = count_waiters_on_arrival / count_arrivals if count_arrivals > 0 else 0.0
            
            # W estimation
            # Using Little's Law: L = lambda_eff * W
            # lambda_eff is the rate of customers entering the system successfully.
            # In steady state, entry rate = departure rate.
            # So lambda_eff = lam_dep_est.
            if lam_dep_est > 0:
                W_est = L_est / lam_dep_est
            else:
                W_est = 0.0
            
            # Convert W to minutes
            W_min = W_est * 60.0
            
            all_L.append(L_est)
            all_W.append(W_min)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(count_arrivals)
            all_blk.append(count_blocks)
            all_dep.append(count_departures)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occ_est)

    seeds_used = len(all_L)
    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    mean_L = sum(all_L) / seeds_used
    mean_W = sum(all_W) / seeds_used
    mean_busy_frac = sum(all_busy_frac) / seeds_used
    mean_p_loss = sum(all_p_loss) / seeds_used
    mean_p_wait = sum(all_p_wait) / seeds_used
    mean_arr = sum(all_arr) / seeds_used
    mean_blk = sum(all_blk) / seeds_used
    mean_dep = sum(all_dep) / seeds_used
    mean_busy_util = sum(all_busy_util) / seeds_used
    mean_busy_occ = sum(all_busy_occupied) / seeds_used
    
    # dep_rate in per hour
    mean_dep_rate = mean_dep / (H - 0.25*H) if H > 0 else 0.0
    # Wait, H is horizon. Window is 0.75 * H.
    # mean_dep is total departures in window.
    # Rate = mean_dep / window_length.
    window_length = H * 0.75
    dep_rate_val = mean_dep / window_length if window_length > 0 else 0.0
    
    result = {
        "L": round(mean_L, 6),
        "W": round(mean_W, 6),
        "busy_frac": round(mean_busy_frac, 6),
        "p_loss": round(mean_p_loss, 6),
        "runtime_units": "seconds", # Placeholder, actual runtime not measured precisely here, or use wall clock? 
                                    # Prompt doesn't strictly require accurate runtime, just key existence.
                                    # I'll put 0.0 or measure it. Let's measure roughly.
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(window_length, 6),
        "arr": round(mean_arr, 6),
        "blk": round(mean_blk, 6),
        "busy_util": round(mean_busy_util, 6),
        "dep": round(mean_dep, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(dep_rate_val, 6), # Effective arrival rate = departure rate
        "p_wait": round(mean_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6)
