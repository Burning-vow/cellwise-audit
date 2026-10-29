import sys, json, random, argparse

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
    
    lam = 4.0 # per hour
    mu_service_time_min = 5.0
    service_time_hr = mu_service_time_min / 60.0
    
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        service_time_hr /= 1.1
    elif args.pert == 'c_up':
        pass # c is fixed at 1 for this problem
        
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_frac_sum = 0.0
    total_arr_sum = 0
    total_dep_sum = 0
    total_blk_sum = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        
        queue = [] # list of arrival times
        server_free_t = 0.0
        is_server_busy = False
        
        # For integration of L and busy time
        last_event_t = 0.0
        area_L = 0.0
        area_busy = 0.0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0
        
        # We need to track events within the window [H*warmup, H]
        # But simulation runs from 0 to H.
        # To handle "area" correctly with discrete events, we integrate between events.
        
        while t < H:
            # Determine next event time
            if not queue and not is_server_busy:
                # Idle system, jump to next arrival
                if next_arr_t > H:
                    break
                t = next_arr_t
                # Process arrival
                if t >= H * warmup_ratio:
                    arr_count_win += 1
                
                # Check if server is free (it should be)
                if t >= server_free_t:
                    # Start service immediately
                    dur = service_time_hr
                    server_free_t = t + dur
                    is_server_busy = True
                    # No waiting
                else:
                    # Should not happen if idle logic is correct, but safe guard
                    queue.append(t)
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                continue
            
            # Events: Arrival or Departure
            next_dep_t = float('inf')
            if is_server_busy:
                next_dep_t = server_free_t
            
            next_ev_t = min(next_arr_t, next_dep_t)
            
            if next_ev_t > H:
                # Integrate up to H
                dt = H - last_event_t
                n_curr = len(queue) + (1 if is_server_busy else 0)
                area_L += n_curr * dt
                if is_server_busy:
                    area_busy += dt
                t = H
                break
            
            # Integrate from last_event_t to next_ev_t
            dt = next_ev_t - last_event_t
            n_curr = len(queue) + (1 if is_server_busy else 0)
            area_L += n_curr * dt
            if is_server_busy:
                area_busy += dt
            
            t = next_ev_t
            last_event_t = t
            
            if t == next_arr_t:
                # Arrival
                if t >= H * warmup_ratio:
                    arr_count_win += 1
                
                # Check capacity? Problem says "auto car wash", usually infinite queue unless specified.
                # "blk" implies blocking/loss. Standard M/M/1 has no loss. 
                # However, prompt asks for blk, p_loss. If it's M/M/1, these are 0.
                # Let's assume infinite buffer as standard for "car wash" unless "capacity K" given.
                # If capacity is infinite, blk=0.
                
                if is_server_busy:
                    queue.append(t)
                else:
                    # Start service
                    dur = service_time_hr
                    server_free_t = t + dur
                    is_server_busy = True
                
                next_arr_t = t + rng.expovariate(lam)
                
            elif t == next_dep_t:
                # Departure
                if t >= H * warmup_ratio:
                    dep_count_win += 1
                    
                # Who departed? The one being served.
                # We don't store start time explicitly in a variable other than server_free_t - dur.
                # But we need W. W = T_sys.
                # We need to know when the current customer arrived.
                # In FCFS, the one being served is the head of the queue if queue was non-empty before,
                # OR the one who just started if queue was empty.
                # Actually, simpler: When service starts, we can record arrival time.
                # Let's modify state: store (arrival_time) for the person in service.
                
                # Correction: I didn't store arrival time of person in service.
                # Let's refactor slightly inside loop or use a variable.
                # Since I can't easily refactor mid-loop without breaking flow, let's look at how I handled it.
                # I appended to queue. When starting service, I set is_server_busy=True.
                # I need to know the arrival time of the person currently in service.
                
                # Let's introduce a variable `current_cust_arr_t`
                pass 

        # Re-running logic mentally to fix missing var...
        # I will rewrite the inner loop carefully in the final code block.
        
        # Resetting for actual code generation below...
