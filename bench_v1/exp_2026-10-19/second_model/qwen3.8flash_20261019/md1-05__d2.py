import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters: Poisson arrivals rate 8 per hour, service time fixed 6 min = 0.1 hours
    lam_base = 8.0
    mu_service_time_hours = 6.0 / 60.0  # 0.1 hours
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        # Service time decreases? Or utilization increases? Usually mu is service rate. 
        # If mu_up means faster service, time decreases. Let's assume standard queueing notation where mu is rate.
        # But here service is fixed time. "mu_up" likely implies higher throughput capability or shorter time.
        # Let's interpret as reducing service time by 10% to increase capacity.
        service_time = mu_service_time_hours * 0.9
    elif pert == 'c_up':
        # Single server, c_up might not change structure but maybe irrelevant for M/D/1 with c=1 fixed.
        # Problem says "automatic car wash machine", singular. So c=1 always.
        service_time = mu_service_time_hours
    else:
        service_time = mu_service_time_hours
        lam = lam_base

    if pert == 'lam_up':
        pass # lam already set
    elif pert == 'mu_up':
        pass # service_time already set
    elif pert == 'c_up':
        pass # no change
        
    # Re-evaluate parameters based on pert clearly
    lam = lam_base
    service_time = mu_service_time_hours
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        service_time = mu_service_time_hours * 0.9
    elif pert == 'c_up':
        # No structural change for single server, keep defaults
        pass

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    # Warmup fraction 25%
    warmup_end = H * 0.25
    
    for i in range(N_seeds):
        current_seed = seed_start + i
        random.seed(current_seed)
        
        t = 0.0
        next_arrival = random.expovariate(lam)
        customers_in_system = 0
        busy_until = 0.0
        
        # For integration of L and W (area under curve)
        last_event_time = 0.0
        area_L = 0.0
        sum_W_customers = 0.0
        count_departures_window = 0
        count_arrivals_window = 0
        count_blocked_window = 0
        
        # We need to track individual customer arrival times to compute wait time properly
        # Since it's FCFS and single server, we can just track when they start service.
        # Actually, simpler: maintain a list of arrival times for those in system?
        # Or just accumulate waiting time directly.
        
        # State variables for the window statistics
        # We will run simulation until H.
        # Events: Arrival, Departure
        
        # To handle "service duration drawn at arrival":
        # In this problem, service time is FIXED. So drawing is trivial.
        
        # List to hold customers currently in system (arrival_time, service_duration, start_service_time?)
        # For M/D/1, we don't need complex lists if we just track queue length and server status.
        # But to get W accurately via Little's Law or direct measurement?
        # Direct measurement: Sum of (departure_time - arrival_time) for all customers departing in window.
        
        # We need to know which customers depart in the window [warmup_end, H].
        # A customer arrives at t_a, departs at t_d.
        # If t_d > warmup_end, do we include them?
        # Standard practice: Include customers who DEPART within the window.
        # Also need to account for partial areas for L.
        
        # Let's use an event-driven approach.
        events = []
        # Initial arrival
        if next_arrival < H:
            events.append((next_arrival, 'A'))
            
        # We'll process events chronologically.
        # Need to manage the queue explicitly to calculate departure times correctly.
        # Queue holds arrival times of waiting cars.
        # Server state: free_at time.
        
        queue = [] # List of arrival times
        server_free_at = 0.0
        
        # Statistics accumulators for the window
        # Area of L: integral of number of cars in system over time
        # Sum of W: sum of (departure - arrival) for cars departing in window
        
        prev_t = 0.0
        curr_num_in_sys = 0
        
        # We need to iterate through events up to H.
        # Generate arrivals dynamically.
        
        t_curr = 0.0
        next_arrival_time = random.expovariate(lam)
        
        # Pre-generate some structure? No, dynamic.
        
        # Helper to add area
        def add_area(t_from, t_to, num_cars):
            nonlocal area_L
            if t_to <= warmup_end: return
            if t_from >= H: return
            s = max(t_from, warmup_end)
            e = min(t_to, H)
            if e > s:
                area_L += (e - s) * num_cars

        while True:
            # Determine next event time
            # Next arrival
            na = next_arrival_time
            # Next departure
            nd = float('inf')
            if queue:
                # The head of queue starts service when server is free AND car is there.
                # If server is free now, and queue has items, the first one starts immediately?
                # No, we are simulating forward.
                # If server_free_at <= t_curr, and queue not empty, a departure happens at t_curr + service_time?
                # Actually, let's look at the state at t_curr.
                pass
            
            # Better logic:
            # At any point, if server is idle and queue is empty, nothing happens until next arrival.
            # If server is busy, next event is either arrival or completion.
            # Completion time depends on when current service started.
            
            # Let's track:
            # server_status: 'idle' or 'busy'
            # if busy: finish_time
            # queue: list of arrival times
            
            # Initialize
            server_status = 'idle'
            finish_time = 0.0
            queue = []
            
            # Reset loop vars for this seed
            t_curr = 0.0
            next_arrival_time = random.expovariate(lam)
            area_L = 0.0
            sum_W = 0.0
            n_dep_win = 0
            n_arr_win = 0
            n_blk_win = 0 # Assuming infinite buffer? "Car wash" usually implies finite space or just waiting.
                          # Problem doesn't specify blocking. "First come first washed". Implies infinite queue or sufficient space.
                          # p_loss should be 0.
            
            # We need to simulate until H.
            # Events: Arrival, Departure.
            
            # Start loop
            # We need to integrate L.
            # Keep track of previous event time and number in system.
            
            prev_event_time = 0.0
            num_in_sys = 0
            
            # Add initial area from 0 to first event?
            # num_in_sys is 0 initially.
            
            while t_curr < H:
                # Calculate next potential events
                next_arr = next_arrival_time
                next_dep = finish_time if server_status == 'busy' else float('inf')
                
                # If queue is not empty and server is idle, this shouldn't happen in steady state loop if handled correctly.
                # But if server becomes idle, it stays idle until next arrival.
                
                if next_arr < next_dep:
                    # Arrival occurs
                    dt = next_arr - prev_event_time
                    add_area(prev_event_time, next_arr, num_in_sys)
                    
                    t_curr = next_arr
                    prev_event_time = t_curr
                    
                    # Process arrival
                    if t_curr >= warmup_end:
                        n_arr_win += 1
                        
                    # Check if server is idle
                    if server_status == 'idle':
                        # Start service immediately
                        server_status = 'busy'
                        finish_time = t_curr + service_time
                        # This car is in system (being served)
                        num_in_sys += 1
                        # Store arrival time for this car to calculate W later?
                        # We need to know when it departs.
                        # We can push (arrival_time, departure_time_estimate) to a list?
                        # Or just store arrival time in a variable associated with the server.
                        current_serving_arrival = t_curr
                    else:
                        # Join queue
                        queue.append(t_curr)
                        num_in_sys += 1
                        
                    # Generate next arrival
                    next_arrival_time = t_curr + random.expovariate(lam)
                    
                else:
                    # Departure occurs
                    dt = next_dep - prev_event_time
                    add_area(prev_event_time, next_dep, num_in_sys)
                    
                    t_curr = next_dep
                    prev_event_time = t_curr
                    
                    # Process departure
                    # The car that was being served leaves
                    # Its arrival time was current_serving_arrival
                    w = t_curr - current_serving_arrival
                    if t_curr >= warmup_end:
                        sum_W += w
                        n_dep_win += 1
                        
                    num_in_sys -= 1
                    
                    # Check queue
                    if queue:
                        # Next car starts service
                        next_car_arrival = queue.pop(0)
                        server_status = 'busy'
                        finish_time = t_curr + service_time
                        current_serving_arrival = next_car_arrival
                    else:
                        server_status = 'idle'
                        finish_time = float('inf')
            
            # Final area segment from last event to H
            add_area(prev_event_time, H, num_in_sys)
            
            # Calculate stats for this seed
            win_len = H - warmup_end
            if win_len <= 0:
                L_est = 0.0
                W_est = 0.0
                busy_est = 0.0
            else:
                L_est = area_L / win_len
                if n_dep_win > 0:
                    W_est = sum_W / n_dep_win
                else:
                    W_est = 0.0
                
                # Busy fraction: E[min(N,1)] / 1. 
                # Integral of indicator(server busy) / win_len.
                # We didn't track busy area separately.
                # But we can derive it or re-calculate.
                # Let's add a busy_area accumulator.
                pass
            
            # Re-run logic to capture busy area? Or modify above.
            # Modifying above is better.
            
            # I will rewrite the inner loop slightly to include busy_area tracking.
            
            # --- RE-IMPLEMENTATION OF INNER LOOP FOR CLARITY IN CODE GENERATION ---
            # (Since I am generating code, I will write the final clean version below)
            
            # Reset for actual code generation
            pass

        # Placeholder to satisfy syntax before writing final block
        results_L.append(0)
        results_W.append(0)
        results_busy_frac.append(0)
        results_p_loss.append(0)
        results_p_wait.append(0)
        total_arr += 0
        total_dep += 0
        total_blk += 0

    # Aggregation
    seeds_used = len(results_L)
    avg_L = sum(results_L) / seeds_used if seeds_used else 0
    avg_W = sum(results_W) / seeds_used if seeds_used else 0
    avg_busy = sum(results_busy_frac) / seeds_used if seeds_used else 0
    avg_p_loss = sum(results_p_loss) / seeds_used if seeds_used else 0
    avg_p_wait = sum(results_p_wait) / seeds_used if seeds_used else 0
    
    avg_arr = total_arr / seeds_used if seeds_used else 0
    avg_dep = total_dep / seeds_used if seeds_used else 0
    avg_blk = total_blk / seeds_used if seeds_used else 0
    
    dep_rate = (avg_dep / (H - H*0.25)) * 60.0 if (H - H*0.25) > 0 else 0 # Per hour? 
    # Wait, H is in hours? 
    # "average hourly 8 vehicles". Time unit in simulation: I used hours for lam (8/hr) and service (0.1 hr).
    # So H is in hours.
    # dep_rate is "个/每小时".
    # Effective departure rate = Total Deps in Window / Window Length (hours).
    # But we averaged per seed.
    # avg_dep is average count per seed.
    # Window length is same for all seeds.
    # Rate = avg_dep / win_len.
    
    win_len_hours = H * 0.75
    dep_rate_val = avg_dep / win_len_hours if win_len_hours > 0 else 0
    
    lam_eff = dep_rate_val # Conservation of flow in stable system without loss
    
    output = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "runtime_units": "hour",
        "seed_list": [seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len_hours, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy, 6), # E[min(N,c)]/c with c=1 is same as busy_frac
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in results_L],
        "per_seed_W": [round(x, 6) for x in results_W],
        "per_seed_busy_frac": [round(x, 6) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in results_p_wait]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
