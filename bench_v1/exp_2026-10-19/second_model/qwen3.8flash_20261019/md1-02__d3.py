import sys, json, random
def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu_base = 12.0 # per hour (5 min service)
    c = 1
    
    if args.pert == 'lam_up': lam_base *= 1.1
    elif args.pert == 'mu_up': mu_base *= 1.1
    elif args.pert == 'c_up': pass # c is fixed at 1 for this problem structure usually, but pert might imply capacity change? Problem says "automatic car wash machine", singular. c=1. If c_up, maybe c=2? But prompt says "perturbation only changes parameters not structure". Let's assume c stays 1 unless specified otherwise in a more complex model. Here c=1.
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arr_time = rng.expovariate(lam_base)
        next_dep_time = float('inf')
        
        # Statistics accumulators for the whole run (to handle warmup correctly by integrating area)
        # We need to integrate N(t) over [win_start, horizon]
        # And count arrivals/departures/blocks in that window
        
        last_event_time = 0.0
        current_N = 0
        
        # Accumulators for the statistical window
        area_N_window = 0.0
        arr_count_window = 0
        dep_count_window = 0
        blk_count_window = 0
        wait_time_sum_window = 0.0 # Sum of waiting times for customers who departed in window? 
        # W is average time in system. Usually calculated as Total Time in System / Number of Departures.
        # Or via Little's Law L = lambda_eff * W.
        # The prompt asks for W directly. Standard DES approach: track sojourn time for each customer.
        # However, we must only accumulate stats in the window.
        # A customer arriving before window start and leaving after contributes partial time?
        # Usually, for steady state estimation with warmup, we discard events before warmup end.
        # For area integrals, we integrate from win_start.
        # For counts, we count events occurring in [win_start, horizon].
        # For W, it's tricky. Common practice: sum of (departure_time - arrival_time) for all customers who DEPARTED in the window.
        # This ignores customers still in system at horizon.
        
        # Let's stick to:
        # L = Area(N) / Window_Length
        # W = Sum(Sojourn Times of Customers Departing in Window) / Count(Departures in Window)
        # busy_frac = Area(Indicator(N>0)) / Window_Length
        
        area_busy_window = 0.0
        
        # To compute Sojourn Time, we need to store arrival time for customers currently in system.
        # Since c=1, max queue length can be large, but we just need to know when the one being served arrived.
        # Actually, FCFS. We need a queue of arrival times.
        queue = [] # List of arrival times of cars waiting or being served
        
        while t < horizon:
            # Determine next event
            if next_arr_time <= next_dep_time:
                t_next = next_arr_time
                event_type = 'arr'
            else:
                t_next = next_dep_time
                event_type = 'dep'
            
            if t_next > horizon:
                break
                
            # Integrate areas up to t_next
            dt = t_next - last_event_time
            
            # Check if integration interval overlaps with window
            # Interval is [last_event_time, t_next]
            # Window is [win_start, horizon]
            
            overlap_start = max(last_event_time, win_start)
            overlap_end = min(t_next, horizon)
            
            if overlap_start < overlap_end:
                overlap_dt = overlap_end - overlap_start
                area_N_window += current_N * overlap_dt
                if current_N > 0:
                    area_busy_window += overlap_dt
            
            # Process Event
            if event_type == 'arr':
                # Generate new interarrival
                next_arr_time = t_next + rng.expovariate(lam_base)
                
                # Check if within window for counting
                if t_next >= win_start:
                    arr_count_window += 1
                
                # Add to queue
                queue.append(t_next)
                
                # Update N
                old_N = current_N
                current_N += 1
                
                # If server was idle, start service
                if old_N == 0:
                    # Service time is fixed 5 mins = 5/60 hours
                    serv_time = 5.0 / 60.0
                    next_dep_time = t_next + serv_time
                else:
                    # Server busy, do nothing to next_dep_time
                    pass
                    
            elif event_type == 'dep':
                # Customer leaves
                # Who left? The head of the queue
                if queue:
                    arr_time_left = queue.pop(0)
                    
                    # Calculate sojourn time
                    sojourn = t_next - arr_time_left
                    
                    # Count departure if in window
                    if t_next >= win_start:
                        dep_count_window += 1
                        wait_time_sum_window += sojourn
                        
                    # Update N
                    old_N = current_N
                    current_N -= 1
                    
                    # Start next service if any
                    if current_N > 0:
                        serv_time = 5.0 / 60.0
                        next_dep_time = t_next + serv_time
                    else:
                        next_dep_time = float('inf')
                else:
                    # Should not happen if logic is correct
                    next_dep_time = float('inf')
            
            last_event_time = t_next
            t = t_next

        # Final integration step if loop broke due to horizon
        # The loop breaks if t_next > horizon. We need to integrate from last_event_time to horizon
        dt_final = horizon - last_event_time
        if dt_final > 0:
            overlap_start = max(last_event_time, win_start)
            overlap_end = horizon
            if overlap_start < overlap_end:
                overlap_dt = overlap_end - overlap_start
                area_N_window += current_N * overlap_dt
                if current_N > 0:
                    area_busy_window += overlap_dt

        # Compute metrics for this seed
        L_est = area_N_window / win_len if win_len > 0 else 0.0
        W_est = wait_time_sum_window / dep_count_window if dep_count_window > 0 else 0.0
        busy_frac_est = area_busy_window / win_len if win_len > 0 else 0.0
        
        # p_loss: In this model (infinite buffer), loss is 0. 
        # But prompt mentions blk. If buffer is infinite, blk=0.
        # "Automatic car wash" usually implies single lane, infinite queue? 
        # Prompt doesn't specify blocking. Standard M/M/1 has no blocking.
        # I will assume infinite buffer, so blk=0, p_loss=0.
        blk_count_window = 0 
        p_loss_est = 0.0
        
        p_wait_est = 0.0
        # Probability of waiting: Fraction of arrivals that found server busy?
        # Or fraction of departures that had wait > 0?
        # Usually P(wait) = rho for M/M/1.
        # Empirical: Count arrivals where queue was non-empty upon arrival?
        # We didn't track that specifically in the window accumulation above.
        # Let's approximate using L and W? No.
        # Let's re-run logic mentally: 
        # When an arrival happens, if current_N > 0 (before increment), they wait.
        # We need to count such arrivals in the window.
        # I missed tracking `wait_arrivals`.
        # Given the constraint on code length and complexity, and that M/M/1 P(wait)=rho,
        # I can estimate rho = L/W/lam_eff? Or just use busy_frac as proxy for utilization.
        # Strictly, P(wait) is prob an arriving customer waits.
        # For Poisson arrivals, PASTA property holds. P(wait) = P(system non-empty) = busy_frac.
        # So p_wait_est = busy_frac_est.
        
        p_wait_est = busy_frac_est
        
        # Other metrics
        arr_rate = arr_count_window / win_len
        dep_rate = dep_count_window / win_len
        lam_eff = dep_rate # Conservation of flow in stable system
        
        busy_util = busy_frac_est # E[min(N,c)]/c = E[N]/1 = L? No.
        # Busy Utilization U = E[min(N,c)]/c. For c=1, U = P(N>=1) = busy_frac.
        # Wait, definition: "busy_frac ... = E[min(N,1)]/1". Yes.
        # "busy_util=E[min(N,c)]/c". Same thing here.
        # "busy_occupied=1-pi0". pi0 = P(N=0). 1-pi0 = P(N>0) = busy_frac.
        # So all three are equal in this specific case.
        
        busy_util_est = busy_frac_est
        busy_occupied_est = busy_frac_est
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count_window)
        all_dep.append(dep_count_window)
        all_blk.append(blk_count_window)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occupied_est)

    # Aggregate results
    avg_L = sum(all_L) / len(all_L)
    avg_W = sum(all_W) / len(all_W)
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac)
    avg_p_loss = sum(all_p_loss) / len(all_p_loss)
    avg_p_wait = sum(all_p_wait) / len(all_p_wait)
    
    avg_arr_per_seed = sum(all_arr) / len(all_arr)
    avg_dep_per_seed = sum(all_dep) / len(all_dep)
    avg_blk_per_seed = sum(all_blk) / len(all_blk)
    
    avg_busy_util = sum(all_busy_util) / len(all_busy_util)
    avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied)
    
    # Dep rate in per hour
    # dep_count_window is total departures in window.
    # Rate = dep_count / win_len.
    # We averaged counts per seed. Need to convert to rate.
    # avg_dep_per_seed is count. Divide by win_len to get rate.
    dep_rate_val = avg_dep_per_seed / win_len if win_len > 0 else 0.0
    lam_eff_val = dep_rate_val
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr_per_seed, 4),
        "blk": round(avg_blk_per_seed, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep_per_seed, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff_val, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_busy_occupied, 4)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
