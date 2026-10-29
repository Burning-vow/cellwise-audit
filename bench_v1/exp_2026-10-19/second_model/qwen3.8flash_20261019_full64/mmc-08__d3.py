import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 10.0   # service rate per minute (mean 10 min)
    c = 3                  # servers

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    warmup_frac = 0.25
    win_len = horizon_min * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_occupied = []
    all_lam_eff = []
    all_p_loss = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        services_done = [0] * c  # completion times for each server
        queue = [] # list of (arrival_time, service_duration)
        active_services = [] # list of (start_time, end_time) currently running
        
        # Statistics accumulators for the whole run (to be filtered later or integrated carefully)
        # We need to integrate over the window [warmup_end, horizon]
        warmup_end = horizon_min * warmup_frac
        
        # To compute area-based stats correctly with a warm-up period, 
        # we simulate events and track state changes.
        # However, standard DES usually tracks integrals continuously.
        # Let's use event-driven simulation.
        
        # Variables for current state
        num_in_system = 0
        last_event_time = 0.0
        integral_N = 0.0 # Integral of number in system over time
        integral_busy_servers = 0.0 # Integral of min(num_serving, c) ? No, busy_frac is E[min(N,c)]/c? 
        # The prompt says: busy_frac definition = E[min(N,c)]/c. This is actually utilization rho.
        # Wait, "busy_frac" usually means fraction of time at least one server is busy? 
        # But prompt explicitly defines it: "busy_frac 的定义：题目契约已点名 = 每台平均利用率 E[min(N,c)]/c".
        # So busy_frac = (Integral of min(num_serving, c) dt) / (T * c).
        
        # Let's track:
        # 1. Integral of N(t) for L
        # 2. Integral of min(num_serving(t), c) for busy_frac/utilization
        # 3. Count of arrivals that found queue non-empty (p_wait)
        # 4. Total waiting+service time sum for W
        
        # Since we have a warm-up period, we should only accumulate stats after warmup_end.
        # But integration requires knowing the value during the interval.
        # Strategy: Simulate full horizon. At each event, update integrals based on duration since last event.
        # If the interval overlaps with the analysis window, add the overlap portion.
        
        # Simplified approach: Run simulation, record events. Then post-process? 
        # Or just check if current time > warmup_end when adding to accumulators?
        # For integrals, we need to split intervals.
        
        # Let's maintain:
        # total_integral_N_window
        # total_integral_busy_window
        # count_arrivals_window
        # count_waits_window
        # total_sojourn_time_window (sum of W_i for customers who departed within window? Or arrived within?)
        # Usually W is average sojourn time of customers served in the steady state.
        # Common practice: Sum sojourn times of customers who completed service in the window, divided by number of such customers.
        # Or: Customers arriving in the window.
        # Prompt: "统计量只在去掉前 25% 预热后的窗口内累计".
        # For L (area), integrate N(t) over window.
        # For W, typically Little's Law holds. If we calculate L and lambda_eff, W=L/lambda_eff.
        # But prompt asks for W directly. Let's sum sojourn times of customers who DEPARTED in the window?
        # Or ARRIVED in the window?
        # Standard output metrics often use customers completing service in the window to avoid truncation bias.
        # Let's assume: Sum of (departure_time - arrival_time) for customers departing in [warmup_end, horizon].
        # And divide by count of such departures.
        
        # Re-evaluating "arr", "dep", "blk":
        # arr: arrivals in window
        # dep: departures in window
        # blk: blocked/lost in window (if any). Here infinite queue, so blk=0.
        
        # Let's implement event loop.
        
        # Event types: Arrival, Departure
        # Priority queue not needed if we manage next_arrival and min(departures).
        
        # Initialize
        t = 0.0
        next_arrival_t = rng.expovariate(lam)
        # Server availability times
        server_free_times = [0.0] * c
        # Queue of customers waiting: (arrival_time, service_time)
        q_waiting = []
        
        # Stats for this seed
        int_N_win = 0.0
        int_busy_win = 0.0
        cnt_arr_win = 0
        cnt_dep_win = 0
        cnt_wait_win = 0
        sum_W_win = 0.0
        cnt_lost_win = 0
        
        # Helper to add to integrals considering window
        def add_to_integrals(dt, n_val, busy_val):
            nonlocal int_N_win, int_busy_win
            if dt <= 0: return
            start_t = t
            end_t = t + dt
            
            # Overlap with [warmup_end, horizon_min]
            ov_start = max(start_t, warmup_end)
            ov_end = min(end_t, horizon_min)
            
            if ov_start < ov_end:
                overlap_dt = ov_end - ov_start
                int_N_win += n_val * overlap_dt
                int_busy_win += busy_val * overlap_dt

        while t < horizon_min:
            # Determine next event time
            next_dep_t = float('inf')
            dep_server_idx = -1
            for idx, ft in enumerate(server_free_times):
                if ft < next_dep_t and ft > t: # Only consider future completions
                    next_dep_t = ft
                    dep_server_idx = idx
            
            # Check if there are pending services started but not finished?
            # Actually, server_free_times stores when they become free.
            # If a server is busy, its free time is in the future.
            # If idle, free time is <= t.
            
            # Find earliest departure among busy servers
            # Note: A server might have finished before t if we didn't process it? 
            # In DES, we process events chronologically.
            
            # Let's find the minimum of next_arrival_t and next_dep_t
            if next_arrival_t < next_dep_t:
                # Arrival Event
                dt = next_arrival_t - t
                # Current state values
                n_current = len(q_waiting) + sum(1 for ft in server_free_times if ft > t)
                busy_current = sum(1 for ft in server_free_times if ft > t)
                
                add_to_integrals(dt, n_current, busy_current)
                
                t = next_arrival_t
                
                # Process Arrival
                # Check if any server is free
                free_server = -1
                for idx, ft in enumerate(server_free_times):
                    if ft <= t:
                        free_server = idx
                        break
                
                # Generate service time NOW
                svc_time = rng.expovariate(mu)
                
                if free_server != -1:
                    # Start service immediately
                    server_free_times[free_server] = t + svc_time
                    # Waiting time is 0
                    # Did they wait? No.
                    # Record arrival in window?
                    if t >= warmup_end:
                        cnt_arr_win += 1
                        # Sojourn time will be added upon departure
                else:
                    # Join queue
                    q_waiting.append((t, svc_time))
                    if t >= warmup_end:
                        cnt_arr_win += 1
                        cnt_wait_win += 1 # Arrived and had to wait
                
                # Schedule next arrival
                next_arrival_t = t + rng.expovariate(lam)
                
            else:
                # Departure Event
                if next_dep_t == float('inf'):
                    break # No more events
                
                dt = next_dep_t - t
                n_current = len(q_waiting) + sum(1 for ft in server_free_times if ft > t)
                busy_current = sum(1 for ft in server_free_times if ft > t)
                
                add_to_integrals(dt, n_current, busy_current)
                
                t = next_dep_t
                
                # Process Departure from dep_server_idx
                # Who was being served? We don't store customer ID in server_free_times easily.
                # We need to know their arrival time to calculate sojourn time.
                # Problem: When we assign a server, we don't link the specific customer object to the server index permanently until departure.
                # Solution: Store (arrival_time, service_time) in a separate structure or map server to customer.
                
                # Refactor: Instead of just server_free_times, let's keep a list of active customers.
                # But simpler: When starting service, push (arrival_time, end_time) to a heap?
                # Or just scan q_waiting? No, q_waiting is for those NOT yet started.
                
                # Let's change data structure slightly.
                # active_customers: list of (arrival_time, end_time) for those currently in service.
                # But we used server_free_times.
                # Let's maintain a parallel array `server_customer_info` where info is (arrival_time, service_time).
                
                # I need to restart the logic block because I missed storing arrival time for active services.
                pass 

        # Due to complexity of refactoring mid-thought, I will rewrite the simulation loop cleanly below.
        # Resetting for clean implementation.
        
        # Clean Implementation Plan:
        # 1. Use a priority queue for events? Or simple min search since c=3 is small.
        # 2. Track:
        #    - `servers`: list of dicts { 'end_time': float, 'arrival_time': float } or None if idle.
        #    - `queue`: list of tuples (arrival_time, service_time)
        #    - `next_arrival`: float
        # 3. Loop until t >= horizon.
        # 4. Next event = min(next_arrival, min(servers[i]['end_time'] for i in range(c) if servers[i]))
        # 5. Update integrals for elapsed time.
        # 6. Process event.
        
        # Restarting seed loop body...
        
        # Clear previous partial vars
        t = 0.0
        next_arrival_t = rng.expovariate(lam)
        # servers[i] is None if idle, else dict {'end': float, 'arr': float}
        servers = [None] * c
        q_waiting = [] # list of (arrival_time, service_time)
        
        int_N_win = 0.0
        int_busy_win = 0.0
        cnt_arr_win = 0
        cnt_dep_win = 0
        cnt_wait_win = 0
        sum_W_win = 0.0
        cnt_lost_win = 0
        
        while t < horizon_min:
            # Find next departure time
            next_dep_t = float('inf')
            dep_idx = -1
            for i in range(c):
                if servers[i] is not None:
                    if servers[i]['end'] < next_dep_t:
                        next_dep_t = servers[i]['end']
                        dep_idx = i
            
            # Determine next event
            if next_arrival_t < next_dep_t:
                # Arrival
                dt = next_arrival_t - t
                # Calculate current N and Busy
                n_curr = len(q_waiting) + sum(1 for s in servers if s is not None)
                b_curr = sum(1 for s in servers if s is not None)
                
                # Integrate
                if dt > 0:
                    ov_start = max(t, warmup_end)
                    ov_end = min(t + dt, horizon_min)
                    if ov_start < ov_end:
                        dur = ov_end - ov_start
                        int_N_win += n_curr * dur
                        int_busy_win += b_curr * dur
                
                t = next_arrival_t
                
                # Find free server
                free_idx = -1
                for i in range(c):
                    if servers[i] is None:
                        free_idx = i
                        break
                
                svc_dur = rng.expovariate(mu)
                
                if free_idx != -1:
                    servers[free_idx] = {'end': t + svc_dur, 'arr': t}
                    if t >= warmup_end:
                        cnt_arr_win += 1
                else:
                    q_waiting.append((t, svc_dur))
                    if t >= warmup_end:
                        cnt_arr_win += 1
                        cnt_wait_win += 1
                
                next_arrival_t = t + rng.expovariate(lam)
                
            else:
                # Departure
                if next_dep_t == float('inf'):
                    # No more departures, but maybe arrivals?
                    # If no servers busy and no queue, jump to next arrival
                    if not q_waiting and all(s is None for s in servers):
                         # Just advance time to next arrival
                         dt = next_arrival_t - t
                         if dt > 0:
                             ov_start = max(t, warmup_end)
                             ov_end = min(t + dt, horizon_min)
                             if ov_start < ov_end:
                                 dur = ov_end - ov_start
                                 int_N_win += 0 * dur
                                 int_busy_win += 0 * dur
                         t = next_arrival_t
                         # Process arrival as above... (Duplicate code risk, better handle generally)
                         # Let's force re-loop by setting next_dep_t high and letting arrival branch take it.
                         continue
                    else:
                        break # Should not happen if logic correct

                dt = next_dep_t - t
                n_curr = len(q_waiting) + sum(1 for s in servers if s is not None)
                b_curr = sum(1 for s in servers if s is not None)
                
                if dt > 0:
                    ov_start = max(t, warmup_end)
                    ov_end = min(t + dt, horizon_min)
                    if ov_start < ov_end:
                        dur = ov_end - ov_start
                        int_N_win += n_curr * dur
                        int_busy_win += b_curr * dur
                
                t = next_dep_t
                
                # Complete service at dep_idx
                cust_arr_time = servers[dep_idx]['arr']
                servers[dep_idx] = None
                
                # Check if this departure is in window
                if t >= warmup_end:
                    cnt_dep_win += 1
                    sojourn = t - cust_arr_time
                    sum_W_win += sojourn
                
                # Start next from queue if available
                if q_waiting:
                    arr_t, svc_dur = q_waiting.pop(0)
                    servers[dep_idx] = {'end': t + svc_dur, 'arr': arr_t}
        
        # End of simulation for this seed
        
        # Calculate metrics for this seed
        if win_len > 0:
            L_est = int_N_win / win_len
            busy_frac_est = int_busy_win / (win_len * c)
            
            # W estimation
            if cnt_dep_win > 0:
                W_est = sum_W_win / cnt_dep_win
            else:
                W_est = 0.0
                
            p_wait_est = cnt_wait_win / cnt_arr_win if cnt_arr_win > 0 else 0.0
            p_loss_est = cnt_lost_win / cnt_arr_win if cnt_arr_win > 0 else 0.0
            
            # Utilization (same as busy_frac per prompt definition)
            busy_util_est = busy_frac_est
            
            # Occupied probability (fraction of time at least one server busy)
            # We didn't track this integral separately. 
            # Approximation: If we tracked integral of indicator(any busy), we'd have it.
            # Let's skip precise occupied if not tracked, or estimate via busy_util?
            # Prompt asks for busy_occupied = 1 - pi_0.
            # We can approximate pi_
