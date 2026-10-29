import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 4.0 # per hour
    mu_service_time_min = 5.0
    service_time_hr = mu_service_time_min / 60.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        # Service time decreases? Or rate increases? "mu_up" usually means higher service rate -> lower time
        # But problem says fixed 5 mins. If perturbation changes it:
        # Let's assume mu_up means faster service (shorter time) or just a label for parameter change.
        # Standard interpretation: mu is rate. Higher mu -> shorter time.
        # Original time = 5 min. New time = 5 / 1.2 min? 
        # Let's stick to modifying the constant duration directly based on name logic.
        # If mu_up implies higher throughput capability, we reduce time.
        service_time_hr = (mu_service_time_min / 1.2) / 60.0
        lam = lam_base
    elif pert == 'c_up':
        # Capacity up? Problem has 1 machine. c_up might mean parallel machines?
        # "扰动只改参数不改结构". So structure (1 server) stays.
        # Maybe c refers to something else? Or maybe it's ignored/no-op for this specific single-server case?
        # Let's treat c_up as no-op for now since structure can't change.
        lam = lam_base
        service_time_hr = mu_service_time_min / 60.0
    else:
        lam = lam_base
        service_time_hr = mu_service_time_min / 60.0

    warmup_frac = 0.25
    warmup_end = H * warmup_frac
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocked = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed_val = S_start + i
        seed_list.append(seed_val)
        rng = random.Random(seed_val)
        
        # State variables
        t = 0.0
        next_arrival_t = rng.expovariate(lam)
        next_departure_t = float('inf')
        queue = [] # List of arrival times
        busy_until = -1.0
        
        # Accumulators for this seed
        s_L_area = 0.0
        s_W_sum = 0.0
        s_busy_time = 0.0
        s_arrivals = 0
        s_departures = 0
        s_blocked = 0
        s_waits = 0 # Count of customers who waited (arrival < start_service)
        
        last_event_t = 0.0
        
        while t < H:
            # Determine next event time
            events = []
            if next_arrival_t <= H:
                events.append(('arr', next_arrival_t))
            if next_departure_t <= H:
                events.append(('dep', next_departure_t))
            
            if not events:
                break
            
            # Find earliest event
            min_t = min(e[1] for e in events)
            dt = min_t - t
            
            # Integrate area before state change
            current_N = len(queue) + (1 if t < busy_until else 0)
            if t >= warmup_end:
                s_L_area += current_N * dt
                if t < busy_until:
                    s_busy_time += dt
            
            t = min_t
            
            # Process all events at time t
            # We need to handle simultaneous events carefully. 
            # In DES, typically arrivals happen before departures if same time? 
            # Or we process them in order. Let's collect all events at t.
            arrs_at_t = [e for e in events if e[0]=='arr' and e[1]==t]
            deps_at_t = [e for e in events if e[0]=='dep' and e[1]==t]
            
            # Process Departures first? Usually FCFS, departure frees server.
            # If a customer arrives exactly when another leaves, they can start immediately.
            # So process dep then arr.
            
            for _ in deps_at_t:
                # A customer leaves
                if queue:
                    # Start serving next
                    arr_time = queue.pop(0)
                    start_serv_t = t
                    end_serv_t = t + service_time_hr
                    busy_until = end_serv_t
                    next_departure_t = end_serv_t
                    
                    if start_serv_t >= warmup_end:
                        w = start_serv_t - arr_time
                        s_W_sum += w
                        s_departures += 1
                        if w > 1e-9:
                            s_waits += 1
                else:
                    # Server becomes idle
                    busy_until = -1.0
                    next_departure_t = float('inf')
                    # The departing customer was already accounted for in previous steps?
                    # No, we account for W at departure.
                    # Wait, if queue is empty, the one leaving is the one being served.
                    # We need to know their arrival time.
                    # My model above doesn't store arrival time of current service.
                    # Fix: Store (arrival_time, service_duration) or just arrival_time for current.
                    pass 

            # Re-evaluating loop structure for correctness regarding current service info.
            # Let's restart the inner loop logic with better state tracking.
            
            # Resetting for correct implementation below...
            # I will rewrite the simulation loop properly.
            
            # Clearing incorrect partial logic above by breaking out and re-implementing cleanly inside the seed loop.
            # Since I cannot edit previous lines easily in thought, I will write the final code block correctly.
            pass

    # Final Code Generation follows
