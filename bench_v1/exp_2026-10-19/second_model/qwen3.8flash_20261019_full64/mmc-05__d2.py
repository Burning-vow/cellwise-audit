import random, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    c = 2
    lam_base = 10.0
    mu_base = 60.0 / 6.0
    time_unit = 'minute'
    horizon_min = args.horizon * 60.0 if args.time_unit == 'hour' else args.horizon
    # Actually, the prompt says H is in same unit as time_unit. Let's assume time_unit is minute for internal consistency or hour? 
    # The problem states: "time_unit 填你程序内部时间轴的单位". Let's use minutes internally for easier service time handling (mean 6 min).
    # But arrival rate is per hour. So lambda = 10/60 per minute.
    
    pert_lam = 1.0
    pert_mu = 1.0
    if args.pert == 'lam_up':
        pert_lam = 1.1
    elif args.pert == 'mu_up':
        pert_mu = 1.1
    elif args.pert == 'c_up':
        pass # c is fixed at 2 in this model description, but perturbation might imply changing capacity? 
             # Prompt says "扰动只改参数不改结构". If c_up means increase capacity, we need to handle it. 
             # However, standard M/M/c usually keeps c fixed unless specified. Let's assume c_up increases c by 1? 
             # Or maybe it just changes a parameter related to cost? The prompt doesn't define what c_up does specifically other than name.
             # Given "bank with 2 counters", let's assume c_up makes c=3? Or maybe it's a distractor. 
             # Let's stick to modifying rates for lam/mu and ignore c_up effect on structure if not clear, or set c=3 for c_up.
             # Re-reading: "扰动只改参数不改结构". Changing c from 2 to 3 is a structural change in some views, but often considered a parameter.
             # Let's assume c_up -> c=3.
        pass 

    if args.pert == 'c_up':
        c = 3
    
    lam = lam_base * pert_lam / 60.0 # arrivals per minute
    mu = mu_base * pert_mu # services per minute (mean service time = 1/mu minutes)
    
    seeds_used = []
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
    
    total_horizon = horizon_min
    warmup = total_horizon * 0.25
    stat_window_len = total_horizon - warmup
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        servers_free = [True] * c
        next_event_time = float('inf')
        event_type = None
        
        # Pre-generate first arrival
        inter_arrival = rng.expovariate(lam)
        next_arrival_time = inter_arrival
        
        # Service completion times for each server
        service_end_times = [float('inf')] * c
        
        # Statistics accumulators (for area integration)
        area_n = 0.0
        last_stat_t = warmup
        current_n_at_last_stat = 0
        
        # Counters within statistical window
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited = 0 # Arrivals that found no free server
        
        # For W calculation: sum of sojourn times of customers who departed in window?
        # Standard definition: Average time spent in system. 
        # We need to track entry time for each customer.
        # Since we don't have classes, we can store a list of (entry_time, service_duration_assigned) for those in system.
        # When they depart, add (departure_time - entry_time) to sum_sojourn.
        
        customers_in_queue = [] # List of entry times
        customers_in_service = [] # List of dicts: {'entry_time': ..., 'end_time': ...}
        
        # Initialize simulation loop
        while t < total_horizon:
            # Determine next event
            min_next = float('inf')
            next_ev_type = None
            
            if next_arrival_time < min_next:
                min_next = next_arrival_time
                next_ev_type = 'arrival'
                
            for j in range(c):
                if service_end_times[j] < min_next:
                    min_next = service_end_times[j]
                    next_ev_type = 'departure'
                    dep_server_idx = j
                    
            if min_next == float('inf'):
                break
                
            t_new = min_next
            
            # Integrate area for N(t) up to t_new
            if t >= warmup:
                dt = t_new - t
                area_n += n_in_system * dt
            elif t_new > warmup:
                dt = t_new - warmup
                area_n += n_in_system * dt
            
            t = t_new
            
            if next_ev_type == 'arrival':
                # Check if blocked (if queue length limit? Problem doesn't specify finite queue, assumes infinite buffer FCFS)
                # "先到先服务" implies infinite queue. So blk should be 0 unless there's a capacity limit not mentioned.
                # Usually M/M/c has infinite queue. p_loss would be 0.
                # However, if "blocked" refers to finding all servers busy AND queue full? No queue limit given.
                # Let's assume infinite queue, so blk=0, p_loss=0.
                
                if t >= warmup:
                    count_arrivals += 1
                    # Did they wait? i.e., were all servers busy upon arrival?
                    if n_in_system >= c:
                        count_waited += 1
                
                # Add to system
                n_in_system += 1
                customers_in_queue.append(t)
                
                # Try to assign to server immediately if one is free
                assigned = False
                for j in range(c):
                    if service_end_times[j] == float('inf'): # Server is idle
                        # Start service
                        svc_dur = rng.expovariate(mu)
                        end_t = t + svc_dur
                        service_end_times[j] = end_t
                        # Move from queue to service
                        entry_t = customers_in_queue.pop(0)
                        customers_in_service.append({'entry': entry_t, 'end': end_t})
                        assigned = True
                        break
                
                # Generate next arrival
                next_arrival_time = t + rng.expovariate(lam)
                
            elif next_ev_type == 'departure':
                j = dep_server_idx
                # Find which customer was being served by j
                # In our simplified logic, we popped from queue when assigning. 
                # We need to know who left.
                # Actually, maintaining separate lists for queue and service is tricky with indices.
                # Better approach: Just track N(t) and use Little's Law approximations or explicit tracking.
                # Explicit tracking:
                # When departure happens at server j:
                # 1. Remove the customer associated with server j.
                # 2. Decrement N.
                # 3. If queue non-empty, start next service.
                
                # How to link server j to a specific customer record?
                # Let's maintain a list `active_services` where index corresponds to server ID?
                # Or simpler: since we only care about stats, let's reconstruct.
                
                # Correction: The previous assignment logic moved a customer from queue to service.
                # We need to identify WHICH customer left.
                # Let's keep a list of tuples (server_id, entry_time, end_time) for active services.
                # This is getting complex without classes.
                
                # Alternative simple counting method for W:
                # Sum of (Departure Time - Arrival Time) for all completed services in window.
                # We need to store arrival time when starting service.
                
                # Let's refactor state:
                # `queue`: list of arrival times waiting.
                # `servers`: list of dicts {'busy': bool, 'start_time': t, 'end_time': t, 'arrival_time': t}
                
                # Resetting logic for clarity inside loop:
                pass

        # The above loop logic is flawed due to lack of persistent state structure across iterations in this scratchpad.
        # Rewriting cleanly below.

    # Clean implementation
    results = {
        'L': 0, 'W': 0, 'busy_frac': 0, 'p_wait': 0, 'runtime_units': time_unit,
        'seed_list': [], 'seeds_used': 0, 'win': 0,
        'arr': 0, 'blk': 0, 'busy_util': 0, 'dep': 0, 'dep_rate': 0, 'lam_eff': 0, 'p_loss': 0,
        'per_seed_L': [], 'per_seed_W': [], 'per_seed_busy_frac': [], 'per_seed_p_loss': [], 'per_seed_p_wait': []
    }
    
    # Re-run clean simulation
    final_stats = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # Parameters
        local_c = c
        local_lam = lam
        local_mu = mu
        
        # Simulation State
        t = 0.0
        n_sys = 0
        # Servers: list of end_times. inf means idle.
        srv_end = [float('inf')] * local_c
        # Queue: list of arrival times
        q_arrivals = []
        # Active services info for calculating W: list of (arrival_time, departure_time)
        # We will append to this list when a service completes.
        completed_sojourns = []
        
        # Next Event Times
        next_arr = rng.expovariate(local_lam)
        
        # Stats accumulators
        area_n = 0.0
        last_t = 0.0
        
        # Window boundaries
        w_start = warmup
        w_end = total_horizon
        
        # Counters for window
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        cnt_wait = 0
        
        while t < w_end:
            # Find next event
            min_t = float('inf')
            ev_type = None
            srv_idx = -1
            
            if next_arr < min_t:
                min_t = next_arr
                ev_type = 'A'
            
            for k in range(local_c):
                if srv_end[k] < min_t:
                    min_t = srv_end[k]
                    ev_type = 'D'
                    srv_idx = k
            
            if min_t == float('inf'):
                break
            
            # Advance time and integrate area
            dt = min_t - t
            if t >= w_start:
                area_n += n_sys * dt
            elif min_t > w_start:
                area_n += n_sys * (min_t - w_start)
            
            t = min_t
            
            if ev_type == 'A':
                # Arrival
                if t >= w_start:
                    cnt_arr += 1
                    if n_sys >= local_c:
                        cnt_wait += 1
                
                # Infinite queue assumption: never blocked
                # If finite queue was intended, logic would differ. Assuming infinite.
                cnt_blk_local = 0 
                
                n_sys += 1
                q_arrivals.append(t)
                
                # Try to start service
                started = False
                for k in range(local_c):
                    if srv_end[k] == float('inf'):
                        dur = rng.expovariate(local_mu)
                        srv_end[k] = t + dur
                        arr_t = q_arrivals.pop(0)
                        # Store for W calc later? 
                        # We need to match departure to arrival.
                        # Let's store (arrival_time, server_index) in a map or list?
                        # Simpler: When D occurs, we know which server finished. 
                        # We need to know WHO was in that server.
                        # Let's maintain a parallel list `srv_arrival` indicating when the current job on server k arrived.
                        pass
                    break # Only one server can be picked? No, check all.
                
                # Refining service assignment storage
                # I'll add a helper list `srv_job_info` initialized to None
                # But I didn't declare it. Let's restart the inner loop logic carefully.
                
                # Correct Logic for Assignment:
                for k in range(local_c):
                    if srv_end[k] == float('inf'):
                        dur = rng.expovariate(local_mu)
                        srv_end[k] = t + dur
                        arr_t = q_arrivals.pop(0)
                        # Record this job's arrival time against this server slot?
                        # We need to retrieve it at departure.
                        # Let's use a dictionary or list indexed by server.
                        # Since I can't easily modify scope here, I will assume a list `job_arrivals` of size C.
                        # Wait, I am writing the code now. I can declare it.
                        break
                
                next_arr = t + rng.expovariate(local_lam)
                
            elif ev_type == 'D':
                # Departure from server srv_idx
                # Retrieve arrival time of the job that was on this server
                # This requires state I haven't fully defined in the snippet above.
                # I will rewrite the whole block properly in the final output.
                pass

        # Placeholder to satisfy syntax during thought process
        pass

    # Final Output Generation
    print(json.dumps(results))

if __name__ == "__main__":
    main()
