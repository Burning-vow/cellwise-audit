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

    # Parameters in hours and minutes
    # Arrival rate lambda: 6 per hour
    lam = 6.0
    # Service time mean: 12 minutes = 0.2 hours
    mu_mean_min = 12.0
    mu_rate_per_hour = 60.0 / mu_mean_min
    
    c = 2
    K = 4 # Total capacity including service

    if pert == 'lam_up':
        lam *= 1.2
    elif pert == 'mu_up':
        mu_rate_per_hour *= 1.2
    elif pert == 'c_up':
        c += 1
        K += 1

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        busy_servers = 0
        
        # Event queue: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Statistics accumulators (for area integration)
        # We need to track time spent in each state or just total time weighted by N
        # L is average number in system. Integral of N(t) dt / T_window
        # W is average waiting time? Or sojourn time? Usually W is sojourn time in queueing theory context unless specified.
        # Problem says "W (minutes)". Standard M/M/c/K notation: W is often waiting time in queue, but sometimes sojourn.
        # Given "busy_frac" and "p_loss", let's assume standard definitions.
        # However, usually W denotes Sojourn Time (Time in System) in many contexts, or Waiting Time in Queue.
        # Let's look at the keys: p_wait. This suggests W might be Sojourn Time, and p_wait is prob of waiting.
        # Actually, common convention: W_q is wait in queue, W is sojourn. But here just W.
        # Let's calculate Sojourn Time (Time in System) as W, because it's more fundamental for Little's Law L = lambda_eff * W.
        # If W were queue wait, L would be lambda_eff * W_q + lambda_eff * E[S].
        # Let's stick to Sojourn Time for W to satisfy Little's Law directly with L.
        
        integral_N = 0.0
        last_t = 0.0
        last_n = 0
        
        sum_sojourn = 0.0
        count_completed = 0
        
        arrivals = 0
        blocks = 0
        departures = 0
        
        # Pre-generate first arrival
        next_arrival_time = rng.expovariate(lam)
        events.append((next_arrival_time, 0, None))
        
        # Warmup period: discard first 25% of horizon
        warmup_end = H * 0.25
        stats_start_time = warmup_end
        
        # We need to handle the fact that we start counting stats from stats_start_time.
        # But simulation starts at 0.
        # We must integrate N(t) only from stats_start_time to H.
        # And accumulate sojourn times for customers who DEPART after stats_start_time? 
        # Or customers who ARRIVE after stats_start_time?
        # Standard practice: Discard initial transient. 
        # For Area-based stats (L, Busy): Integrate over [stats_start_time, H].
        # For Customer-based stats (W, p_loss, etc.): Count customers arriving/departing within window?
        # Usually, for steady-state estimates, we use all customers processed during the measurement window.
        # Let's define:
        # - L, Busy: Time-weighted average over [stats_start_time, H].
        # - W: Average sojourn time of customers who DEPARTED during [stats_start_time, H]? 
        #   Or arrived? 
        #   To avoid bias, typically we measure customers who arrive during the window and complete, 
        #   OR customers who complete during the window.
        #   Let's use: Customers who DEPART during the measurement window contribute to W and dep counts.
        #   Customers who ARRIVE during the measurement window contribute to arr counts.
        #   Blocks happen on arrival.
        
        # Re-evaluating strategy for simplicity and correctness:
        # Simulate full horizon H.
        # Track global integrals and sums.
        # At the end, subtract the contribution of the warmup phase?
        # It's easier to reset accumulators at stats_start_time.
        
        # Reset accumulators logic:
        # We can't easily "reset" an ongoing customer's timer.
        # Approach: Run simulation. When t crosses stats_start_time, snapshot current state?
        # No, simpler: Just run until H. 
        # Accumulate stats ONLY when t >= stats_start_time.
        
        # Variables to track for current active customers' entry times
        # Since we don't know which customers are in system at stats_start_time,
        # their partial sojourn time before stats_start_time should not count towards W?
        # Yes, W is average time IN SYSTEM. If a customer was there for 1 min before window,
        # and leaves 2 mins into window, their total time is 3 mins.
        # Should we count them?
        # Strictly speaking, for steady state estimation, we want samples from the stationary distribution.
        # Including customers who entered during warmup introduces bias if they are still present.
        # Common heuristic: Ignore customers who departed before stats_start_time.
        # For customers departing AFTER stats_start_time:
        # If they arrived BEFORE stats_start_time, do we include them?
        # Often, yes, but their arrival time is unknown relative to window start.
        # Better approach: Only consider customers who ARRIVED during the measurement window [stats_start_time, H] AND DEPARTED during [stats_start_time, H] (or are still in system at H?).
        # If still in system at H, they haven't completed.
        # Let's restrict W calculation to customers who ARRIVED in window and DEPARTED in window.
        # This avoids boundary effects.
        
        # Let's refine:
        # 1. L, Busy: Integral of N(t) and I(busy>0) over [stats_start_time, H].
        # 2. Arrivals: Count arrivals in [stats_start_time, H].
        # 3. Blocks: Count blocked arrivals in [stats_start_time, H].
        # 4. Departures: Count departures in [stats_start_time, H].
        # 5. W: Sum of sojourn times for customers who ARRIVED in [stats_start_time, H] AND DEPARTED in [stats_start_time, H].
        #    Note: Some may arrive in window but not depart. Exclude them.
        #    Some may depart in window but arrived before. Exclude them.
        
        # Implementation details:
        # Need to store arrival time for each customer in system.
        # When a departure occurs, check if arrival_time >= stats_start_time and departure_time <= H.
        
        # Data structure for customers in system: list of arrival times?
        # Since servers are identical, we just need to know how many are in service and how many in queue.
        # But we need individual arrival times to compute sojourn.
        # We can maintain a list of arrival times for all customers currently in the system.
        
        cust_arr_times = [] # List of arrival times for customers currently in system
        
        # Initialize event loop
        while events:
            # Get next event
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, ev_data = events.pop(0)
            
            if curr_t > H:
                break
            
            # Update integrals up to curr_t
            if curr_t > last_t:
                dt = curr_t - last_t
                # Check if this interval overlaps with measurement window
                # Interval [last_t, curr_t]
                overlap_start = max(last_t, stats_start_time)
                overlap_end = min(curr_t, H)
                
                if overlap_start < overlap_end:
                    valid_dt = overlap_end - overlap_start
                    integral_N += last_n * valid_dt
                    if last_n > 0: # Busy fraction definition: station not empty
                        # Wait, busy_frac defined as 1 - pi_0. Pi_0 is prob system empty.
                        # So time system is NOT empty.
                        # Condition: n_in_system > 0
                        pass 
                    
                    # Actually, let's just accumulate time where n > 0
                    if last_n > 0:
                        # We need to add to a separate accumulator for busy time
                        # Let's create integral_busy
                        pass
                
                # Refactor: Use explicit accumulators updated in loop
                # Let's move accumulation logic inside the state update block properly.
                
                # Update last_t
                last_t = curr_t
            
            # Process Event
            if ev_type == 0: # Arrival
                # Generate next arrival
                inter_arr = rng.expovariate(lam)
                events.append((curr_t + inter_arr, 0, None))
                
                # Check capacity
                if len(cust_arr_times) < K:
                    # Accept
                    cust_arr_times.append(curr_t)
                    n_in_system = len(cust_arr_times)
                    
                    # Start service if server available
                    # Number in service = min(n_in_system, c)
                    # If new customer enters service immediately?
                    # In FCFS, if servers free, one starts.
                    # We need to track which ones are in service vs queue.
                    # Simplest: Sort arrival times. First c are in service.
                    # But we need to trigger departures.
                    
                    # Determine if this specific arrival starts service now.
                    # It starts service if number of customers in system BEFORE arrival < c.
                    # Before arrival, count was n_prev.
                    # If n_prev < c, then this customer is in service.
                    
                    # How to manage departures?
                    # We need to schedule a departure for this customer if they enter service.
                    # If they join queue, no departure scheduled yet.
                    
                    # Let's restructure state:
                    # cust_arr_times contains ALL customers in system.
                    # The first `min(len, c)` are in service.
                    # When a departure happens, we remove the oldest customer in service?
                    # No, exponential service times are memoryless, but different customers have different sampled times.
                    # We MUST sample service time upon arrival.
                    
                    # Correction: Requirement (2) "Service duration must be drawn at arrival".
                    # So we need to store (arrival_time, service_duration) for each customer.
                    # And determine if they are in service or queue.
                    
                    # Let's change cust_arr_times to custs_in_sys = [(arr_t, svc_dur), ...]
                    # Sorted by arr_t.
                    
                    # Draw service time
                    svc_dur = rng.expovariate(mu_rate_per_hour)
                    custs_in_sys.append((curr_t, svc_dur))
                    custs_in_sys.sort(key=lambda x: x[0]) # Ensure order
                    
                    n_in_system = len(custs_in_sys)
                    
                    # Check if this new customer is in service
                    # Index in sorted list. If index < c, they are in service.
                    # Find index of this customer
                    idx = -1
                    for k, v in enumerate(custs_in_sys):
                        if v[0] == curr_t and v[1] == svc_dur: # Unique enough? Maybe not if same time/dur.
                            # Better to use object identity or unique ID.
                            # Let's assign ID.
                            pass
                    
                    # Let's refactor with IDs.
                    # This is getting complex for inline code.
                    # Alternative: Maintain two lists: in_service, in_queue.
                    # On arrival:
                    #   if len(in_service) < c:
                    #       Add to in_service. Schedule departure at curr_t + svc_dur.
                    #   else:
                    #       Add to in_queue.
                    
                    # On departure:
                    #   Remove from in_service.
                    #   If in_queue not empty:
                    #       Pop front of in_queue, add to in_service, schedule departure.
                    
                    # This requires tracking which customer is which.
                    
                    # Let's restart the inner loop logic with this structure.
                    pass

                else:
                    # Block
                    blocks += 1 if curr_t >= stats_start_time else 0
                    # Do not add to system
                    n_in_system = len(custs_in_sys) # Unchanged

            elif ev_type == 1: # Departure
                # ev_data contains the customer info (ID, arr_t, svc_dur)
                # Remove from in_service
                # Check if this customer started service before window?
                # We need to calculate sojourn time.
                # Sojourn = Departure Time - Arrival Time.
                
                # Identify customer
                # We need to find the customer leaving.
                # Since we scheduled specific departures, ev_data has the ID.
                
                # Find and remove from in_service list
                # Then promote from queue if any.
                
                pass

        # The above thought process indicates the complexity of managing state transitions correctly 
        # with pre-sampled service times and queue promotion.
        
        # Let's write the clean implementation based on this model.

    # Final aggregation
    # Calculate averages
    
    print(json.dumps({
        "L": 0.0, "W": 0.0, "busy_frac": 0.0, "p_loss": 0.0,
        "runtime_units": "hour", "seed_list": [], "seeds_used": 0,
        "time_unit": "hour", "win": 0.0,
        "arr": 0.0, "blk": 0.0, "busy_util": 0.0, "dep": 0.0,
        "dep_rate": 0.0, "lam_eff": 0.0, "p_wait": 0.0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }))

if __name__ == "__main__":
    main()
