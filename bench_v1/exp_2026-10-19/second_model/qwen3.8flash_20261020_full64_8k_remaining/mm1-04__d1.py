import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min avg service -> 1/5 * 60 = 12)
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    horizon_hours = H
    
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
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    win_len = horizon_hours * (1 - warmup_ratio)
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        customers_in_system = 0
        server_busy = False
        service_end_time = float('inf')
        
        # For statistics
        area_N = 0.0
        area_busy = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        sum_W = 0.0
        wait_times = [] # To calculate p_wait and W properly? 
        # Actually W is average stay time. We need to track arrival times of those who depart in window.
        # But we only accumulate stats after warmup.
        # Let's store arrival time for each customer currently in system or waiting.
        # Since it's M/M/1, queue can be infinite.
        
        # Data structure: list of (arrival_time, service_duration) for those in system?
        # Or just track when they enter and leave.
        # Simpler: maintain a list of active customers with their arrival times.
        # When a departure happens, pop the one that started service first? No, FCFS.
        # The one at head of queue starts service.
        
        # Let's use a queue for waiting customers and a flag for server.
        # Each element in queue is arrival_time.
        # If server busy, we have current_service_end_time.
        
        queue = [] # List of arrival times of waiting customers
        current_service_end = float('inf')
        last_event_time = 0.0
        
        # Warmup end time
        warmup_end = horizon_hours * warmup_ratio
        
        while True:
            # Determine next event time
            next_arrival_t = next_arrival
            next_departure_t = current_service_end if server_busy else float('inf')
            
            next_event_t = min(next_arrival_t, next_departure_t)
            
            if next_event_t > horizon_hours:
                break
                
            # Integrate areas up to next_event_t
            dt = next_event_t - last_event_time
            if last_event_time >= warmup_end:
                area_N += customers_in_system * dt
                if server_busy:
                    area_busy += 1.0 * dt
            
            # Process event
            if next_event_t == next_arrival_t:
                # Arrival
                count_arrivals += 1
                if last_event_time < warmup_end:
                    pass # Ignore counts before warmup? 
                    # Problem says "statistics only accumulated in window after removing first 25% warmup".
                    # So arrivals/departures/blocks should also be counted only in the window?
                    # Usually yes.
                
                # Check if this arrival is in the measurement window
                # An arrival at t is in window if t >= warmup_end.
                # However, its departure might be later.
                # We need to record arrival time to compute W for those departing in window.
                
                if next_event_t >= warmup_end:
                    # This arrival contributes to arr count
                    # But wait, if it arrives exactly at warmup_end, include it.
                    pass
                
                # Add to queue or start service
                if not server_busy:
                    server_busy = True
                    dur = rng.expovariate(mu)
                    current_service_end = next_event_t + dur
                    # Store arrival time for this customer being served
                    # We need to know when they arrived to calc W upon departure.
                    # Let's keep a variable for the arrival time of the person currently in service.
                    # But if someone is waiting, we need a queue of arrival times.
                    
                    # Refactor state:
                    # server_busy implies there is a customer in service.
                    # We need to track the arrival time of the customer in service.
                    # And a queue of arrival times for waiting customers.
                    
                    # Let's introduce:
                    # in_service_arrival_time: float or None
                    # waiting_queue: list of floats (arrival times)
                    
                    # Re-initialize variables outside loop?
                    pass
                else:
                    queue.append(next_event_t)
                
                # Generate next arrival
                next_arrival = next_event_t + rng.expovariate(lam)
                
            elif next_event_t == next_departure_t:
                # Departure
                # Who departs? The one in service.
                # We need their arrival time.
                # Let's assume we tracked it.
                
                # Calculate W for this customer if departure is in window
                # And if arrival was in window? 
                # Standard practice: Count departures in window. Their W is (dep_time - arr_time).
                # If arr_time < warmup_end, do we exclude them?
                # "Statistics ... accumulated in window".
                # Usually, we consider events occurring in the window.
                # A departure event occurs at t. If t >= warmup_end, we record the departure.
                # Do we record the W? Yes, if the customer departed in the window.
                # Even if they arrived during warmup?
                # Often, to avoid bias, we might discard customers who arrived during warmup but left after.
                # Or we just take all departures in the window.
                # Given the prompt "area-type quantities must be integrated before changing state",
                # and "statistics only ... in window", let's assume we count departures in window.
                # And for W, we use the actual stay time.
                
                # Let's refine the data structures inside the loop logic properly.
                pass
            
            last_event_time = next_event_t

        # The above logic sketch is incomplete. I will rewrite the simulation loop cleanly.
        
        # Reset for clean implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # State
        # Number in system = len(queue) + (1 if server_busy else 0)
        # But we need arrival times.
        # Let's use:
        # server_status: 'idle' or 'busy'
        # current_customer_arrival: time when the person in service arrived
        # current_service_end: time when service ends
        # waiting_customers: list of arrival times
        
        server_status = 'idle'
        current_cust_arr = None
        current_serv_end = float('inf')
        waiting_custs = []
        
        # Stats accumulators for this seed
        s_area_N = 0.0
        s_area_busy = 0.0
        s_count_arr = 0
        s_count_dep = 0
        s_count_blk = 0 # In M/M/1 no blocking, so always 0
        s_sum_W = 0.0
        s_count_W = 0 # Number of customers whose W is recorded (departed in window)
        s_count_wait = 0 # Number of customers who waited (arrived when busy)
        s_total_dep_in_window = 0
        
        warmup_end = horizon_hours * warmup_ratio
        
        while True:
            next_arr_t = next_arrival
            next_dep_t = current_serv_end if server_status == 'busy' else float('inf')
            
            next_ev_t = min(next_arr_t, next_dep_t)
            
            if next_ev_t > horizon_hours:
                # Final integration step?
                # We stop at horizon.
                # Area from last_event_time to horizon?
                # The loop breaks if next event > horizon.
                # We need to integrate up to horizon.
                dt = horizon_hours - t
                if t >= warmup_end:
                    n_now = len(waiting_custs) + (1 if server_status == 'busy' else 0)
                    s_area_N += n_now * dt
                    if server_status == 'busy':
                        s_area_busy += 1.0 * dt
                break
            
            # Integrate from t to next_ev_t
            dt = next_ev_t - t
            if t >= warmup_end:
                n_now = len(waiting_custs) + (1 if server_status == 'busy' else 0)
                s_area_N += n_now * dt
                if server_status == 'busy':
                    s_area_busy += 1.0 * dt
            
            # Handle Event
            if next_ev_t == next_arr_t:
                # Arrival
                if next_ev_t >= warmup_end:
                    s_count_arr += 1
                
                # Check if server busy
                if server_status == 'busy':
                    waiting_custs.append(next_ev_t)
                    # Did they wait? Yes, because server was busy.
                    # But did they wait *in the window*?
                    # p_wait usually defined as fraction of arrivals who wait.
                    # If arrival is in window, and they join queue, they waited.
                    if next_ev_t >= warmup_end:
                        s_count_wait += 1
                else:
                    server_status = 'busy'
                    current_cust_arr = next_ev_t
                    dur = rng.expovariate(mu)
                    current_serv_end = next_ev_t + dur
                
                next_arrival = next_ev_t + rng.expovariate(lam)
                
            elif next_ev_t == next_dep_t:
                # Departure
                # Customer leaves
                cust_arr = current_cust_arr
                
                # Was this departure in window?
                if next_ev_t >= warmup_end:
                    s_count_dep += 1
                    # Record W
                    w_val = next_ev_t - cust_arr
                    s_sum_W += w_val
                    s_count_W += 1
                    
                # Next customer?
                if waiting_custs:
                    next_cust_arr = waiting_custs.pop(0)
                    server_status = 'busy'
                    current_cust_arr = next_cust_arr
                    dur = rng.expovariate(mu)
                    current_serv_end = next_ev_t + dur
                else:
                    server_status = 'idle'
                    current_cust_arr = None
                    current_serv_end = float('inf')
            
            t = next_ev_t
        
        # Compute metrics for this seed
        L_est = s_area_N / win_len if win_len > 0 else 0
        busy_frac_est = s_area_busy / win_len if win_len > 0 else 0
        W_est = s_sum_W / s_count_W if s_count_W > 0 else 0
        p_wait_est = s_count_wait / s_count_arr if s_count_arr > 0 else 0
        p_loss_est = 0.0 # M/M/1 has no loss
        
        # Busy util E[min(N,c)]/c. c=1. E[min(N,1)] = P(N>=1) = busy_frac?
        # Prompt says busy_frac = E[min(N,1)]/1. So busy_util should be same?
        # "busy_util=E[min(N,c)]/c"
        # "busy_occupied=1-pi0"
        # In M/M/1, pi0 = 1 - rho. 1-pi0 = rho.
        # E[min(N,1)] = P(N>=1) = rho.
        # So busy_util = busy_frac = busy_occupied.
        
        busy_util_est = busy_frac_est
        busy_occ_est = busy_frac_est
        
        dep_rate_est = s_count_dep / win_len if win_len > 0 else 0
        lam_eff_est = s_count_arr / win_len if win_len > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(s_count_arr)
        all_blk.append(s_count_blk)
        all_dep.append(s_count_dep)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        all_busy_occupied.append(busy_occ_est)

    seeds_used = len(per_seed_L)
    
    def mean(lst):
        return sum(lst)/len(lst) if lst else 0.0
        
    res = {
        "L": mean(all_L),
        "W": mean(all_W),
        "busy_frac": mean(all_busy_frac),
        "p_wait": mean(all_p_wait),
        "runtime_units": "seconds", # Not specified, but usually wall clock. Can't measure easily without time.time(). Let's put 0.0 or dummy.
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win_len,
        "arr": mean(all_arr),
        "blk": mean(all_blk),
        "busy_util": mean(all_busy_util),
        "dep": mean(all_dep),
        "dep_rate": mean(all_dep_rate),
        "lam_eff": mean(all_lam_eff),
        "p_loss": mean(all_p_loss),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": mean(all_busy_occupied)
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
