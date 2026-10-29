import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr? No, 6 min = 0.1 hr. Mean service time = 0.1 hr. Rate mu = 1/0.1 = 10 per hour.
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
        
    # Warmup fraction
    warmup_frac = 0.25
    t_warmup = H * warmup_frac
    
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
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn at arrival and attached to customer
        # We need a queue of (arrival_time, service_duration)
        queue = [] 
        servers_free_at = [0.0] * c
        
        # Statistics accumulators (for the window after warmup)
        # Area under curve for L (number in system)
        area_L = 0.0
        last_t = 0.0
        last_N = 0
        
        # Counts for window
        count_arr_window = 0
        count_dep_window = 0
        count_blk_window = 0
        count_wait_window = 0 # Arrivals that had to wait (queue length > 0 or server busy?) 
                              # "Arrival needs to queue" usually means they don't start service immediately.
                              # In FCFS with c servers, if all servers busy, they wait.
                              # If a server is free, they start immediately.
                              # So p_wait is prob(arrival finds all servers busy).
        
        # For W calculation: sum of (departure - arrival) for customers served in window?
        # Or average over all customers who arrived in window?
        # Standard definition: Average time spent in system by customers arriving in the window.
        # But we must be careful with truncation. Usually, we track completion times.
        # Let's accumulate total time in system for customers who DEPARTED in the window?
        # Or customers who ARRIVED in the window?
        # The prompt says "statistics only accumulated in window after removing first 25% warmup".
        # Area-based quantities (L) integrate state over time.
        # Count-based quantities (arr, dep) count events in time interval.
        # W is an average. It should be Total Time in System / Number of Customers.
        # Which customers? Those whose entire stay is within the window? Or those who arrive in the window?
        # Common practice: Little's Law consistency suggests using arrivals in window.
        # However, if a customer arrives near end of window, their departure might be outside.
        # To avoid bias, often we use departures in window for W estimation if we want steady-state throughput match.
        # But let's look at "area-type quantities must be integrated before changing state".
        # Let's assume W is calculated as: Sum(departure_time - arrival_time) for all customers who DEPARTED during the measurement window, divided by number of such departures.
        # This ensures we have complete sojourn times.
        
        total_sojourn_time_window = 0.0
        
        # Event loop
        while t < H:
            # Determine next event time
            arr_time = next_arrival
            # Next server completion
            # Find min of servers_free_at that is <= H? 
            # Actually, we process events chronologically.
            
            # Candidates: Arrival, Departure from any server
            # We need to know which server finishes next.
            # Since we attach service duration at arrival, we can push departure events into a heap or just scan.
            # Scanning c=2 or 3 is cheap.
            
            dep_times = [s for s in servers_free_at if s > t]
            if not dep_times:
                next_dep = float('inf')
            else:
                next_dep = min(dep_times)
                
            next_event = min(arr_time, next_dep)
            
            if next_event >= H:
                break
                
            # Integrate area for L up to next_event
            dt = next_event - last_t
            if last_t >= t_warmup:
                area_L += last_N * dt
            
            t = next_event
            
            if abs(t - arr_time) < 1e-9:
                # Arrival
                # Check if any server is free
                free_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_idx = k
                        break
                
                # Draw service time now
                svc_dur = rng.expovariate(mu)
                
                if free_idx != -1:
                    # Start service immediately
                    servers_free_at[free_idx] = t + svc_dur
                    # Customer does not wait
                    # Add to queue? No, directly to server.
                    # But we need to track them for departure stats.
                    # We can store (arrival_time, departure_time) in a list of active customers?
                    # Or just update stats when departure happens.
                    # Let's maintain a list of "in-system" customers with their arrival times.
                    # When a departure occurs, we pop one.
                    # But FCFS order matters for who leaves? 
                    # With exponential service, memoryless property makes order irrelevant for distribution, 
                    # but for exact simulation, we need to know which specific customer left.
                    # Actually, since we assign service time at arrival, we know exactly when each customer will leave IF they start service.
                    # If they wait, their start time depends on server availability.
                    
                    # Better approach: Maintain a queue of waiting customers (arrival_time, service_duration).
                    # And a set/list of servers with (customer_arrival_time, scheduled_departure_time).
                    
                    # Let's refactor state:
                    # queue: list of (arrival_time, service_duration) for waiting customers.
                    # servers: list of (arrival_time, departure_time) for currently served customers.
                    
                    # On arrival:
                    # If len(servers) < c:
                    #   dep_t = t + svc_dur
                    #   servers.append((t, dep_t))
                    #   N increases by 1.
                    # Else:
                    #   queue.append((t, svc_dur))
                    #   N increases by 1.
                    #   p_wait indicator: 1
                    
                    # On departure:
                    #   Remove from servers.
                    #   If queue not empty:
                    #     Pop front (arrival_time, svc_dur)
                    #     new_dep_t = t + svc_dur
                    #     servers.append((arrival_time, new_dep_t))
                    #   N decreases by 1.
                    
                    # This requires tracking N correctly.
                    
                    # Let's restart the logic structure inside the loop with this clearer state model.
                    pass 
                
                # Re-implementing the core loop logic below with clear state handling.
                # I will rewrite the inner part of the seed loop.
                
                # Resetting variables for clarity in code generation
                # ...
                
                # Actually, let's just write the clean version directly.
                pass

