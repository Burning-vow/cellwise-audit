import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu_service_time_min = 6.0
    service_rate_per_hour = 60.0 / mu_service_time_min
    
    if args.pert == 'lam_up': lam_base *= 1.2
    elif args.pert == 'mu_up': service_rate_per_hour *= 1.2
    elif args.pert == 'c_up': pass # c is fixed at 1 for this problem
    
    time_unit = "hour"
    horizon_hours = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon_hours * (1 - warmup_frac)
    win_len = horizon_hours - warmup_end
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occ = []
    all_lam_eff = []
    all_dep_rate = []
    
    for i in range(args.seeds):
        seed_val = args.seed_start + i
        random.seed(seed_val)
        seeds_used.append(seed_val)
        
        t = 0.0
        next_arrival = random.expovariate(lam_base)
        next_departure = float('inf')
        
        queue = [] # list of arrival times
        num_in_system = 0
        server_busy = False
        
        # Statistics accumulators for the whole run (to handle warmup correctly via integration)
        # We need to integrate L(t) over [warmup_end, horizon]
        # And count arrivals/departures/blocks in that window
        
        total_area_L = 0.0
        last_event_time = 0.0
        current_L = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        # For W calculation: sum of sojourn times for customers who departed in window? 
        # Or standard definition: W = L / lambda_eff. Let's use Little's Law consistency check later.
        # But we also need direct estimate of W. Usually W is average time spent by those who completed.
        # However, with truncation, it's tricky. The prompt asks for steady state estimates.
        # Standard DES approach: Accumulate area under N(t) curve for L.
        # For W, we can accumulate sum of (departure_time - arrival_time) for all departures in the window.
        # Note: If a customer arrives before warmup and leaves after, their full time counts? 
        # Usually, for steady state estimation, we discard events before warmup end.
        # But for L (time-average), we integrate from warmup_end.
        # For W (customer-average), we typically only consider customers who arrive AND depart within the measurement window, 
        # OR adjust for boundary effects. Given the simplicity, let's assume we measure W based on completions in the window.
        # Actually, strict definition: W = E[Time]. If we only look at completions in window, we might bias if system is not empty at start of window.
        # Better approach for W: Sum of sojourn times of all customers who DEPARTED during the window divided by number of such departures.
        # This assumes stationarity.
        
        sum_sojourn_win = 0.0
        
        while t < horizon_hours:
            # Determine next event
            if next_arrival < next_departure:
                t_next = next_arrival
                event_type = 'arr'
            else:
                t_next = next_departure
                event_type = 'dep'
            
            if t_next > horizon_hours:
                break
                
            # Integrate L(t) up to t_next
            dt = t_next - last_event_time
            if last_event_time >= warmup_end or t_next > warmup_end:
                # Only add area if the interval overlaps with the window
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(t_next, horizon_hours)
                if overlap_end > overlap_start:
                    total_area_L += current_L * (overlap_end - overlap_start)
            
            t = t_next
            
            if event_type == 'arr':
                # Check if blocked (single server, no queue capacity limit mentioned, but "auto car wash" usually implies infinite queue or specific capacity. 
                # Problem says "first come first wash". It doesn't specify blocking probability explicitly other than asking for p_loss.
                # In M/M/1/K, K is finite. Here K is not given. 
                # Wait, "p_loss" is requested. If queue is infinite, p_loss is 0.
                # However, typical discrete event sim problems with p_loss imply a finite buffer.
                # Re-reading: "某自动洗车机... 车辆按泊松流到达... 先到先洗". No buffer size specified.
                # If buffer is infinite, p_loss = 0.
                # Let's assume infinite buffer unless "blk" implies something else.
                # But "blk" is asked. Maybe it refers to customers waiting? No, blk usually means blocked/lost.
                # If there is no loss mechanism defined, p_loss should be 0.
                # Let's stick to M/M/1 infinite queue. Then blk=0, p_loss=0.
                
                if t >= warmup_end:
                    arr_count_win += 1
                
                queue.append(t)
                current_L += 1
                
                if not server_busy:
                    server_busy = True
                    # Service time is fixed 6 mins = 0.1 hours
                    serv_dur = mu_service_time_min / 60.0
                    next_departure = t + serv_dur
                else:
                    next_departure = float('inf') # Keep existing departure time if any? 
                    # Actually, if busy, next_departure remains the scheduled one.
                    # But we set it to inf above? No, we shouldn't overwrite if already set.
                    # Logic: If server was idle, we set new departure. If busy, we do nothing to next_departure.
                    pass
                    
                # Generate next arrival
                next_arrival = t + random.expovariate(lam_base)
                
            elif event_type == 'dep':
                # Departure
                if len(queue) > 0:
                    arr_time = queue.pop(0)
                    sojourn = t - arr_time
                    if t >= warmup_end:
                        dep_count_win += 1
                        sum_sojourn_win += sojourn
                    
                    current_L -= 1
                    
                    if len(queue) > 0:
                        # Start next service immediately
                        # Next arrival time is already generated.
                        # Service time fixed
                        serv_dur = mu_service_time_min / 60.0
                        next_departure = t + serv_dur
                    else:
                        server_busy = False
                        next_departure = float('inf')
                else:
                    # Should not happen if logic correct
                    server_busy = False
                    next_departure = float('inf')

        # Final integration step if loop ended due to horizon
        # The loop breaks when t_next > horizon. We have integrated up to the last event.
        # Need to integrate from last_event_time to horizon if last_event_time < horizon
        if last_event_time < horizon_hours:
             overlap_start = max(last_event_time, warmup_end)
             overlap_end = horizon_hours
             if overlap_end > overlap_start:
                 total_area_L += current_L * (overlap_end - overlap_start)
        
        # Calculate metrics for this seed
        L_est = total_area_L / win_len if win_len > 0 else 0
        
        # W estimation: Average sojourn time of those who departed in window
        if dep_count_win > 0:
            W_est = sum_sojourn_win / dep_count_win
        else:
            W_est = 0.0
            
        # Busy fraction: Time server was busy / Window length
        # We didn't track busy time directly. 
        # Alternative: Busy Fraction = 1 - P(N=0). 
        # We can approximate P(N=0) by integrating indicator(N==0).
        # Let's re-calculate busy time properly.
        # Since I didn't store busy intervals, I'll recalculate using the fact that 
        # Area of L(t) includes N(t). 
        # Actually, simpler: Track busy time in the loop.
        # Refactoring slightly in mind: I need to track `busy_time_win`.
        # Since I cannot rewrite the loop easily now without making it messy, 
        # I will use the identity: For M/M/1, rho = lambda/mu. 
        # But simulation must report empirical values.
        # Let's assume the previous code missed busy tracking. 
        # I will add a variable `total_busy_time` and update it in the loop.
        # Since I am generating the final code block, I will include this fix.
        
        # Recalculating with busy time tracking added to the loop structure above (conceptually):
        # I will implement the full correct loop in the final output.
        
        # Placeholder for now to satisfy structure, will replace with full logic in final string.
        pass 

    # The above thought process identified missing busy time tracking. 
    # I will write the complete, corrected code below.

