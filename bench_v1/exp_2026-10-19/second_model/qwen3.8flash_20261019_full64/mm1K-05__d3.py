import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours
    lam_base = 9.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 h = 10 per hour
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
        mu = mu_base
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
    
    c_max = 4 # Capacity including service

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    
    total_time_units = 0.0
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Queue and Service tracking
        # We need to track customers in system (waiting + serving)
        # Since it's MM1K, we can just track count N.
        # But for W, we need arrival times of those who eventually depart within window? 
        # Or standard area-based L and flow balance?
        # The prompt asks for W (average waiting time in system).
        # Standard definition: W = L / lambda_eff (Little's Law) or sum(time_in_system)/count_departures.
        # Given "area型量必须在改变状态之前积分", let's use event-driven simulation with proper accounting.
        
        n_customers = 0
        # To calculate W accurately via simulation, we usually track departure events.
        # However, truncating at Horizon makes exact W tricky if a customer is still in system.
        # Common practice: Only count completed services for W, or use Little's law on steady state stats.
        # Let's stick to: W = (Total time spent by all customers who departed during the window) / (Number of departures in window).
        # But wait, if a customer arrives before warmup and departs after, do we count them?
        # Warmup removes first 25%. So we start collecting stats at T_warm = 0.25 * H.
        # Customers present at T_warm are part of the initial state for the measurement window.
        # Their remaining time contributes to L (area), but their full W is not known unless they depart.
        # Usually, for discrete event sim, we track:
        # 1. Area under N(t) curve for L.
        # 2. For W, we sum (departure_time - arrival_time) for each departure that occurs in the window.
        #    If an arrival happened before the window started, its arrival time is unknown to the window logic unless we simulate from 0.
        #    We simulate from 0.
        
        # Data structures for pending customers to calculate W
        # We need to know when they arrived.
        # Since capacity is small, we can store arrival times of people currently in system.
        # When someone leaves, we pop the earliest arrival? No, FCFS.
        # In M/M/1/K, service order is FCFS.
        
        queue_arrivals = [] # List of arrival times of people in system (including one in service)
        
        # Stats accumulators for this seed
        area_N = 0.0
        last_event_time = 0.0
        
        # Warmup cutoff
        t_warm = 0.25 * H
        
        # Counters for the window [t_warm, H]
        # Note: Events happening exactly at boundaries need care. Usually [start, end).
        
        arr_count_win = 0
        blk_count_win = 0
        dep_count_win = 0
        sum_W_win = 0.0 # Sum of sojourn times for departures in window
        
        # We also need to handle customers already in system at t_warm.
        # They contribute to L (area) immediately.
        # Do they contribute to W? Only if they depart in the window.
        # If they depart in the window, their arrival was < t_warm. We have their arrival time stored.
        
        # Initialize simulation from 0 to H
        # We must run from 0 to capture the state at t_warm correctly.
        
        # Reset for new seed
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        n_customers = 0
        queue_arrivals = []
        area_N = 0.0
        last_event_time = 0.0
        
        # Pre-simulation variables to help with windowing
        # We will iterate events until t >= H
        
        while True:
            # Determine next event time
            t_next = min(next_arrival, next_departure)
            
            if t_next > H:
                break
            
            # Update area for L calculation
            # Area += N * (t_next - last_event_time)
            # But we only want area in the window [t_warm, H]?
            # Prompt: "统计量只在去掉前 25% 预热后的窗口内累计"
            # So L should be average N over [t_warm, H].
            # We need to integrate N(t) over [t_warm, H].
            
            dt = t_next - last_event_time
            if dt > 0:
                # Calculate overlap with window [t_warm, H]
                win_start = max(last_event_time, t_warm)
                win_end = min(t_next, H)
                if win_end > win_start:
                    area_N += n_customers * (win_end - win_start)
            
            last_event_time = t_next
            t = t_next
            
            # Process Event
            if t == next_arrival:
                # Arrival
                if n_customers < c_max:
                    # Accept
                    n_customers += 1
                    queue_arrivals.append(t)
                    
                    # Check if server becomes busy
                    if n_customers == 1:
                        # Start service
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                    
                    # Window counting
                    if t >= t_warm:
                        arr_count_win += 1
                else:
                    # Blocked
                    if t >= t_warm:
                        blk_count_win += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif t == next_departure:
                # Departure
                if n_customers > 0:
                    # Remove first customer (FCFS)
                    arrival_time = queue_arrivals.pop(0)
                    n_customers -= 1
                    
                    # Calculate sojourn time
                    sojourn = t - arrival_time
                    
                    # Window counting for W and Dep
                    if t >= t_warm:
                        dep_count_win += 1
                        sum_W_win += sojourn
                    
                    # If more customers waiting, start next service
                    if n_customers > 0:
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                    else:
                        next_departure = float('inf')
                else:
                    # Should not happen if logic correct, but safety
                    next_departure = float('inf')

        # End of simulation loop
        
        # Final area update if last_event_time < H? 
        # The loop breaks when t_next > H. 
        # The area up to H has been accounted for in the step where t_next > H?
        # No, the loop condition `if t_next > H: break` happens BEFORE updating area for the interval ending at H.
        # We need to add the area from last_event_time to H.
        
        dt_final = H - last_event_time
        if dt_final > 0:
            win_start = max(last_event_time, t_warm)
            win_end = H
            if win_end > win_start:
                area_N += n_customers * (win_end - win_start)
        
        window_length = H - t_warm
        
        # Compute metrics for this seed
        if window_length > 0:
            L_val = area_N / window_length
        else:
            L_val = 0.0
            
        if dep_count_win > 0:
            W_val = sum_W_win / dep_count_win
        else:
            W_val = 0.0
            
        # Busy fraction: Time server is busy / Window length
        # Server is busy if n_customers > 0.
        # We didn't explicitly track busy area. 
        # We can derive it or re-calculate. 
        # Let's re-calculate busy area properly.
        # Actually, easier to track busy_area alongside area_N.
        
        # Re-run logic mentally: I missed tracking busy_area.
        # Let's fix the accumulation inside the loop.
        
        # Since I cannot go back and edit the loop structure easily without rewriting,
        # I will rewrite the inner loop to include busy_area tracking.
        
        pass 

    # Rewriting the core simulation block for clarity and correctness regarding busy_area
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    
    total_time_units = 0.0
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        n_customers = 0
        queue_arrivals = []
        
        area_N = 0.0
        area_Busy = 0.0 # Time server is occupied (n>0)
        last_event_time = 0.0
        
        t_warm = 0.25 * H
        
        arr_count_win = 0
        blk_count_win = 0
        dep_count_win = 0
        sum_W_win = 0.0
        
        while True:
            t_next = min(next_arrival, next_departure)
            
            if t_next > H:
                break
            
            dt = t_next - last_event_time
            if dt > 0:
                win_start = max(last_event_time, t_warm)
                win_end = min(t_next, H)
                if win_end > win_start:
                    duration = win_end - win_start
                    area_N += n_customers * duration
                    if n_customers > 0:
                        area_Busy += duration
            
            last_event_time = t_next
            t = t_next
            
            if t == next_arrival:
                if n_customers < c_max:
                    n_customers += 1
                    queue_arrivals.append(t)
                    if n_customers == 1:
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                    if t >= t_warm:
                        arr_count_win += 1
                else:
                    if t >= t_warm:
                        blk_count_win += 1
                next_arrival = t + rng.expovariate(lam)
                
            elif t == next_departure:
                if n_customers > 0:
                    arrival_time = queue_arrivals.pop(0)
                    n_customers -= 1
                    sojourn = t - arrival_time
                    if t >= t_warm:
                        dep_count_win += 1
                        sum_W_win += sojourn
                    if n_customers > 0:
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')

        dt_final = H - last_event_time
        if dt_final > 0:
            win_start = max(last_event_time, t_warm)
            win_end = H
            if win_end > win_start:
                duration = win_end - win_start
                area_N += n_customers * duration
                if n_customers > 0:
                    area_Busy += duration
        
        window_length = H - t_warm
        
        L_val = area_N / window_length if window_length > 0 else 0.0
        W_val = sum_W_win / dep_count_win if dep_count_win > 0 else 0.0
        busy_frac_val = area_Busy / window_length if window_length > 0 else 0.0
        
        # p_loss: blocked / (arrived + blocked)? Or blocked / total attempts?
        # Total attempts in window = arr_count_win + blk_count_win
        total_attempts = arr_count_win + blk_count_win
        p_loss_val = blk_count_win / total_attempts if total_attempts > 0 else 0.0
        
        # p_wait: Probability of waiting. 
        # In M/M/1/K, P(wait) = P(N>=1) ? No, P(wait) usually means P(arrival finds server busy).
        # Or P(N>=1) in steady state?
        # Let's define p_wait as the fraction of accepted arrivals that had to wait (server busy upon arrival).
        # We didn't track this directly. 
        # Alternative interpretation: P(N>=1) which is busy_frac.
        # Or P(N>=2) for queueing?
        # Standard metric often requested: P(wait) = P(server busy) = busy_frac.
        # But sometimes it means P(queue non-empty).
        # Given the ambiguity, and "busy_occupied=1-pi0", let's assume p_wait refers to the probability an arriving customer waits.
        # This requires checking state at arrival.
        # Let's approximate p_wait using Little's Law or just set it to busy_frac if strict definition isn't clear.
        # However, we can compute it: 
        # We need count of arrivals where n_customers > 0 (before increment).
        # I didn't store that. 
        # Let's look at the output requirements again.
        # "p_wait" is listed.
        # In many contexts, p_wait = P(W > 0).
        # For M/M/1, P(W>0) = rho. For M/M/1/K, it's complex.
        # Let's use the empirical measure: Fraction of accepted arrivals that found the server busy.
        # I need to modify the loop to count this.
        
        # Re-modifying loop to count wait_events
        # I will restart the seed loop code generation to include this.
        
        pass

    # Final clean implementation
    
    import sys, json, random, argparse

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--seeds', type=int, default=1)
        parser.add_argument('--horizon', type=float, default=100.0)
        parser.add_argument('--seed-start', type=int, default=42)
        parser.add_argument('--pert', type=str, default='none')
        args = parser.parse_args()

        N_seeds = args.seeds
        H = args.horizon
        S_start = args.seed_start
        pert = args.pert

        lam_base = 9.0
        mu_base = 10.0 
        
        if pert == 'lam_up':
            lam = lam_base * 1.1
            mu = mu_base
        elif pert == 'mu_up':
            lam = lam_base
            mu = mu_base * 1.1
        elif pert == 'c_up':
            lam = lam_base
            mu = mu_base
        else:
            lam = lam_base
            mu = mu_base
        
        c_max = 4

        res_L = []
        res_W = []
        res_busy = []
        res_ploss = []
        res_pwait = []
        res_arr = []
        res_blk = []
        res_dep = []
        
        seed_list = []

        for i in range(N_seeds):
            seed = S_start + i
            seed_list.append(seed)
            rng = random.Random(seed)
            
            t = 0.0
            next_arr = rng.expovariate(lam)
            next_dep = float('inf')
            
            n_cust = 0
            q_arrs = []
            
            area_n = 0.0
            area_busy = 0.0
            last_t = 0.0
            
            t_warm = 0.25 * H
            
            cnt_arr = 0
            cnt_blk = 0
            cnt_dep = 0
            sum_w = 0.0
            cnt_wait = 0 # Accepted arrivals that waited
            
            while True:
                t_next = min(next_arr, next_dep)
                if t_next > H:
                    break
                
                dt = t_next - last_t
                if dt > 0:
                    ws = max(last_t
