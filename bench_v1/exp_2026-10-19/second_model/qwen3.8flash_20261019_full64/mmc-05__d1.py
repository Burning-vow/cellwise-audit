import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    # Parameters in hours
    lam_base = 10.0
    mu_base = 60.0 / 6.0  # 10 per hour
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    
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
    all_busy_occupied = []
    
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # Simulation state
        t = 0.0
        horizon_end = H
        
        # Events: (time, type, data)
        # type: 'arrival', 'departure'
        events = []
        
        # Initial arrival
        next_arrival_time = rng.expovariate(lam)
        if next_arrival_time < horizon_end:
            events.append((next_arrival_time, 'arrival', None))
            
        queue = [] # List of customers waiting (each is a dict with service_time)
        servers = [None] * c # Each server holds the departure time or None if idle
        num_in_system = 0
        
        # Statistics accumulators (for area integration and counts)
        # We need to track integral of L over time, total wait+service time, etc.
        # But we only accumulate after warmup.
        
        warmup_end = 0.25 * horizon_end
        
        # State variables for current interval
        last_event_time = 0.0
        current_num_in_system = 0
        
        # Accumulators for the whole run (we will filter by window later? 
        # No, standard DES usually resets stats at start of measurement window.
        # Let's simulate from 0 to H, but only collect stats from warmup_end to H.
        
        # To do this properly in discrete event simulation:
        # We process events. When an event occurs at time T, we update integrals based on previous state.
        # If the previous state was during measurement window, we add to accumulators.
        
        # Variables to hold accumulated stats for this seed
        int_L = 0.0 # Integral of number in system over measurement window
        int_W_sum = 0.0 # Sum of (wait+service) times for customers who completed within measurement window?
        # Actually, W is average time in system. Usually defined as Little's Law L = lambda * W.
        # Or simply average of individual sojourn times.
        # The prompt asks for "average wait+service time W". This implies sample mean of sojourn times.
        # However, L is time-average number in system.
        # Let's stick to:
        # L = (Integral of N(t) dt) / Window_Length
        # W = (Sum of sojourn times of customers who departed in window) / Count_departed_in_window
        # p_wait = (Count arrivals that found all servers busy) / Total Arrivals in window
        
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0 # In M/M/c/K, blocked means lost. Here K=infinity? "bank branch" usually infinite queue.
        # Prompt mentions blk and p_loss. If queue is infinite, blk=0, p_loss=0.
        # But let's assume infinite capacity unless specified otherwise. Standard bank model has infinite queue.
        # So blk should be 0.
        
        sum_sojourn_times_window = 0.0
        
        # Helper to check if a time point is in measurement window
        def in_window(t_val):
            return t_val >= warmup_end
            
        # Process events
        while events:
            # Find next event
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, ev_data = events.pop(0)
            
            if curr_t > horizon_end:
                break
                
            # Update integrals from last_event_time to curr_t
            dt = curr_t - last_event_time
            if dt > 0:
                # Check overlap with measurement window
                # Interval [last_event_time, curr_t]
                # Measurement window [warmup_end, horizon_end]
                
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(curr_t, horizon_end)
                
                if overlap_start < overlap_end:
                    overlap_dt = overlap_end - overlap_start
                    int_L += current_num_in_system * overlap_dt
                    
            last_event_time = curr_t
            
            if ev_type == 'arrival':
                # Schedule next arrival
                inter_arrival = rng.expovariate(lam)
                next_t = curr_t + inter_arrival
                if next_t <= horizon_end:
                    events.append((next_t, 'arrival', None))
                    
                # Handle arrival
                # Check if any server is free
                free_server_idx = -1
                for k in range(c):
                    if servers[k] is None:
                        free_server_idx = k
                        break
                        
                if free_server_idx != -1:
                    # Start service immediately
                    service_time = rng.expovariate(mu)
                    dep_time = curr_t + service_time
                    servers[free_server_idx] = dep_time
                    events.append((dep_time, 'departure', {'start_time': curr_t, 'end_time': dep_time}))
                    current_num_in_system += 1
                    if in_window(curr_t):
                        count_arrivals_window += 1
                        # Wait time is 0
                        # Sojourn time will be added when it departs
                else:
                    # All servers busy, join queue
                    service_time = rng.expovariate(mu)
                    queue.append({'arrival_time': curr_t, 'service_time': service_time})
                    current_num_in_system += 1
                    if in_window(curr_t):
                        count_arrivals_window += 1
                        # This customer waited. We don't know total sojourn yet.
                        
            elif ev_type == 'departure':
                # Customer leaves
                cust_info = ev_data
                start_serv_time = cust_info['start_time']
                end_serv_time = cust_info['end_time']
                
                # Determine which server freed up
                # We stored dep_time in servers array. Need to find index.
                # Since multiple servers could have same dep time theoretically (prob 0), just scan.
                freed_idx = -1
                for k in range(c):
                    if servers[k] == end_serv_time:
                        freed_idx = k
                        break
                if freed_idx == -1:
                    # Fallback if floating point issues, though unlikely with expovariate
                    # Just pick first non-None that matches approximately? 
                    # Better: store server index in event data.
                    pass
                
                # Actually, let's refine event structure to include server index.
                # Re-running logic mentally: I didn't store server index in departure event.
                # Let's fix the code generation below.
                
                # For now, assume we can identify it.
                servers[freed_idx] = None
                current_num_in_system -= 1
                
                # Calculate sojourn time
                # Arrival time was not stored in departure event directly in my sketch above.
                # I need to pass arrival time through.
                
                # Let's rewrite the event handling more carefully in the final code block.
                pass

    # Due to complexity of tracking exact indices and ensuring correctness in one shot without classes,
    # I will implement a robust version using tuples for events containing necessary info.
    
    # Resetting implementation plan for clean code:
    # Event tuple: (time, type, payload)
    # Payload for arrival: None
    # Payload for departure: (server_index, arrival_time, service_duration)
    
    results_per_seed = {
        'L': [], 'W': [], 'busy_frac': [], 'p_wait': [], 'arr': [], 'dep': [], 'blk': [], 
        'busy_util': [], 'dep_rate': [], 'lam_eff': [], 'p_loss': [], 'busy_occupied': []
    }
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        horizon_end = H
        warmup_end = 0.25 * horizon_end
        
        # Priority queue via list sort (small scale simulation)
        events = []
        
        # Generate first arrival
        next_arr = rng.expovariate(lam)
        if next_arr < horizon_end:
            events.append((next_arr, 'A', None))
            
        servers = [None] * c # Stores departure time
        queue = [] # List of dicts: {'arr_t': ..., 'serv_dur': ...}
        n_sys = 0
        
        # Stats
        int_L = 0.0
        cnt_A_win = 0
        cnt_D_win = 0
        sum_Sojourn_win = 0.0
        cnt_Waiting_Arrivals_win = 0 # Arrivals that had to wait (all servers busy)
        cnt_Blocked_win = 0 # Always 0 for infinite queue
        
        last_t = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, typ, payload = events.pop(0)
            
            if curr_t > horizon_end:
                break
                
            # Integrate L
            dt = curr_t - last_t
            if dt > 0:
                os = max(last_t, warmup_end)
                oe = min(curr_t, horizon_end)
                if os < oe:
                    int_L += n_sys * (oe - os)
            last_t = curr_t
            
            if typ == 'A':
                # Schedule next arrival
                ia = rng.expovariate(lam)
                nt = curr_t + ia
                if nt <= horizon_end:
                    events.append((nt, 'A', None))
                
                # Find free server
                free_idx = -1
                for k in range(c):
                    if servers[k] is None:
                        free_idx = k
                        break
                
                serv_dur = rng.expovariate(mu)
                
                if free_idx != -1:
                    dep_t = curr_t + serv_dur
                    servers[free_idx] = dep_t
                    events.append((dep_t, 'D', (free_idx, curr_t, serv_dur)))
                    n_sys += 1
                    if curr_t >= warmup_end:
                        cnt_A_win += 1
                        # Wait time 0, sojourn = serv_dur. Added at departure.
                else:
                    queue.append({'arr_t': curr_t, 'serv_dur': serv_dur})
                    n_sys += 1
                    if curr_t >= warmup_end:
                        cnt_A_win += 1
                        cnt_Waiting_Arrivals_win += 1
                        
            elif typ == 'D':
                srv_idx, arr_t, serv_dur = payload
                servers[srv_idx] = None
                n_sys -= 1
                
                # Check if someone in queue starts service
                if queue:
                    next_cust = queue.pop(0)
                    # Service starts now (curr_t)
                    new_arr_t = next_cust['arr_t']
                    new_serv_dur = next_cust['serv_dur']
                    dep_t_new = curr_t + new_serv_dur
                    servers[srv_idx] = dep_t_new
                    events.append((dep_t_new, 'D', (srv_idx, new_arr_t, new_serv_dur)))
                    # Note: The departing customer's sojourn time needs to be recorded if they departed in window.
                    # The new customer's sojourn time will be recorded when THEY depart.
                
                # Record sojourn time for the departing customer
                # Sojourn = Departure Time - Arrival Time
                sojourn = curr_t - arr_t
                
                if curr_t >= warmup_end:
                    cnt_D_win += 1
                    sum_Sojourn_win += sojourn
                    
        # End of simulation for seed i
        
        win_len = horizon_end - warmup_end
        if win_len <= 0:
            continue
            
        L_est = int_L / win_len
        W_est = sum_Sojourn_win / cnt_D_win if cnt_D_win > 0 else 0.0
        p_wait_est = cnt_Waiting_Arrivals_win / cnt_A_win if cnt_A_win > 0 else 0.0
        busy_frac_est = L_est / c # E[N]/c ? No. Busy fraction definition in prompt: E[min(N,c)]/c.
        # Wait, prompt says: busy_frac definition = E[min(N,c)]/c.
        # My int_L is integral of N(t). I need integral of min(N(t), c).
        # I did NOT integrate min(N,c). I integrated N.
        # Correction needed: I must track integral of min(n_sys, c).
        
        # Re-simulating with correct integrator for busy_frac/busy_util
        # Since I already ran the loop, I'll restart the inner loop logic for accuracy or adjust.
        # Given constraints, I'll rewrite the core loop to capture both integrals.
        
        # Let's redo the seed calculation properly.
        pass

    # Final Code Structure Generation
    import random, json, argparse

    def run_sim(seed, H, lam, mu, c):
        rng = random.Random(seed)
        warmup = 0.25 * H
        events = []
        next_arr = rng.expovariate(lam)
        if next_arr < H:
            events.append((next_arr, 'A', None))
        
        servers = [None] * c
        queue = []
        n_sys = 0
        
        int_N = 0.0
        int_MinNC = 0.0
        cnt_A = 0
        cnt_D = 0
        sum_Soj = 0.0
        cnt_Wait = 0
        
        last_t = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, pay = events.pop(0)
            if t > H: break
            
            dt = t - last_t
            if dt > 0:
                os = max(last_t, warmup)
                oe = min(t, H)
                if os < oe:
                    dur = oe - os
                    int_N += n_sys * dur
                    int_MinNC += min(n_sys, c) * dur
            last_t = t
            
            if typ == 'A':
                ia = rng.expovariate(lam)
                nt = t + ia
                if nt <= H:
                    events.append((nt, 'A', None))
                
                sd = rng.expovariate(mu)
                free = -1
                for k in range(c):
                    if servers[k] is None:
                        free = k; break
                
                if free != -1:
                    dep = t + sd
                    servers[free] = dep
                    events.append((dep, 'D', (free, t, sd)))
                    n_sys += 1
                    if t >= warmup:
                        cnt_A += 1
                else:
                    queue.append({'at': t, 'sd': sd})
                    n_sys += 1
                    if t >= warmup:
                        cnt_A += 1
                        cnt_Wait += 1
                        
            elif typ == 'D':
                si, at, sd = pay
                servers[si] = None
                n_sys -= 1
                
                if queue:
                    nc = queue.pop(0)
                    nd = t + nc['sd']
                    servers[si] = nd
                    events.append((nd, 'D', (si, nc['at'], nc['sd'])))
                
                if t >= warmup:
                    cnt_D += 1
                    sum_Soj += (t - at)
                    
        win = H - warmup
        if win <= 0: return None
        
        L = int_N / win
        busy_frac = int_MinNC / win / c
        W = sum_Soj / cnt_D if cnt_D > 0 else 0
        p_wait = cnt_Wait / cnt_A if cnt_A > 0 else 0
        p_loss = 0.0 # Infinite queue
        blk = 0.0
        
        # busy_util is same as busy_frac per prompt definition E[min(N,c)]/c
        busy_util = busy_frac
        # busy_occupied = 1 - pi_0. Approximate as fraction of time at least one server busy?
        # Or simply utilization? Prompt distinguishes them.
        # pi_0 is prob system empty. 
        # We didn't track time where n_sys==0 specifically vs others.
        # Let's
