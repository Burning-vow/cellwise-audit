import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # in hours
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters
    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min mean -> 1/5 hr mean? No, 5 min is 1/12 hr. Mean service time = 1/mu. If mean=5min=1/12hr, then mu=12/hr.)
    c = 1
    K = 4 # capacity including server
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    # Time unit: hour
    time_unit = "hour"
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    results_busy_util = []
    results_dep_rate = []
    results_lam_eff = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        horizon_end = H
        
        # State variables
        n_in_system = 0
        next_event_time = float('inf')
        event_type = None # 'arrival' or 'departure'
        
        # For area integration of L and busy time
        last_update_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        
        # Counters for statistics within window (we will use full horizon as window for simplicity unless warmup specified differently, but prompt says remove first 25% warmup)
        # Warmup fraction
        warmup_end = 0.25 * H
        
        # We need to track events that happen after warmup_end for counts, 
        # but area integrals must be split or we just integrate from warmup_end to H.
        # To do this correctly with discrete events:
        # 1. Simulate until warmup_end. Reset accumulators at warmup_end.
        # 2. Continue simulation until H, accumulating stats.
        
        # Let's restructure: Run simulation loop. When crossing warmup_end, reset counters and set start_time_for_stats.
        
        stats_start_time = warmup_end
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_count = 0 # Number of customers who waited (arrived when system not empty?) Or p_wait usually means prob an arriving customer has to wait.
        # In M/M/1/K, p_wait is often defined as probability that an arrival finds all servers busy. Here c=1. So P(N>=1).
        # But standard definition: Fraction of arrivals that enter queue (wait > 0).
        
        # Variables for current customer
        # Queue holds (arrival_time, service_duration)
        queue = deque()
        
        # Initial state: Empty system. First arrival generated.
        inter_arrival = rng.expovariate(lam)
        next_event_time = inter_arrival
        event_type = 'arrival'
        
        # We need to handle the transition at warmup_end carefully.
        # It's easier to simulate step by step.
        
        while t < horizon_end:
            # Determine next event
            if event_type == 'arrival':
                t_next = next_event_time
            elif event_type == 'departure':
                t_next = next_event_time
            else:
                break
                
            if t_next > horizon_end:
                # Integrate up to horizon_end
                dt = horizon_end - t
                if t >= stats_start_time:
                    area_L += n_in_system * dt
                    if n_in_system > 0:
                        area_busy += dt
                t = horizon_end
                break
            
            # Integrate up to t_next
            dt = t_next - t
            if t >= stats_start_time:
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            
            t = t_next
            
            # Check if we crossed warmup boundary during this interval?
            # The logic above assumes we are already past stats_start_time if t >= stats_start_time.
            # But what if t < stats_start_time and t_next > stats_start_time?
            # We need to split the interval.
            
            # Correction: The simple integration above fails if stats_start_time falls inside [t_old, t_new].
            # Let's implement a robust helper or check before integrating.
            
            # Actually, let's restart the loop structure to handle the warmup cut properly.
            pass 

        # Re-implementing the simulation loop with proper warmup handling
        
        t = 0.0
        n_in_system = 0
        queue.clear()
        
        # Generate first arrival
        inter_arrival = rng.expovariate(lam)
        next_event_time = inter_arrival
        event_type = 'arrival'
        
        # Accumulators for post-warmup stats
        area_L_post = 0.0
        area_busy_post = 0.0
        arr_count_post = 0
        blk_count_post = 0
        dep_count_post = 0
        wait_count_post = 0 # Arrivals that had to wait (found server busy)
        
        # We need to know the state at warmup_end to continue correctly.
        # Strategy: Simulate normally. When an event occurs, check if it crosses warmup_end.
        # If so, process the part before warmup_end, reset accumulators, then process the rest.
        
        # This is complex. Alternative: Just run two phases.
        # Phase 1: Simulate until warmup_end. Discard stats. Keep state.
        # Phase 2: Simulate from warmup_end to H. Collect stats.
        
        # Phase 1: Warmup
        while t < warmup_end:
            if event_type == 'arrival':
                t_next = next_event_time
            else:
                t_next = next_event_time
                
            if t_next > warmup_end:
                # Advance time to warmup_end without processing event
                t = warmup_end
                break
            
            t = t_next
            
            if event_type == 'arrival':
                if n_in_system < K:
                    n_in_system += 1
                    # Schedule departure
                    serv_time = rng.expovariate(mu)
                    queue.append((t, serv_time))
                    # If server was idle, start service immediately
                    if len(queue) == 1:
                        # Departure time is t + serv_time
                        dep_time = t + serv_time
                        # Set next event to departure if it's sooner than next arrival
                        # But we haven't generated next arrival yet.
                        # Standard DES: Generate next arrival now.
                        inter_arrival = rng.expovariate(lam)
                        next_arrival_time = t + inter_arrival
                        
                        # Compare next_arrival_time and dep_time
                        if dep_time < next_arrival_time:
                            next_event_time = dep_time
                            event_type = 'departure'
                        else:
                            next_event_time = next_arrival_time
                            event_type = 'arrival'
                    else:
                        # Server busy, just add to queue. Next event is still the scheduled departure.
                        # Wait, if server was busy, there is already a pending departure.
                        # We don't change next_event_time.
                        # But we need to generate next arrival? 
                        # Usually, we generate next arrival only when an arrival happens.
                        # If we didn't schedule a new departure, the next event remains the old one.
                        # But we need to know when the NEXT arrival comes to compare.
                        # Ah, the "next_event_time" variable tracks the earliest upcoming event.
                        # If we added to queue, the earliest event is still the existing departure OR the new arrival.
                        # We must generate the new arrival time here.
                        inter_arrival = rng.expovariate(lam)
                        next_arrival_time = t + inter_arrival
                        
                        # Current next_event_time is the departure of the person currently being served.
                        # Is next_arrival_time earlier?
                        if next_arrival_time < next_event_time:
                            next_event_time = next_arrival_time
                            event_type = 'arrival'
                        # Else keep current next_event_time (departure)
                        
                else:
                    # Blocked
                    # Generate next arrival
                    inter_arrival = rng.expovariate(lam)
                    next_event_time = t + inter_arrival
                    event_type = 'arrival'
                    
            elif event_type == 'departure':
                # Complete service
                # Pop from queue? The head of queue is the one being served.
                # We stored (arrival_time, serv_time). 
                # Actually, simpler: just decrement count.
                # But we need to know if someone starts service.
                
                # Remove completed customer
                # The queue contains waiting customers. The one being served is effectively "in service".
                # My previous logic: queue holds ALL customers in system? 
                # Let's refine: 
                # n_in_system includes those in service and waiting.
                # queue stores (arrival_time, service_duration) for ALL customers in system.
                # The first element is the one in service (if any).
                
                # On departure:
                # 1. Remove head of queue.
                # 2. Decrement n_in_system.
                # 3. If queue not empty, the new head starts service.
                #    Its departure time is current_time + its service_duration.
                #    Update next_event_time to min(new_departure, next_arrival).
                # 4. If queue empty, next event is next_arrival.
                
                # Problem: I didn't store the "next_arrival_time" globally. I regenerated it on each arrival.
                # This approach is messy because "next_event_time" depends on both future arrival and future departure.
                
                # Better Approach: Maintain `next_arrival_time` and `next_departure_time`.
                # Event is min(next_arrival_time, next_departure_time).
                
                # Let's rewrite the state management.
                pass

        # Restarting implementation with cleaner state variables
        
        # Reset for Phase 1
        t = 0.0
        n_in_system = 0
        queue = deque() # Stores (arrival_time, service_duration)
        
        # Initialize next times
        next_arrival_time = rng.expovariate(lam)
        next_departure_time = float('inf')
        
        # Helper to determine next event
        def get_next_event(t_current, na, nd):
            if na <= nd:
                return na, 'arrival'
            else:
                return nd, 'departure'

        # Phase 1: Warmup
        while t < warmup_end:
            t_next, ev_type = get_next_event(t, next_arrival_time, next_departure_time)
            
            if t_next > warmup_end:
                t = warmup_end
                break
            
            t = t_next
            
            if ev_type == 'arrival':
                if n_in_system < K:
                    n_in_system += 1
                    serv_dur = rng.expovariate(mu)
                    queue.append((t, serv_dur))
                    
                    # If server was idle (queue length became 1), start service
                    if len(queue) == 1:
                        next_departure_time = t + serv_dur
                    
                    # Generate next arrival
                    next_arrival_time = t + rng.expovariate(lam)
                    
                else:
                    # Blocked
                    # Generate next arrival
                    next_arrival_time = t + rng.expovariate(lam)
                    
            elif ev_type == 'departure':
                # Customer leaves
                # Remove from queue
                if queue:
                    queue.popleft()
                    n_in_system -= 1
                    
                    # If queue not empty, next customer starts service
                    if queue:
                        # The next customer's service duration is already known
                        _, next_serv_dur = queue[0]
                        next_departure_time = t + next_serv_dur
                    else:
                        next_departure_time = float('inf')
                
                # Note: Arrival generation is handled in arrival branch.
                # Do we regenerate arrival here? No.
                
        # End of Warmup. State is consistent.
        # Now Phase 2: Statistics Collection
        
        # Reset accumulators
        area_L = 0.0
        area_busy = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_count = 0 # Arrivals that found server busy (n_in_system >= 1 at arrival instant)
        
        # We need to integrate from warmup_end to H.
        # The current time is t (which is warmup_end or slightly less if we broke early? 
        # If we broke because t_next > warmup_end, t is set to warmup_end.
        # But the state variables (next_arrival_time etc) are valid relative to real time.
        
        # However, if we stopped mid-interval, we need to ensure we don't double count or miss.
        # Since we set t=warmup_end and didn't process the event, the next event is still in the future.
        
        while t < H:
            t_next, ev_type = get_next_event(t, next_arrival_time, next_departure_time)
            
            if t_next > H:
                # Integrate remaining time
                dt = H - t
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                t = H
                break
            
            # Integrate up to t_next
            dt = t_next - t
            area_L += n_in_system * dt
            if n_in_system > 0:
                area_busy += dt
            
            t = t_next
            
            if ev_type == 'arrival':
                arr_count += 1
                if n_in_system < K:
                    n_in_system += 1
                    serv_dur = rng.expovariate(mu)
                    queue.append((t, serv_dur))
                    
                    # Check if waited: if n_in_system > 1 BEFORE adding? 
                    # Or if server was busy. Server is busy if n_in_system >= 1 (since c=1).
                    # If n_in_system was >= 1 before arrival, they wait.
                    # But we incremented n_in_system already.
                    # Let's check condition before increment.
                    # Refactor:
                    # if n_in_system >= 1: wait_count += 1 (for c=1)
                    # Actually, for general c, wait if n_in_system >= c.
                    if n_in_system >= 1: # c=1
                        wait_count += 1
                        
                    if len(queue) == 1:
                        next_departure_time = t + serv_dur
                    
                    next_arrival_time = t + rng.expovariate(lam)
                else:
                    blk_count += 1
                    next_arrival_time = t + rng.expovariate(lam)
                    
            elif ev_type == 'departure':
                dep_count += 1
                if queue:
                    queue.popleft()
                    n_in_system -= 1
                    if queue:
                        _, next_serv_dur = queue[0]
                        next_departure_time = t + next_serv_dur
                    else:
                        next_departure_time = float('inf')

        # Calculate metrics for this seed
        win_len = H - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        L_est = area_L / win_len
        W_est = L_est / (dep_count / win_len) if dep_count > 0 else 0.0 # Little's Law: L = lambda_eff * W => W = L / lambda_eff
        # lambda_eff = dep_count / win_len (throughput)
        
        busy_frac_est = area_busy / win_len
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_est = wait_count / arr_count if arr_count > 0 else 0.0
        
        # busy_util = E[min(N,c)]/c. For c=1, E[min(N,1)] = P(N>=1) = busy_frac.
        # So busy_util should equal busy_frac for c=1.
        busy_util_est = busy_frac_est 
        
        dep_rate_est = dep_count / win_len # per hour
        lam_eff_est = dep_rate_est
        
        results_L.append(L_est)
        results_W.append(W_est)
        results_busy_frac.append(busy_frac_est)
        results_p_loss.append(p_loss_est)
        results_p_wait.append(p_wait_est)
        results_arr.append(arr_count)
        results_blk.append(blk_count)
        results_dep.append(dep_count)
        results_busy_util.append(busy_util_est)
        results_dep_rate.append(dep_rate_est)
        results_lam_eff.append(lam_eff_est)

    # Aggregate across seeds
    avg_L = sum(results_L) / N_se