# Let's write the clean version directly.

import argparse, json, random, heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 10.0 
    c_base = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
        mu = mu_base
        c = c_base
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
        c = c_base
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        c = c_base
        
    warmup_frac = 0.25
    t_warmup = H * warmup_frac
    
    results = {
        'L': [], 'W': [], 'busy_frac': [], 'p_wait': [],
        'arr': [], 'dep': [], 'blk': [], 'busy_util': [],
        'dep_rate': [], 'lam_eff': [], 'p_loss': []
    }
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # State
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queue of waiting customers: (arrival_time, service_duration)
        waiting_queue = []
        # Servers: list of departure_times. We also need to map back to arrival_time for W calc.
        # Let's keep servers as list of tuples: (arrival_time, departure_time)
        servers = [] 
        
        # Stats accumulators for the window [t_warmup, H]
        area_L = 0.0
        last_t = 0.0
        last_N = 0
        
        count_arr = 0
        count_dep = 0
        count_blk = 0 # Assuming no blocking/loss in standard M/M/c unless specified. Problem doesn't mention capacity limit. So blk=0.
        count_wait = 0 # Arrivals that joined queue (had to wait)
        
        total_sojourn = 0.0 # Sum of (dep - arr) for customers departing in window
        
        # Helper to get current N
        def get_N():
            return len(waiting_queue) + len(servers)
            
        last_N = get_N()
        
        while t < H:
            # Determine next event
            arr_time = next_arrival
            dep_time = min([s[1] for s in servers]) if servers else float('inf')
            
            next_event = min(arr_time, dep_time)
            
            if next_event >= H:
                # Integrate until H
                dt = H - last_t
                if last_t >= t_warmup:
                    area_L += last_N * dt
                t = H
                break
            
            # Integrate area up to next_event
            dt = next_event - last_t
            if last_t >= t_warmup:
                area_L += last_N * dt
            
            t = next_event
            
            if abs(t - arr_time) < 1e-9:
                # Arrival
                # Draw service time
                svc_dur = rng.expovariate(mu)
                
                # Check if server available
                # A server is available if its departure time <= t
                # But we removed departed servers already? 
                # No, we process events sequentially. At time t, if dep_time == t, it was processed?
                # If arr_time == dep_time, tie-breaking. Usually arrival then departure or vice versa?
                # In continuous time, probability of exact tie is 0.
                # But due to floating point, we check.
                
                # Update servers: remove those finished at or before t?
                # Actually, the event loop handles one event at a time.
                # If next_event is arrival, it means no departure happened strictly before this arrival.
                # So all servers in `servers` list have dep_time > t.
                # Thus, no server is free.
                
                # Wait, what if a server finished at exactly t?
                # If dep_time == t, it would be picked as next_event too.
                # Let's handle ties by processing departures first? Or arrivals first?
                # Standard convention: if a customer arrives exactly when another leaves, 
                # the leaving customer frees the server, so the arriving customer starts immediately.
                # So process departures first if tied.
                
                # Correction: The loop picks min. If equal, we need explicit tie-break.
                # Let's force dep_time < arr_time to be departure, else arrival.
                # If equal, treat as departure first.
                
                if abs(dep_time - t) < 1e-9 and dep_time <= arr_time:
                     # This branch shouldn't happen if we structured carefully, 
                     # but let's ensure we process departures if they are due.
                     pass 

                # Simpler: Check if any server is free NOW.
                # Since we haven't processed departures yet, `servers` contains active ones.
                # If a server's dep_time == t, it is effectively free.
                # But our event selection picked `next_event`. 
                # If `arr_time` was chosen, it implies `arr_time <= dep_time`.
                # If `arr_time < dep_time`, no server is free.
                # If `arr_time == dep_time`, a server IS free.
                
                # Let's refine event selection to prioritize departures on tie.
                # Already did: next_event = min(...). 
                # If arr_time == dep_time, both are candidates.
                # We need to know which one to execute.
                
                # Let's change strategy:
                # 1. Calculate next_arrival and next_departure.
                # 2. If next_departure <= next_arrival, process departure.
                # 3. Else process arrival.
                
                # Re-evaluating the block above:
                # We are inside `if abs(t - arr_time) < 1e-9`.
                # This means we chose Arrival.
                # Did we choose it because arr < dep? Yes.
                # So dep_time > t. So no server is free.
                
                # Therefore, customer MUST wait.
                waiting_queue.append((t, svc_dur))
                count_arr += 1 if t >= t_warmup else 0
                count_wait += 1 if t >= t_warmup else 0
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                # Find the server that departs at t
                # There might be multiple? Unlikely with continuous dist.
                # Remove one.
                idx_to_remove = -1
                for k, s in enumerate(servers):
                    if abs(s[1] - t) < 1e-9:
                        idx_to_remove = k
                        break
                
                if idx_to_remove != -1:
                    arr_t, dep_t = servers.pop(idx_to_remove)
                    
                    # Record sojourn time if departure is in window
                    if t >= t_warmup:
                        count_dep += 1
                        total_sojourn += (t - arr_t)
                        
                    # Serve next from queue if available
                    if waiting_queue:
                        next_cust_arr_t, next_svc_dur = waiting_queue.pop(0)
                        new_dep_t = t + next_svc_dur
                        servers.append((next_cust_arr_t, new_dep_t))
                
                # Note: If no server matched exactly due to float error, we might miss.
                # But we constructed servers from expovariate sums, so they should match.
                
            # Update N for next integration step
            last_t = t
            last_N = get_N()
            
        # End of simulation for this seed
        
        # Calculate metrics for this seed
        win_len = H - t_warmup
        
        # L: Average number in system
        L_val = area_L / win_len if win_len > 0 else 0
        
        # W: Average time in system
        # Using departures in window
        W_val = total_sojourn / count_dep if count_dep > 0 else 0
        
        # Busy Fraction: E[min(N,c)]/c
        # We didn't track area of min(N,c). 
        # We can approximate or re-calculate.
        # Let's add area_minNc accumulator.
        # Refactoring needed.
        
        # P_wait: Probability arrival has to wait
        # count_wait / count_arr
        p_wait_val = count_wait / count_arr if count_arr > 0 else 0
        
        # Busy Utilization: Same as busy_frac definition in prompt?
        # Prompt: busy_frac = E[min(N,c)]/c.
        # busy_util = E[min(N,c)]/c.
        # They seem identical in definition provided.
        # "busy_occupied = 1 - pi_0".
        
        # We need to compute E[min(N,c)].
        # Let's re-run the accumulation logic mentally or modify code.
        # I will modify the loop to accumulate area_minNc.
        
        # Since I cannot easily edit the generated thought process, I will write the final code with these accumulators included.
        
        # Accumulators needed:
        # area_L
        # area_minNc
        # count_arr, count_dep, count_wait
        # total_sojourn
        
        # Also need pi_0 for busy_occupied?
        # pi_0 = Prob(N=0). Can estimate via time fraction where N=0.
        # area_zero = integral of 1 if N==0 else 0.
        
        # Let's finalize the code structure.
        
        # Results storage
        res_L = L_val
        res_W = W_val
        res_p_wait = p_wait_val
        res_arr = count_arr
        res_dep = count_dep
        res_blk = 0 # No loss system
        res_p_loss = 0
        
        # Need to recalculate busy_frac etc properly in the final code.
        
        # Store per seed
        results['L'].append(res_L)
        results['W'].append(res_W)
        results['p_wait'].append(res_p_wait)
        results['arr'].append(res_arr)
        results['dep'].append(res_dep)
        results['blk'].append(res_blk)
        results['p_loss'].append(res_p_loss)
        
        # Placeholder for others, will fill in final code.
        results['busy_frac'].append(0) 
        results['busy_util'].append(0)
        results['dep_rate'].append(0)
        results['lam_eff'].append(0)

    # Aggregate
    avg_L = sum(results['L']) / N_seeds
    avg_W = sum(results['W']) / N_seeds
    avg_p_wait = sum(results['p_wait']) / N_seeds
    avg_arr = sum(results['arr']) / N_seeds
    avg_dep = sum(results['dep']) / N_seeds
    avg_blk = sum(results['blk']) / N_seeds
    
    # Output JSON
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": 0.0, # Will calculate in final code
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hour",
        "seed_list": [seed_start + i for i in range(N_seeds)],
        "seeds_used": N_seeds,
        "time_unit": "hour",
        "win": round(H - t_warmup, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": 0.0,
        "dep": round(avg_dep, 4),
        "dep_rate": 0.0,
        "lam_eff": 0.0,
        "p_loss": 0.0,
        "per_seed_L": [round(x, 4) for x in results['L']],
        "per_seed_W": [round(x, 4) for x in results['W']],
        "per_seed_busy_frac": [0.0]*N_seeds,
        "per_seed_p_loss": [0.0]*N_seeds,
        "per_seed_p_wait": [round(x, 4) for x in results['p_wait']]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
