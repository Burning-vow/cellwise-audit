import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    args = p.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    
    if pert == "lam_up":
        lam = lam_base * 1.1
    elif pert == "mu_up":
        mu = mu_base * 1.1
    elif pert == "c_up":
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    warmup_frac = 0.25
    time_unit = "minute"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        n_in_system = 0
        server_busy = False
        
        # For statistics
        area_L = 0.0
        total_time = 0.0
        wait_times_sum = 0.0
        num_completed = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked = 0 # M/M/1 no blocking, but track just in case logic changes or for consistency
        
        # Warmup handling
        warmup_end = H * warmup_frac
        
        # State variables for integration
        last_event_time = 0.0
        
        # We need to simulate until H
        while t < H:
            # Determine next event
            if next_arrival < next_departure:
                t_next = next_arrival
                event_type = 'arrival'
            else:
                t_next = next_departure
                event_type = 'departure'
            
            if t_next > H:
                dt = H - t
                # Integrate before updating state? No, we integrate the duration of current state
                if t >= warmup_end:
                    area_L += n_in_system * dt
                    total_time += dt
                break
            
            dt = t_next - t
            if t >= warmup_end:
                area_L += n_in_system * dt
                total_time += dt
            
            t = t_next
            
            if event_type == 'arrival':
                # Service time drawn at arrival
                svc_time = rng.expovariate(mu)
                
                if not server_busy:
                    server_busy = True
                    next_departure = t + svc_time
                    n_in_system += 1
                    if t >= warmup_end:
                        num_arrivals_window += 1
                        # Wait time is 0
                        wait_times_sum += 0.0
                        num_completed += 1 # This customer will depart later, but we count completion stats when they leave? 
                        # Actually, standard W is average time in system. We accumulate upon departure.
                        # Let's store arrival time and service time on a queue if needed, but for MM1 FCFS single server:
                        # If server idle, start immediately. Departure time known.
                        # We need to know when this specific customer leaves to add their sojourn time.
                        # Since it's MM1, we can just push (arrival_time, departure_time) to a list?
                        # Or simpler: When departure happens, we know who left.
                        # But we need to link arrival to departure.
                        # Let's maintain a queue of customers waiting/serving.
                        pass
                else:
                    # Server busy, join queue
                    n_in_system += 1
                    if t >= warmup_end:
                        num_arrivals_window += 1
                    # Add to queue
                    # We need a data structure to hold customers
                    # Let's use a list of dicts or tuples: (arrival_time, service_time)
                    # But we already drew svc_time.
                    # We'll append to a queue variable defined outside loop?
                    # Refactor: Define queue inside seed loop.
                    pass
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'departure':
                # Customer leaves
                n_in_system -= 1
                if t >= warmup_end:
                    num_departures_window += 1
                
                # Calculate sojourn time for the departing customer
                # We need to know who departed. In MM1 FCFS, it's the head of the queue.
                # So we must have maintained a queue.
                # Let's restart the inner loop logic with proper queue management.
                pass

        # The above draft was messy. Rewriting cleanly below.
        
        # Reset for clean implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        n_in_system = 0
        server_busy = False
        queue = [] # List of (arrival_time, service_time) for those waiting
        
        area_L = 0.0
        total_time_window = 0.0
        sum_sojourn = 0.0
        count_sojourn = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0 # Always 0 for infinite buffer
        
        warmup_end = H * warmup_frac
        
        while t < H:
            # Find next event time
            events = []
            if next_arrival <= H:
                events.append(('arr', next_arrival))
            if next_departure <= H:
                events.append(('dep', next_departure))
            
            if not events:
                break
                
            # Pick earliest
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - t
            if t >= warmup_end:
                area_L += n_in_system * dt
                total_time_window += dt
            
            t = etime
            
            if etype == 'arr':
                svc = rng.expovariate(mu)
                if not server_busy:
                    server_busy = True
                    next_departure = t + svc
                    # Store info for the one being served
                    # We need to know when this person leaves to calculate sojourn.
                    # Since only one is served, we can keep a variable for current customer's arrival time.
                    curr_cust_arr_t = t
                    curr_svc_t = svc
                    n_in_system += 1
                    if t >= warmup_end:
                        arr_count += 1
                else:
                    n_in_system += 1
                    if t >= warmup_end:
                        arr_count += 1
                    queue.append((t, svc))
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'dep':
                # Current customer leaves
                sojourn = t - curr_cust_arr_t
                if t >= warmup_end:
                    sum_sojourn += sojourn
                    count_sojourn += 1
                    dep_count += 1
                
                n_in_system -= 1
                
                if queue:
                    # Next from queue starts service
                    next_arr_t, next_svc_t = queue.pop(0)
                    curr_cust_arr_t = next_arr_t
                    curr_svc_t = next_svc_t
                    next_departure = t + next_svc_t
                else:
                    server_busy = False
                    next_departure = float('inf')
                    
        # End of simulation for this seed
        
        L_est = area_L / total_time_window if total_time_window > 0 else 0.0
        W_est = sum_sojourn / count_sojourn if count_sojourn > 0 else 0.0
        
        # Busy fraction: E[min(N,1)] / 1. 
        # Area where server is busy.
        # We didn't track busy area explicitly. 
        # Note: In MM1, server is busy iff N > 0.
        # So area_busy = area_L? No.
        # N(t) is number in system. Server busy if N(t) >= 1.
        # We need to integrate indicator(N>0).
        # Let's re-run or fix logic. I missed integrating busy status.
        
        # Re-simulate quickly to get busy area? Or modify loop.
        # Modifying loop is better.
        
        # Restarting seed loop with correct busy tracking...
        # To save lines, I will combine the logic properly in the final code block.
        
        # Placeholder for now, will write full correct code in output.
        pass

    # Final Output Construction
    # ...