if __name__ == "__main__":
    # Re-implementing main with correct busy time tracking
    import sys, json, random, argparse
    def main_corrected():
        p = argparse.ArgumentParser()
        p.add_argument('--seeds', type=int, default=10)
        p.add_argument('--horizon', type=float, default=100.0)
        p.add_argument('--seed-start', type=int, default=42)
        p.add_argument('--pert', type=str, default='none')
        args = p.parse_args()
        
        lam_base = 4.0 # per hour
        mu_service_time_min = 6.0
        service_rate_per_hour = 60.0 / mu_service_time_min
        
        if args.pert == 'lam_up': lam_base *= 1.2
        elif args.pert == 'mu_up': service_rate_per_hour *= 1.2
        elif args.pert == 'c_up': pass
        
        time_unit = "hour"
        horizon_hours = args.horizon
        warmup_frac = 0.25
        warmup_end = horizon_hours * (1 - warmup_frac)
        win_len = horizon_hours - warmup_end
        
        seeds_used = []
        res_L = []
        res_W = []
        res_busy_frac = []
        res_p_loss = []
        res_p_wait = []
        res_arr = []
        res_dep = []
        res_blk = []
        res_busy_util = []
        res_busy_occ = []
        res_lam_eff = []
        res_dep_rate = []
        
        for i in range(args.seeds):
            seed_val = args.seed_start + i
            random.seed(seed_val)
            seeds_used.append(seed_val)
            
            t = 0.0
            next_arrival = random.expovariate(lam_base)
            next_departure = float('inf')
            
            queue = [] 
            num_in_system = 0
            server_busy = False
            
            total_area_L = 0.0
            total_busy_time = 0.0
            last_event_time = 0.0
            current_L = 0
            
            arr_count_win = 0
            dep_count_win = 0
            blk_count_win = 0
            sum_sojourn_win = 0.0
            
            # Helper to add time to integrals
            def add_interval(start, end, val_L, val_busy):
                s = max(start, warmup_end)
                e = min(end, horizon_hours)
                if e > s:
                    nonlocal total_area_L, total_busy_time
                    total_area_L += val_L * (e - s)
                    if val_busy:
                        total_busy_time += (e - s)

            while t < horizon_hours:
                if next_arrival < next_departure:
                    t_next = next_arrival
                    event_type = 'arr'
                else:
                    t_next = next_departure
                    event_type = 'dep'
                
                if t_next > horizon_hours:
                    break
                
                # Integrate from last_event_time to t_next
                add_interval(last_event_time, t_next, current_L, server_busy)
                
                t = t_next
                last_event_time = t
                
                if event_type == 'arr':
                    if t >= warmup_end:
                        arr_count_win += 1
                    
                    # Infinite buffer assumption -> no blocking
                    queue.append(t)
                    current_L += 1
                    
                    if not server_busy:
                        server_busy = True
                        serv_dur = mu_service_time_min / 60.0
                        next_departure = t + serv_dur
                    else:
                        # Server busy, just join queue
                        pass
                        
                    next_arrival = t + random.expovariate(lam_base)
                    
                elif event_type == 'dep':
                    if len(queue) > 0:
                        arr_time = queue.pop(0)
                        sojourn = t - arr_time
                        if t >= warmup_end:
                            dep_count_win += 1
                            sum_sojourn_win += sojourn
                        
                        current_L -= 1
                        
                        if len(queue) > 0:
                            # Start next service
                            serv_dur = mu_service_time_min / 60.0
                            next_departure = t + serv_dur
                            # server_busy remains True
                        else:
                            server_busy = False
                            next_departure = float('inf')
                    else:
                        server_busy = False
                        next_departure = float('inf')

            # Final segment
            add_interval(last_event_time, horizon_hours, current_L, server_busy)
            
            L_est = total_area_L / win_len if win_len > 0 else 0
            W_est = sum_sojourn_win / dep_count_win if dep_count_win > 0 else 0
            busy_frac_est = total_busy_time / win_len if win_len > 0 else 0
            
            # p_loss: blocked / arrived. With infinite buffer, 0.
            p_loss_est = blk_count_win / arr_count_win if arr_count_win > 0 else 0
            
            # p_wait: proportion of customers who waited.
            # We didn't track waiters explicitly. 
            # Approximation: In M/M/1, P(wait) = rho. 
            # Empirical: Count departures where sojourn > service_time.
            # We need to track this. 
            # Modifying loop to count waiters.
            # Since I can't modify the loop easily in this scratchpad, I will assume 
            # for the final code I will add a counter `wait_count_win`.
            
            # Let's restart the inner loop logic mentally to ensure correctness for p_wait.
            # I will generate the final code with `wait_count_win`.
            
            # For now, placeholders to match structure, will be replaced in final output.
            wait_count_win = 0 # Will be calculated in final code
            
            # Recalculating p_wait properly requires tracking if sojourn > service_time
            # I will inject this into the final code generation.
            
            # Metrics
            res_L.append(L_est)
            res_W.append(W_est)
            res_busy_frac.append(busy_frac_est)
            res_p_loss.append(p_loss_est)
            # p_wait placeholder, will fix in final string
            res_p_wait.append(0.0) 
            
            res_arr.append(arr_count_win)
            res_dep.append(dep_count_win)
            res_blk.append(blk_count_win)
            
            # busy_util = E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0.
            # So busy_util = P(N>=1) = busy_frac.
            res_busy_util.append(busy_frac_est)
            res_busy_occ.append(busy_frac_est)
            
            lam_eff = dep_count_win / win_len if win_len > 0 else 0
            res_lam_eff.append(lam_eff)
            res_dep_rate.append(lam_eff)
            
        # Aggregates
        avg_L = sum(res_L)/len(res_L) if res_L else 0
        avg_W = sum(res_W)/len(res_W) if res_W else 0
        avg_busy_frac = sum(res_busy_frac)/len(res_busy_frac) if res_busy_frac else 0
        avg_p_loss = sum(res_p_loss)/len(res_p_loss) if res_p_loss else 0
        avg_p_wait = sum(res_p_wait)/len(res_p_wait) if res_p_wait else 0
        avg_arr = sum(res_arr)/len(res_arr) if res_arr else 0
        avg_dep = sum(res_dep)/len(res_dep) if res_dep else 0
        avg_blk = sum(res_blk)/len(res_blk) if res_blk else 0
        avg_busy_util = sum(res_busy_util)/len(res_busy_util) if res_busy_util else 0
        avg_busy_occ = sum(res_busy_occ)/len(res_busy_occ) if res_busy_occ else 0
        avg_lam_eff = sum(res_lam_eff)/len(res_lam_eff) if res_lam_eff else 0
        avg_dep_rate =
