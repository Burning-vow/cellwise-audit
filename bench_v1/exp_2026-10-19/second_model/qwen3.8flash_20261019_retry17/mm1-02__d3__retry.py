import sys, json, random, math

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # in hours
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H_horizon = args.horizon
    S_start = args.seed_start
    pert_name = args.pert

    # Parameters
    # Lambda: arrivals per hour
    lam_base = 4.0 
    # Mu: service rate per hour (mean service time 5 mins = 1/12 hour -> mu = 12/hr)
    mu_base = 12.0 
    
    if pert_name == 'lam_up':
        lam = lam_base * 1.1
        mu = mu_base
    elif pert_name == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert_name == 'c_up':
        # c is capacity/servers, but problem says 1 server. 
        # "perturbation only changes parameters not structure". 
        # If c_up implies changing number of servers, it violates "structure" if we add servers.
        # However, usually c refers to cost or capacity. In M/M/1 context, maybe it's a distractor or implies lambda/mu change?
        # The prompt says "NAME takes none/lam_up/mu_up/c_up". 
        # Let's assume c_up might mean increasing arrival rate further or decreasing service rate?
        # Or perhaps it's a typo for something else. Given strict constraints, let's treat c_up as no-op or slight variation if needed.
        # But wait, standard discrete event sim perturbations often test sensitivity.
        # Let's stick to base params for c_up unless specified otherwise, or maybe it affects lambda?
        # Actually, looking at typical queueing problems, c might be cost. But here we simulate physics.
        # Let's assume c_up does nothing to physical rates for now, or maybe it's a trick.
        # Re-reading: "perturbation only changes parameters not structure".
        # If I have to guess, maybe c is related to lambda? No, lam_up exists.
        # Maybe c is the number of servers? But structure is fixed at 1.
        # Let's just use base parameters for c_up to be safe, or apply a small factor to both?
        # Let's assume c_up means "cost up" which doesn't affect simulation dynamics directly in this model.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    # Warmup fraction
    warmup_frac = 0.25
    
    for i in range(N_seeds):
        seed_val = S_start + i
        rng = random.Random(seed_val)
        
        # Simulation variables
        t = 0.0
        next_arrival_t = rng.expovariate(lam)
        # Service times are drawn upon arrival and attached to customer
        # We need a queue of customers waiting for service
        # Each customer: (arrival_time, service_duration)
        queue = [] 
        
        # State tracking for integration
        # We need to integrate L(t) over time to get average L
        # And integrate busy indicator to get busy_frac
        
        last_event_time = 0.0
        current_num_in_system = 0 # Includes those in service and waiting
        current_server_busy = False
        
        # Accumulators for the statistical window
        # Window starts after warmup
        warmup_end = H_horizon * warmup_frac
        
        # To handle area integration correctly with pre-warmup exclusion:
        # We track integral of N(t) from warmup_end to H_horizon
        # And integral of Busy(t) from warmup_end to H_horizon
        
        int_N_window = 0.0
        int_Busy_window = 0.0
        
        # Counters within window
        count_arr_window = 0
        count_dep_window = 0
        count_blk_window = 0 # Losses (if any, though M/M/1 infinite buffer has no loss, but p_loss defined as 0?)
        # Problem says "system stable", M/M/1 usually infinite queue. 
        # "blk" is rejected/lost. In M/M/1 FCFS infinite buffer, blk=0.
        # p_wait: probability that an arriving customer waits (finds server busy).
        
        count_wait_arrivals_window = 0 # Arrivals that had to wait (server busy upon arrival)
        total_service_time_sum_window = 0.0 # Sum of sojourn times for completed services in window?
        # W is average time in system. Usually calculated as Total Time in System / Number of Customers Completed.
        # Or via Little's Law L = lambda * W. 
        # The prompt asks for W directly. Best estimate: Average of (departure_time - arrival_time) for all customers who departed during the window?
        # Or all customers who arrived during the window?
        # Standard definition: Average sojourn time of customers served in the interval.
        # Let's accumulate sum of sojourn times for departures occurring in the window.
        sum_sojourn_window = 0.0
        num_departures_window = 0
        
        # Event loop
        # Events: Arrival, Departure
        # Next departure time depends on when service started.
        # If server idle, next departure is infinity until an arrival happens.
        
        next_departure_t = float('inf')
        
        while t < H_horizon:
            # Determine next event time
            next_event_t = min(next_arrival_t, next_departure_t)
            
            if next_event_t > H_horizon:
                break
            
            # Advance time
            dt = next_event_t - last_event_time
            
            # Integrate state over [last_event_time, next_event_t]
            # Only add to window integrals if the interval overlaps with [warmup_end, H_horizon]
            
            overlap_start = max(last_event_time, warmup_end)
            overlap_end = min(next_event_t, H_horizon)
            
            if overlap_start < overlap_end:
                duration_overlap = overlap_end - overlap_start
                int_N_window += current_num_in_system * duration_overlap
                if current_server_busy:
                    int_Busy_window += duration_overlap
            
            t = next_event_t
            last_event_time = t
            
            # Process Event
            if t == next_arrival_t:
                # Arrival
                # Draw service time NOW and attach to customer
                svc_time = rng.expovariate(mu)
                
                # Check if server is busy
                if current_server_busy:
                    # Customer waits
                    queue.append((t, svc_time))
                    current_num_in_system += 1
                    
                    # Record wait status for p_wait calculation
                    if t >= warmup_end:
                        count_wait_arrivals_window += 1
                
                else:
                    # Server free, start service immediately
                    current_server_busy = True
                    next_departure_t = t + svc_time
                    current_num_in_system += 1
                    # Store info about the customer currently in service?
                    # We need to know their arrival time to calculate sojourn time later.
                    # Since only one in service, we can store it separately or push to a "in-service" slot.
                    # Let's keep a variable for the customer in service.
                    cust_in_service = (t, svc_time)
                    
                # Update counters for arrivals in window
                if t >= warmup_end:
                    count_arr_window += 1
                
                # Schedule next arrival
                next_arrival_t = t + rng.expovariate(lam)
                
            elif t == next_departure_t:
                # Departure
                # The customer finishing service is the one who was in service.
                # We need their arrival time.
                # How did we store it? 
                # If we used `cust_in_service` variable above, we need to maintain it.
                # Let's refactor slightly: maintain `current_cust_info` = (arrival_time, service_duration)
                
                # Wait, in the arrival block, if server was free, I set `cust_in_service`.
                # If server was busy, I pushed to queue.
                # When departure happens, we remove the head of the queue? No, the one in service leaves.
                # Then we check if queue is empty.
                
                # Retrieve arrival time of departing customer
                # This requires storing the arrival time of the person currently being served.
                # Let's ensure `cust_in_service` is accessible.
                
                arr_time_of_departer = cust_in_service[0]
                sojourn_time = t - arr_time_of_departer
                
                # Update counters for departures in window
                if t >= warmup_end:
                    count_dep_window += 1
                    sum_sojourn_window += sojourn_time
                    num_departures_window += 1
                
                current_num_in_system -= 1
                
                # Start next service if available
                if len(queue) > 0:
                    next_cust = queue.pop(0)
                    cust_in_service = next_cust
                    next_departure_t = t + next_cust[1]
                    # Server remains busy
                    current_server_busy = True
                else:
                    current_server_busy = False
                    next_departure_t = float('inf')
                    cust_in_service = None

        # End of simulation for this seed
        
        # Calculate metrics for this seed based on window data
        win_len = H_horizon - warmup_end
        
        if win_len <= 0:
             # Fallback if horizon too short
             L_est = 0.0
             W_est = 0.0
             busy_est = 0.0
             p_wait_est = 0.0
             p_loss_est = 0.0
        else:
            L_est = int_N_window / win_len
            # W = Average Sojourn Time of customers who DEPARTED in the window
            if num_departures_window > 0:
                W_est = sum_sojourn_window / num_departures_window
            else:
                W_est = 0.0 # Should not happen in stable long run
            
            busy_est = int_Busy_window / win_len
            
            # p_wait: Fraction of ARRIVALS in window that found server busy
            if count_arr_window > 0:
                p_wait_est = count_wait_arrivals_window / count_arr_window
            else:
                p_wait_est = 0.0
                
            # p_loss: M/M/1 infinite buffer -> 0 losses
            p_loss_est = 0.0

        seeds_used.append(seed_val)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += count_arr_window
        total_dep += count_dep_window
        total_blk += count_blk_window

    # Aggregate results
    avg_L = sum(per_seed_L) / N_seeds if N_seeds > 0 else 0.0
    avg_W = sum(per_seed_W) / N_seeds if N_seeds > 0 else 0.0
    avg_busy_frac = sum(per_seed_busy_frac) / N_seeds if N_seeds > 0 else 0.0
    avg_p_wait = sum(per_seed_p_wait) / N_seeds if N_seeds > 0 else 0.0
    avg_p_loss = sum(per_seed_p_loss) / N_seeds if N_seeds > 0 else 0.0
    
    # Per-seed averages for counts
    avg_arr_per_seed = total_arr / N_seeds if N_seeds > 0 else 0.0
    avg_dep_per_seed = total_dep / N_seeds if N_seeds > 0 else 0.0
    avg_blk_per_seed = total_blk / N_seeds if N_seeds > 0 else 0.0
    
    # dep_rate: effective departure rate per hour
    # Total departures in window across all seeds / Total window time across all seeds
    total_window_time = N_seeds * (H_horizon - warmup_frac * H_horizon)
    if total_window_time > 0:
        dep_rate = total_dep / total_window_time
    else:
        dep_rate = 0.0
        
    # lam_eff: effective arrival rate
    if total_window_time > 0:
        lam_eff = total_arr / total_window_time
    else:
        lam_eff = 0.0

    # busy_util: E[min(N,c)]/c. Here c=1. So E[N]/1 = L.
    # But strictly, util is fraction of time server is busy.
    # Prompt: "busy_util=E[min(N,c)]/c". For M/M/1, min(N,1) is 1 if N>=1, 0 if N=0.
    # So E[min(N,1)] = P(N>=1) = 1 - pi_0.
    # This is exactly the busy fraction.
    busy_util = avg_busy_frac
    
    # busy_occupied = 1 - pi_0. Same as busy_util in M/M/1.
    busy_occupied = avg_busy_frac
    
    # Output JSON
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "seconds", # Not requested in keys list explicitly? "键必须包含... runtime_units". Yes.
        "seed_list": seeds_used,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(H_horizon - warmup_frac * H_horizon, 6),
        "arr": round(avg_arr_per_seed, 6),
        "blk": round(avg_blk_per_seed, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep_per_seed, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
