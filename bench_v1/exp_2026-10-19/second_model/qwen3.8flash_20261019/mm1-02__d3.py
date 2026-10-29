import argparse, json, random, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 4.0 # per hour
    mu_base = 60.0 / 5.0 # per hour (12 per hour)
    c = 1
    
    if args.pert == 'lam_up': lam = lam_base * 1.1
    elif args.pert == 'mu_up': mu = mu_base * 1.1; lam = lam_base
    elif args.pert == 'c_up': lam = lam_base; mu = mu_base; c = 2
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * warmup_frac
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_busy_occupied = []
    
    seed_list = list(range(args.seed_start, args.seed_start + args.seeds))
    
    for s in seed_list:
        rng = random.Random(s)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} # customer_id -> duration
        queue = [] # list of customer_ids waiting
        server_free_time = 0.0
        current_customer = None
        
        # Statistics accumulators for the window [warmup_end, horizon]
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_waited = 0 # customers who waited > 0 upon arrival? Or just p_wait definition? 
                         # Usually p_wait is prob an arriving customer waits.
                         # In M/M/1, P(wait) = rho. Let's track arrivals that join queue or start service later than arrival.
        
        # We need to simulate events.
        # Events: Arrival, Departure
        
        # Initial state
        last_event_time = 0.0
        n_in_system = 0
        
        while True:
            # Determine next event time
            arr_t = next_arrival
            dep_t = float('inf')
            if current_customer is not None:
                dep_t = server_free_time
            
            if arr_t >= horizon and dep_t >= horizon:
                break
                
            if arr_t < dep_t:
                # Process Arrival
                dt = arr_t - last_event_time
                if last_event_time < warmup_end:
                    pass # ignore pre-warmup accumulation logic if we only integrate after warmup?
                    # Actually, we should integrate from max(last_event_time, warmup_end) to min(arr_t, horizon)
                
                # Integrate areas up to this event time
                int_start = max(last_event_time, warmup_end)
                int_end = min(arr_t, horizon)
                if int_end > int_start:
                    dur = int_end - int_start
                    area_L += n_in_system * dur
                    if n_in_system > 0:
                        area_busy += dur
                
                t = arr_t
                last_event_time = t
                
                if t >= warmup_end and t <= horizon:
                    count_arr += 1
                    
                # Generate service time now
                svc_dur = rng.expovariate(mu)
                cust_id = count_arr # simple ID for tracking within this seed run stats? No, use global counter or local.
                # Let's use a local counter for IDs to map service times if needed, but here we just attach it.
                # For W calculation, we need arrival time.
                
                # Check if system can accept
                # Infinite buffer assumed unless specified otherwise? "打印店" usually implies queue.
                # But perturbation 'c_up' changes servers.
                # If c servers, check if any free.
                
                # Simplified for single server first, then generalize logic slightly for c>1 if needed by structure?
                # The prompt says "don't define classes", "one main".
                # Let's stick to general multi-server logic to be safe with c_up.
                
                # Find a free server
                # We need to track server states.
                # Since c is small, we can manage lists.
                
                # Re-evaluating structure for c servers:
                # servers: list of release times.
                # queue: list of (arrival_time, service_duration)
                
                # Let's restart the simulation loop structure to support c properly.
                pass 

        # Resetting approach for clean code within constraints:
        # Use a priority queue or simple event list since c is small.
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Servers: list of available times (initially 0)
        servers = [0.0] * c
        # Queue: list of tuples (arrival_time, service_duration)
        queue = []
        
        # Stats
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_customers_in_window = 0 # For average W denominator? Or total departures?
        # W is avg time in system. Sum of (dep_time - arr_time) for all customers who departed in window?
        # Standard practice: accumulate W for customers who complete service in the window.
        
        last_event_time = 0.0
        
        # Helper to get current number in system
        def get_n():
            return len(queue) + sum(1 for st in servers if st > t)
            
        # Main Loop
        while True:
            # Next arrival time
            arr_t = next_arrival
            
            # Next departure time: min of server release times that are > t
            # Also consider if queue is empty, no departure until new arrival starts service?
            # No, if server busy, it has a release time.
            dep_t = float('inf')
            for i in range(c):
                if servers[i] > t:
                    if servers[i] < dep_t:
                        dep_t = servers[i]
                        
            # If queue is not empty, does a departure trigger immediate start?
            # Yes, handled in departure processing.
            
            if arr_t >= horizon and dep_t >= horizon:
                break
                
            # Choose next event
            if arr_t <= dep_t:
                evt_t = arr_t
                evt_type = 'arr'
            else:
                evt_t = dep_t
                evt_type = 'dep'
                
            # Integrate areas from last_event_time to evt_t
            int_start = max(last_event_time, warmup_end)
            int_end = min(evt_t, horizon)
            if int_end > int_start:
                dur = int_end - int_start
                n_curr = len(queue) + sum(1 for st in servers if st > last_event_time) # Approximate N during interval?
                # N is constant between events.
                # Calculate N at last_event_time (after previous event processed)
                # We need to maintain N explicitly or calculate it.
                # Let's maintain N variable.
                pass
            
            # Refactor: Maintain N explicitly.
            # This requires careful updating.
            
            # Let's rewrite the loop body cleanly.
            
            # Update time
            dt = evt_t - last_event_time
            if last_event_time < warmup_end:
                # Only integrate part after warmup
                if evt_t > warmup_end:
                    dur = evt_t - warmup_end
                    area_L += N * dur
                    if N > 0:
                        area_busy += dur
            else:
                dur = evt_t - last_event_time
                area_L += N * dur
                if N > 0:
                    area_busy += dur
            
            t = evt_t
            last_event_time = t
            
            if evt_type == 'arr':
                # Generate service time
                svc = rng.expovariate(mu)
                
                # Check capacity/blocking?
                # Problem doesn't specify blocking probability mechanism other than 'blk'.
                # Usually infinite queue. If finite, blk occurs.
                # Assuming infinite queue as standard M/M/1/c/K?
                # Prompt mentions 'blk' and 'p_loss'.
                # If queue length limit exists? Not specified.
                # Default assumption: Infinite queue => blk=0, p_loss=0.
                # However, 'c_up' perturbation might imply finite capacity?
                # Without explicit K, assume K=infinity.
                
                # Add to queue
                queue.append((t, svc))
                N += 1
                
                if t >= warmup_end and t <= horizon:
                    count_arr += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Try to assign to server
                assigned = False
                for i in range(c):
                    if servers[i] <= t:
                        servers[i] = t + svc
                        queue.pop(0) # Remove from queue
                        N -= 1 # It was counted in N, now moving to service? 
                               # Wait, N includes queue + service.
                               # If I added to queue, N increased.
                               # If I move to service, N stays same?
                               # My N definition: len(queue) + active_servers.
                               # When adding to queue: len(queue) increases.
                               # When assigning: len(queue) decreases, active_servers increases.
                               # Net change in N is 0.
                               # So I shouldn't decrement N here if I incremented it on arrival.
                               # Correction: On arrival, N increases by 1.
                               # If assigned immediately, it moves from queue to server. N remains same.
                               # If not assigned, it stays in queue. N remains same.
                               # So N increment happens once on arrival.
                               # Assignment logic:
                               # Pop from queue. Set server time.
                               # N does NOT change because it was already counted.
                        assigned = True
                        break
                
            elif evt_type == 'dep':
                # Find which server finished
                # There might be multiple? Unlikely with continuous time, but handle one.
                # Find index with min servers[i] == t
                idx = -1
                for i in range(c):
                    if abs(servers[i] - t) < 1e-9:
                        idx = i
                        break
                
                if idx != -1:
                    # Customer leaves
                    # Need to know their arrival time to calculate W
                    # We lost the arrival time when we assigned them to server!
                    # Fix: Store (arrival_time, service_duration) in server slot too?
                    # Or store in a separate dict/list.
                    
                    # Let's change data structures:
                    # servers: list of dicts {'release_time': ..., 'arrival_time': ...}
                    # queue: list of dicts {'arrival_time': ..., 'service_duration': ...}
                    
                    # Restarting data structure design...
                    pass

        # Due to complexity of rewriting mid-thought, I will write the final code directly using robust structures.
        # Structures:
        # queue: list of (arrival_time, service_duration)
        # servers: list of (release_time, arrival_time_of_current_cust)
        # N = len(queue) + count(active servers)
        
        # Re-initializing for actual code generation below.
        pass

# Final Code Generation follows
