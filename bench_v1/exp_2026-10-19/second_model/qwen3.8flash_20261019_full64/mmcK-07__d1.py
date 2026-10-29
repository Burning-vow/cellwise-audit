import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0  # 5 per hour
    c = 3
    K = 4  # total capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75  # Remove first 25% warmup
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        # Service completion times for each server (if busy)
        # We track when servers become free. 
        # Since we have c servers, we can maintain a list of finish times or just count busy servers.
        # Better: maintain a min-heap or sorted list of departure events? 
        # Simpler discrete event simulation approach:
        # Events: Arrival, Departure.
        # We need to know which server finishes next.
        # Let's keep a list of remaining service times for active customers? 
        # Or better: keep a list of absolute departure times for the current customers in service.
        
        departures = [] # List of absolute times when current services end
        
        # Statistics accumulators (for the window [warmup_end, H])
        warmup_end = H * 0.25
        last_stat_time = warmup_end
        
        area_L = 0.0
        area_busy = 0.0 # Time where n > 0
        area_occupied_servers = 0.0 # Sum of min(n, c) over time
        
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0 # Total waiting+service time for completed customers in window
        
        # To calculate W correctly, we need arrival time of each customer.
        # When a customer departs, if their arrival was >= warmup_end, add (dep - arr) to sum_W and increment count_dep_for_W?
        # Actually, standard definition: L is average number in system. W is average time in system.
        # Little's Law: L = lambda_eff * W.
        # We should accumulate W only for customers who arrive AND depart within the observation window?
        # Usually, for steady state estimates, we integrate L over time and divide by window length.
        # For W, we sum sojourn times of customers that complete during the window, divided by number of completions?
        # Or sum sojourn times of all customers that arrived during the window?
        # Common practice: Sum sojourn times of customers departing in the window, divided by number of such departures.
        # But this might bias if arrivals/departures are not balanced.
        # Alternative: Use Little's law estimate from L and effective rate.
        # The prompt asks for W explicitly. Let's compute it as average sojourn time of customers that depart during the statistical window.
        
        # We need to store arrival time for each customer currently in system.
        # Since max capacity is small (K), we can just use a list.
        # Each element: (arrival_time, departure_time_estimate?) No, departure time depends on service start.
        # Let's manage queues.
        # Queue structure:
        # Servers: c slots. Each slot has a customer with arrival_time and service_duration.
        # Waiting line: K-c slots. Each has arrival_time.
        
        # Re-implementing with explicit queue management for clarity and correctness regarding "service duration drawn at arrival".
        
        # Reset state for new seed
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        
        # Customers in service: list of dicts {arr_t, serv_dur, start_t}
        # Actually, we just need to know when they leave.
        # Let's maintain a list of departure times for the c servers.
        # And a FIFO queue for waiting cars.
        
        # Server availability: initially 0.0
        server_free_times = [0.0] * c
        # Waiting queue: list of arrival times
        wait_queue = []
        
        # Active customers info for stats:
        # We need to link departure to arrival time.
        # When a car enters service, we record its arrival time associated with the specific server instance?
        # Easier: Just track global events.
        
        # Event-driven simulation loop
        # Next event time
        while True:
            # Determine next event
            next_depart = float('inf')
            for ft in server_free_times:
                if ft < next_depart:
                    next_depart = ft
            
            next_event = min(next_arrival, next_depart)
            
            if next_event > H:
                break
                
            dt = next_event - t
            if t >= warmup_end:
                # Accumulate areas
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                # Busy util: sum of occupied servers
                occ = min(n_in_system, c)
                area_occupied_servers += occ * dt
            
            t = next_event
            
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                count_arr += 1 if t >= warmup_end else 0
                
                if n_in_system < K:
                    # Accept
                    # Draw service time now
                    serv_time = rng.expovariate(mu)
                    
                    # Find a free server
                    found_server = -1
                    for idx in range(c):
                        if server_free_times[idx] <= t + 1e-9:
                            found_server = idx
                            break
                    
                    if found_server != -1:
                        # Start service immediately
                        server_free_times[found_server] = t + serv_time
                        # Store arrival time for this job to calculate W later?
                        # We need to associate the departure event with the arrival time.
                        # Since we don't have unique IDs, let's push (t, serv_time) to a pending list?
                        # Better: Maintain a list of jobs in system.
                        # Job: {arr_t, status: 'serv'/'wait', server_idx?}
                        # This is getting complex. Let's stick to simple counters.
                        
                        # To get W, we need sum of (dep_t - arr_t).
                        # We can store arrival times in a queue corresponding to the order of service completion?
                        # No, FCFS.
                        # Let's maintain a list `jobs` containing arrival times of all customers in system.
                        # When a customer departs, we remove the oldest one? Yes, FCFS.
                        # But we need to know WHICH one departed. In FCFS, the one that started service earliest departs first?
                        # Not necessarily if service times vary.
                        # However, usually in these sims, we assume FCFS discipline.
                        # If FCFS, the customer entering service first leaves first? No, service times are random.
                        # So we must track individual customers.
                        
                        # Let's restart the data structure design.
                        pass
                    else:
                        # Wait
                        wait_queue.append(t)
                        n_in_system += 1
                        # Need to track arrival time for W calculation upon departure
                        # Let's add to a global list of active customers: (arrival_time, is_waiting)
                        # Actually, simpler: 
                        # Keep a list `active_customers` of arrival times.
                        # When someone departs, we need to know their arrival time.
                        # In FCFS, the person who has been in the system longest is the one who entered service first?
                        # No.
                        # Standard M/M/c/K FCFS:
                        # We need to know the arrival time of the specific customer leaving.
                        # Let's assign an ID or just store arrival times in a queue for service entry.
                        # When a server becomes free, it takes the head of the waiting queue (if any) or stays idle.
                        # The customer entering service has an arrival time.
                        # We can store (arrival_time, departure_time) pairs?
                        # Let's maintain a list `in_service` of tuples (arrival_time, finish_time).
                        # And `waiting` list of arrival_times.
                        
                        # Refactored State:
                        # in_service: list of (arr_t, fin_t)
                        # waiting: list of arr_t
                        # n_in_system = len(in_service) + len(waiting)
                        
                        # Add to waiting
                        waiting.append(t)
                        n_in_system += 1
                else:
                    # Blocked
                    count_blk += 1 if t >= warmup_end else 0
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - next_depart) < 1e-9:
                # Departure
                # Find which server finished
                # It's the one with min(finish_time) == t
                # We need to identify the customer.
                # If we stored (arr_t, fin_t) in in_service, we find the one with fin_t == t.
                # Then remove it.
                # Then check if waiting queue is non-empty.
                # If yes, pop front, assign to this server, set new fin_t = t + exp(mu).
                # Update stats.
                
                # Identify departing customer
                # Assuming no ties in continuous distribution, exactly one matches.
                dep_idx = -1
                for idx, (arr_t, fin_t) in enumerate(in_service):
                    if abs(fin_t - t) < 1e-9:
                        dep_idx = idx
                        break
                
                if dep_idx != -1:
                    arr_t_dep = in_service[dep_idx][0]
                    del in_service[dep_idx]
                    n_in_system -= 1
                    
                    # Record W if departure in window
                    if t >= warmup_end:
                        w_val = t - arr_t_dep
                        sum_W += w_val
                        count_dep += 1
                        
                    # Check waiting queue
                    if waiting:
                        new_arr_t = waiting.pop(0)
                        new_serv_t = rng.expovariate(mu)
                        new_fin_t = t + new_serv_t
                        in_service.append((new_arr_t, new_fin_t))
                        n_in_system += 1 # Wait, n_in_system decreased then increased?
                        # Net change: 1 left, 1 entered service. Count remains same?
                        # No, the one in waiting was already counted in n_in_system.
                        # So moving from waiting to in_service doesn't change n_in_system.
                        # Correction:
                        # Before departure: n = len(in) + len(wait)
                        # After removing from in: n decreases by 1.
                        # If we move from wait to in: n increases by 1.
                        # So net n is unchanged.
                        # But we decremented n_in_system above. So we must increment it back if we pull from wait.
                        n_in_system += 1
                    else:
                        # Server becomes idle
                        pass
                else:
                    # Should not happen
                    pass

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        # Window length
        w_len = H - warmup_end
        
        if w_len > 0:
            L_est = area_L / w_len
            busy_frac_est = area_busy / w_len
            busy_util_est = area_occupied_servers / (w_len * c)
            
            # p_loss: blocked / (blocked + accepted)? Or blocked / total arrivals?
            # Usually loss probability is fraction of attempts lost.
            # p_loss = blk / (blk + accepted_in_window) ?
            # Note: count_arr counts arrivals in window.
            # Some arrivals in window might be blocked.
            # p_loss = count_blk / count_arr if count_arr > 0 else 0
            
            p_loss_est = count_blk / count_arr if count_arr > 0 else 0.0
            
            # W: Average sojourn time of those who departed in window.
            # If count_dep > 0:
            W_est = sum_W / count_dep if count_dep > 0 else 0.0
            
            # p_wait: Probability of waiting.
            # Fraction of accepted customers who had to wait?
            # Or fraction of time there were people waiting?
            # Usually P_wait = L_q / L or similar.
            # Let's define p_wait as fraction of accepted customers who waited.
            # We didn't track this directly.
            # Alternative: Area of waiting queue / Area of system?
            # Let's approximate p_wait using Little's Law components or track it.
            # Tracking: When a customer arrives and joins waiting, mark them.
            # When they enter service, if they were marked, increment wait_count.
            # This requires more state.
            # Given constraints, I'll estimate p_wait as (L - L_s)/L? No.
            # Let's use: p_wait = (Average number waiting) / (Average number in system)?
            # We didn't track area_waiting separately.
            # Let's re-run logic mentally: I need to track waiting area.
            # I will modify the loop slightly in the final code to track area_waiting.
            
            # For now, placeholder based on available data or recalculation needed.
            # I will ensure the final code tracks area_waiting.
            
            # Dep rate
            dep_rate_est = count_dep / w_len if w_len > 0 else 0.0
            lam_eff_est = (count_arr - count_blk) / w_len if w_len > 0 else 0.0
            
        else:
            L_est = 0.0
            busy_frac_est = 0.0
            busy_util_est = 0.0
            p_loss_est = 0.0
            W_est = 0.0
            p_wait_est = 0.0
            dep_rate_est = 0.0
            lam_eff_est = 0.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est) # Will fix in real code
        all_arr.append(count_arr)
        all_blk.append(count_blk)
        all_dep.append(count_dep)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)

    # Aggregate results
    avg_L = sum(all_L) / N_seeds
    avg_W = sum(all_W) / N_seeds
    avg_busy_frac = sum(all_busy_frac) / N_seeds
    avg_p_loss = sum(all_p_loss) / N_seeds
    avg_p_wait = sum(all_p_wait) / N_seeds
    avg_arr = sum(all_arr) / N_seeds
    avg_blk = sum(all_blk) / N_seeds
    avg_dep = sum(all_dep) / N_seeds
    avg_busy_util = sum(all_busy_util) / N_seeds
    avg_dep_rate = sum(all_dep_rate) / N_seeds
    avg_lam_eff = sum(all_lam_eff) / N_seeds
    
    # Convert W to minutes
    W_min = avg_W * 60.0

    result = {
        "L": round(avg_L, 6),
        "W": round(W_min, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x*60, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
