import json, math, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min mean -> 1/5 hr^-1? No, 5 min is 1/12 hr. So rate is 12/hr)
    c = 1
    K = 4 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 2
        K = 5 # Assuming capacity scales or just adding server? Problem says "only 1 doctor", but perturbation changes parameters. 
              # If c_up means more doctors, capacity might change. Let's assume K remains total slots? 
              # Usually c_up implies increasing servers. If servers increase, waiting room size might stay same or total capacity increases.
              # Given "候诊区连同诊室内一共只能容纳 4 人", this is a hard constraint on system state N <= 4.
              # If we add a doctor, does the capacity become 5? Or is it still 4 people max in the building?
              # The problem statement defines the base model. Perturbations modify parameters.
              # Let's assume K is fixed at 4 for simplicity unless specified otherwise, but usually c affects service rate distribution.
              # However, standard M/M/c/K has K as max customers. If c changes, K might need adjustment to keep physical space constant?
              # Let's stick to modifying rates only for lam/mu, and for c_up, let's assume it means faster service effectively? 
              # No, c is number of servers. If c=2, then service rate is sum of two exp(12). 
              # But the capacity constraint "4 people" is likely physical. So K=4 regardless of c?
              # If c=2, then when 2 are being served, 2 can wait. Total 4. This fits.
              pass
    else:
        lam = lam_base
        mu = mu_base
        
    # Re-evaluate pert logic for c_up
    if pert == 'c_up':
        c = 2
        # Service rate per server is still mu_base? Or total capacity doubles?
        # Standard interpretation: c servers, each with rate mu.
        # Capacity K is still 4 (physical limit).
        pass

    time_unit = 'hour'
    win = H * 0.75 # Remove first 25% warmup
    start_time_warmup = H * 0.25
    
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
        n = 0 # Number of customers in system
        next_arrival = rng.expovariate(lam)
        # We need to track service completion times for up to c servers.
        # Since c is small, we can maintain a list of remaining service times or absolute finish times.
        # Better: maintain a priority queue of events.
        # Events: Arrival, Departure.
        # When an arrival happens, if n < K, customer enters. Service time drawn immediately.
        # If n >= K, blocked.
        # Departures happen when service finishes.
        
        # To handle multiple servers efficiently without complex classes:
        # We can simulate event by event.
        # List of active service end times.
        active_services = [] 
        
        # Statistics accumulators (for area integration)
        # L_area: integral of n(t) dt over [start_time_warmup, H]
        # Busy_time: integral of (n(t)>0 ? 1 : 0) dt over window
        # Wait_time_sum: sum of waiting times for completed services that started after warmup? 
        # W definition: Average waiting time in system (sojourn time) or queueing time?
        # Usually W in Little's Law context is sojourn time (waiting + service).
        # "W（分钟）" - typically mean time in system.
        # We need to accumulate total time spent in system for all customers who departed during the measurement window?
        # Or all customers who arrived during the window?
        # Standard discrete event simulation for steady state:
        # L = Area / Time_window
        # W = Total_Time_In_System_of_Departed_Customers_in_Window / Count_Departed_in_Window
        # p_loss = Blocked_Count / Arrivals_Count (in window)
        # busy_frac = Busy_Time / Time_window
        
        # Need to track individual customer entry time to calculate sojourn time upon departure.
        # Since we don't use classes, we can store tuples in active_services: (finish_time, entry_time)
        
        last_event_time = 0.0
        current_n = 0
        
        # Pre-generate arrivals? No, dynamic.
        # Event loop
        while t < H:
            # Determine next event time
            next_departure = float('inf')
            if active_services:
                # Find min finish time
                # active_services stores (finish_time, entry_time)
                # We can sort or just scan since c is small
                min_idx = -1
                min_time = float('inf')
                for idx, (ft, et) in enumerate(active_services):
                    if ft < min_time:
                        min_time = ft
                        min_idx = idx
                next_departure = min_time
            
            next_arrival_time = next_arrival
            
            if next_departure < next_arrival_time:
                # Departure event
                t = next_departure
                # Update integrals from last_event_time to t
                dt = t - last_event_time
                if last_event_time >= start_time_warmup:
                    L_area += current_n * dt
                    if current_n > 0:
                        busy_time += dt
                
                # Process departure
                # Remove the service that finished
                # We identified min_idx above, but indices shift if we remove.
                # Let's re-find and pop
                min_idx = -1
                min_time = float('inf')
                for idx, (ft, et) in enumerate(active_services):
                    if ft == t: # Floating point equality risk, better use <=
                        if ft <= t + 1e-9:
                            min_idx = idx
                            break
                if min_idx != -1:
                    ft, et = active_services.pop(min_idx)
                    current_n -= 1
                    # Record sojourn time if departure happened in window
                    if t >= start_time_warmup:
                        sojourn = t - et
                        total_sojourn += sojourn
                        dep_count += 1
                else:
                    # Should not happen
                    pass
                    
                last_event_time = t
                
            else:
                # Arrival event
                t = next_arrival_time
                # Update integrals
                dt = t - last_event_time
                if last_event_time >= start_time_warmup:
                    L_area += current_n * dt
                    if current_n > 0:
                        busy_time += dt
                
                # Process arrival
                if t >= start_time_warmup:
                    arr_count += 1
                
                if current_n < K:
                    # Enter system
                    current_n += 1
                    # Draw service time
                    serv_time = rng.expovariate(mu)
                    finish_t = t + serv_time
                    active_services.append((finish_t, t))
                    
                    # Schedule next arrival
                    next_arrival = t + rng.expovariate(lam)
                else:
                    # Blocked
                    if t >= start_time_warmup:
                        blk_count += 1
                    # Schedule next arrival
                    next_arrival = t + rng.expovariate(lam)
                
                last_event_time = t

        # Final update for integrals up to H
        dt = H - last_event_time
        if last_event_time >= start_time_warmup:
            L_area += current_n * dt
            if current_n > 0:
                busy_time += dt
        
        # Calculate metrics for this seed
        # Note: Variables like L_area, busy_time etc need to be initialized inside loop
        # I missed initialization in the thought process. Will fix in code.
        
        # Reset accumulators for next seed? No, they are local to loop iteration if defined there.
        # In the code structure below, I will define them inside the loop.
        
        # Metrics
        avg_L = L_area / win if win > 0 else 0
        avg_W_min = (total_sojourn / dep_count * 60) if dep_count > 0 else 0 # Convert hours to minutes
        avg_busy_frac = busy_time / win if win > 0 else 0
        avg_p_loss = blk_count / arr_count if arr_count > 0 else 0
        # p_wait: Probability of waiting? Or fraction of time someone waits?
        # Usually P(wait) in M/M/c is prob that arriving customer must wait.
        # Here, if n >= c, new arrival waits.
        # We didn't track this explicitly. 
        # Approximation: Fraction of arrivals that found n >= c?
        # Or fraction of time n >= c?
        # Let's compute fraction of arrivals that had to wait (i.e., entered when n >= c before entry? No, n is count BEFORE entry).
        # If n_before_entry >= c, then wait.
        # We need to track this.
        
        # Re-running logic mentally: I need to track wait_events.
        # Let's add `wait_count` to track arrivals where n >= c.
        
        # For now, assuming p_wait is estimated via utilization or similar? 
        # The prompt asks for p_wait. It's likely P(W>0).
        # In simulation: count arrivals where n >= c.
        
        # I will include these counters in the final code.
        
        results_L.append(avg_L)
        results_W.append(avg_W_min)
        results_busy_frac.append(avg_busy_frac)
        results_p_loss.append(avg_p_loss)
        # p_wait calculation needs data
        results_p_wait.append(0.0) # Placeholder, will implement properly
        
        results_arr.append(arr_count)
        results_blk.append(blk_count)
        results_dep.append(dep_count)

    # Aggregate across seeds
    seeds_used = len(results_L)
    mean_L = sum(results_L) / seeds_used
    mean_W = sum(results_W) / seeds_used
    mean_busy_frac = sum(results_busy_frac) / seeds_used
    mean_p_loss = sum(results_p_loss) / seeds_used
    mean_p_wait = sum(results_p_wait) / seeds_used
    
    total_arr = sum(results_arr)
    total_blk = sum(results_blk)
    total_dep = sum(results_dep)
    
    avg_arr_per_seed = total_arr / seeds_used
    avg_blk_per_seed = total_blk / seeds_used
    avg_dep_per_seed = total_dep / seeds_used
    
    # dep_rate: effective departure rate per hour
    # Total departures / Total time simulated (H * seeds)? 
    # Or average per seed? "dep_rate 是'个/每小时'的有效离开率"
    # Likely mean dep per seed / win? Or total dep / total sim time?
    # Let's use mean_dep_per_seed / win (hours)
    dep_rate = avg_dep_per_seed / win if win > 0 else 0
    
    # busy_util = E[min(N,c)]/c
    # We didn't track min(N,c) integral. 
    # busy_occupied = 1 - pi_0 = busy_frac (as defined in prompt: "站不空的时间比例")
    # Prompt says: "busy_frac 的定义：题目契约已点名 = 站不空的时间比例 1−π₀"
    # And "请另报 busy_util=E[min(N,c)]/c 与 busy_occupied=1−π₀"
    # So busy_occupied should be equal to busy_frac.
    # busy_util requires tracking sum(min(n,c)).
    
    # I need to go back and add tracking for busy_util and p_wait.
    
    # Refactoring plan for actual code:
    # Inside seed loop:
    # Initialize: L_area=0, busy_time=0, util_area=0, wait_count=0, arr_count=0, blk_count=0, dep_count=0, total_sojourn=0
    # On event transition:
    #   dt = t - last_event_time
    #   if last_event_time >= start_warmup:
    #       L_area += n * dt
    #       if n > 0: busy_time += dt
    #       util_area += min(n, c) * dt
    #   ...
    # On Arrival:
    #   if t >= start_warmup:
    #       arr_count += 1
    #       if n >= c: wait_count += 1
    #   ...
    
    # Then:
    # busy_util = util_area / (win * c)
    # p_wait = wait_count / arr_count
    
    # Let's write the full code now.

if __name__ == "__main__":
    main()
