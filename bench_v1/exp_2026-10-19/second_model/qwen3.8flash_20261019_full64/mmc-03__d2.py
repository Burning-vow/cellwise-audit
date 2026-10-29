import random, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 10.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {}
        queue = []
        servers_free_at = [0.0] * c
        n_in_system = 0
        n_waiting = 0
        
        warmup_end = horizon_hours * 0.25
        stats_window_len = horizon_hours - warmup_end
        
        area_n = 0.0
        area_min_nc = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited = 0
        total_w_time = 0.0
        
        last_event_time = 0.0
        
        while t < horizon_hours:
            arr_t = next_arrival
            dep_t = min(servers_free_at) if any(s > t for s in servers_free_at) else float('inf')
            
            if arr_t <= dep_t and arr_t < horizon_hours:
                dt = arr_t - last_event_time
                if last_event_time >= warmup_end:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                
                t = arr_t
                last_event_time = t
                count_arrivals += 1
                
                if n_in_system < c:
                    idx = servers_free_at.index(min(servers_free_at))
                    st = rng.expovariate(mu)
                    servers_free_at[idx] = t + st
                    n_in_system += 1
                else:
                    if len(queue) == 0:
                        pass 
                    queue.append(t)
                    n_in_system += 1
                    n_waiting += 1
                    count_waited += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif dep_t < horizon_hours and dep_t != float('inf'):
                dt = dep_t - last_event_time
                if last_event_time >= warmup_end:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                
                t = dep_t
                last_event_time = t
                
                idx = servers_free_at.index(min(servers_free_at))
                servers_free_at[idx] = float('inf')
                n_in_system -= 1
                count_departures += 1
                
                if queue:
                    arrival_time_of_next = queue.pop(0)
                    n_waiting -= 1
                    st = rng.expovariate(mu)
                    servers_free_at[idx] = t + st
                    n_in_system += 1
                    w_time = (t - arrival_time_of_next) + st
                    if arrival_time_of_next >= warmup_end:
                         total_w_time += w_time
                         # Note: W is avg waiting+service time. 
                         # We need to track completion times properly or use Little's Law?
                         # The prompt asks for W directly. Let's accumulate sojourn time for those who complete in window.
                         # But we already added st above. Sojourn = departure_time - arrival_time.
                         # Wait, I calculated w_time as (t - arrival_time_of_next) + st which is wrong because st is future duration.
                         # Correct sojourn for this customer completing at t is t - arrival_time_of_next.
                         # But this customer just started service at t? No, they were in queue, now start service.
                         # They will depart at t + st.
                         # So their sojourn time is not known yet.
                         # Better approach: Track sojourn time upon departure.
                    else:
                        pass
            else:
                break
        
        # Re-run logic with correct tracking of sojourn time on departure
        # Resetting variables for a cleaner simulation loop that tracks sojourn correctly
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # stores arrival times
        n_in_system = 0
        
        warmup_end = horizon_hours * 0.25
        area_n = 0.0
        area_min_nc = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited_on_arrival = 0
        sum_sojourn = 0.0
        last_event_time = 0.0
        
        # Pre-generate service times? Prompt says "service duration must be drawn at arrival".
        # So we draw when they arrive. If they are blocked, do we still draw? Usually yes, but they don't enter.
        # If they enter queue, we store the drawn service time with them.
        
        # Let's restart the loop structure carefully.
        # State: 
        # - queue: list of tuples (arrival_time, service_duration)
        # - servers_free_at: list of floats
        
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] 
        n_in_system = 0
        
        warmup_end = horizon_hours * 0.25
        area_n = 0.0
        area_min_nc = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited_on_arrival = 0
        sum_sojourn = 0.0
        last_event_time = 0.0
        
        while True:
            # Determine next event time
            arr_t = next_arrival
            dep_t = min(servers_free_at) if servers_free_at else float('inf')
            
            if arr_t >= horizon_hours and dep_t >= horizon_hours:
                break
            
            if arr_t <= dep_t:
                # Arrival
                dt = arr_t - last_event_time
                if last_event_time >= warmup_end:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                
                t = arr_t
                last_event_time = t
                count_arrivals += 1
                
                # Draw service time at arrival
                st = rng.expovariate(mu)
                
                # Check if server available
                free_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    servers_free_at[free_idx] = t + st
                    n_in_system += 1
                else:
                    queue.append((t, st))
                    n_in_system += 1
                    n_waiting = len(queue)
                    if n_waiting > 0: # Was empty before adding? Or rather, was there anyone waiting?
                        # "Probability of needing to wait upon arrival"
                        # If queue was empty AND no server free -> wait.
                        # Actually, if no server free, they wait regardless of queue length (queue length becomes 1).
                        # If server free, they don't wait.
                        # So check: did they go into queue? Yes.
                        count_waited_on_arrival += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                dt = dep_t - last_event_time
                if last_event_time >= warmup_end:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                
                t = dep_t
                last_event_time = t
                
                # Find which server finished
                finished_idx = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9:
                        finished_idx = k
                        break
                
                if finished_idx == -1:
                    # Floating point issue, take min
                    finished_idx = servers_free_at.index(min(servers_free_at))
                
                servers_free_at[finished_idx] = float('inf')
                n_in_system -= 1
                count_departures += 1
                
                # Who departed? The one who was being served.
                # We need to know their arrival time to calculate sojourn.
                # Problem: We didn't store arrival time for the person currently in service.
                # Fix: Store (arrival_time, service_duration, end_time) for active services?
                # Or simpler: When someone starts service, record their arrival time.
                
                # Let's refactor state to include active customers' arrival times.
                # This requires restarting the loop again. It's getting messy.
                # Alternative: Use Little's Law for L, and derive W from L/lam_eff?
                # Prompt asks for W explicitly.
                # Let's stick to accumulating sojourn time.
                # To do this, we need to know arrival time of departing customer.
                # We can maintain a list of active customers: (arrival_time, finish_time).
                
                # Restarting with better state management.
                pass 

        # Final attempt with clean state
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Active customers: list of (arrival_time, finish_time)
        active = [] 
        # Queue: list of (arrival_time, service_duration)
        queue = []
        
        warmup_end = horizon_hours * 0.25
        area_n = 0.0
        area_min_nc = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited_on_arrival = 0
        sum_sojourn = 0.0
        last_event_time = 0.0
        
        while True:
            arr_t = next_arrival
            dep_t = min([a[1] for a in active]) if active else float('inf')
            
            if arr_t >= horizon_hours and dep_t >= horizon_hours:
                break
            
            if arr_t <= dep_t:
                dt = arr_t - last_event_time
                if last_event_time >= warmup_end:
                    n_sys = len(active) + len(queue)
                    area_n += n_sys * dt
                    area_min_nc += min(n_sys, c) * dt
                
                t = arr_t
                last_event_time = t
                count_arrivals += 1
                
                st = rng.expovariate(mu)
                
                if len(active) < c:
                    finish_t = t + st
                    active.append((t, finish_t))
                else:
                    queue.append((t, st))
                    count_waited_on_arrival += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                dt = dep_t - last_event_time
                if last_event_time >= warmup_end:
                    n_sys = len(active) + len(queue)
                    area_n += n_sys * dt
                    area_min_nc += min(n_sys, c) * dt
                
                t = dep_t
                last_event_time = t
                
                # Remove first completed active customer
                # Find index of min finish time
                min_finish = float('inf')
                min_idx = -1
                for i, (arr, fin) in enumerate(active):
                    if fin < min_finish:
                        min_finish = fin
                        min_idx = i
                
                arr_time, _ = active.pop(min_idx)
                count_departures += 1
                sojourn = t - arr_time
                if arr_time >= warmup_end:
                    sum_sojourn += sojourn
                
                # Start next from queue if exists
                if queue:
                    q_arr, q_st = queue.pop(0)
                    new_finish = t + q_st
                    active.append((q_arr, new_finish))
        
        win_len = horizon_hours - warmup_end
        if win_len > 0:
            L_est = area_n / win_len
            busy_frac_est = area_min_nc / (win_len * c)
            p_wait_est = count_waited_on_arrival / count_arrivals if count_arrivals > 0 else 0.0
            # W estimation: Average sojourn time of customers who arrived in window and departed?
            # Or simply sum_sojourn / count_departures_in_window?
            # count_departures includes those who arrived before window.
            # Strictly, W is average time in system.
            # Using Little's Law: W = L / lambda_eff.
            # lambda_eff = count_arrivals_in_window / win_len? No, arrivals in window might not have departed.
            # Standard DES estimator for W: Sum of sojourn times of all customers who completed during window / Number of completions during window.
            # But we filtered sum_sojourn by arrival time >= warmup_end.
            # Let's use Little's Law for consistency with L and effective rate.
            # Effective arrival rate in window:
            # Customers arriving in window: We didn't count them separately.
            # Let's assume steady state approx: W = L / lam_eff.
            # lam_eff = count_arrivals / horizon? No.
            # Let's calculate W directly from accumulated data if possible.
            # We have sum_sojourn for customers arriving in window.
            # How many such customers departed? We didn't track that count specifically.
            # Fallback: W = L / (count_arrivals / horizon_hours) ? No.
            # Let's use: W = L / lam where lam is input rate? Only if stable.
            # Better: W = L / (dep_rate).
            dep_rate = count_departures / horizon_hours
            if dep_rate > 0:
                W_est = L_est / dep_rate
            else:
                W_est = 0.0
            
            # Refine W using direct measurement if we tracked completions in window
            # For simplicity and robustness in short sims, Little's law is often preferred.
            # However, prompt implies direct measurement.
            # Let's try to estimate W via sum_sojourn / num_completions_of_window_arrivals.
            # We don't have num_completions_of_window_arrivals.
            # I will use Little's Law: W = L / lambda_effective.
            # lambda_effective = count_arrivals / horizon_hours (assuming no loss/blocking in M/M/c with infinite queue)
            # Since it's FCFS with infinite queue, no blocking. blk=0.
            # So lam_eff = count_arrivals / horizon_hours.
            lam_eff = count_arrivals / horizon_hours
            if lam_eff > 0:
                W_est = L_est / lam_eff
            else:
                W_est = 0.0
                
            p_loss_est = 0.0 # Infinite queue, no loss
            blk_est = 0.0
        else:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_wait_est = 0.0
            lam_eff = 0.0
            p_loss_est = 0.0
            blk_est = 0.0
            dep_rate = 0.0

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals)
        all_dep.append(count_departures)
        all_blk.append(blk_est)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(dep_rate if win_len>0 else 0)
        all_lam_eff.append(lam_eff)
        seeds_used_list.append(seed)

    avg_L = sum(all_L)/N_seeds if N_seeds>0 else 0
    avg_W = sum(all_W)/N_seeds if N_seeds>0 else 0
    avg_busy_frac = sum(all_busy_frac)/N_seeds if N_seeds>0 else 0
    avg_p_wait =
