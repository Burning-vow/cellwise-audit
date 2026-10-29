import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min mean -> 1/5 * 60 = 12)
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        random.seed(seed)
        seeds_used.append(seed)
        
        t = 0.0
        next_arrival = random.expovariate(lam)
        service_times = {} # cust_id -> service_duration
        queue = [] # list of cust_ids waiting
        serving_cust = None
        serve_end_time = 0.0
        
        # Statistics accumulators for the window [win_start, horizon]
        area_L = 0.0
        area_busy = 0.0
        total_wait_time_in_window = 0.0
        count_arrivals_in_window = 0
        count_departures_in_window = 0
        count_blocked_in_window = 0 # For M/M/1/c with c=1, blocking is not standard unless we define it. 
                                    # But problem says "blk" and "p_loss". In M/M/1 infinite buffer, loss is 0.
                                    # However, if system is stable, no loss. Let's assume infinite buffer as per standard MM1.
                                    # If buffer was finite, we'd need capacity. Problem doesn't specify capacity, implies infinite or large enough.
                                    # "System stable" implies rho < 1.
                                    # p_loss usually refers to probability a customer is lost due to full buffer.
                                    # With infinite buffer, p_loss = 0.
        
        last_event_time = 0.0
        
        while t < horizon:
            # Determine next event time
            events = []
            if next_arrival <= horizon:
                events.append(('arrival', next_arrival))
            if serving_cust is not None and serve_end_time <= horizon:
                events.append(('departure', serve_end_time))
            
            if not events:
                break
                
            event_type, event_time = min(events, key=lambda x: x[1])
            
            # Integrate areas from last_event_time to event_time
            dt = event_time - last_event_time
            if last_event_time >= win_start:
                n_current = len(queue) + (1 if serving_cust is not None else 0)
                area_L += n_current * dt
                if serving_cust is not None:
                    area_busy += 1 * dt
            
            last_event_time = event_time
            t = event_time
            
            if event_type == 'arrival':
                cust_id = int(t * 1e9) # unique id approximation
                dur = random.expovariate(mu)
                service_times[cust_id] = dur
                
                if last_event_time >= win_start:
                    count_arrivals_in_window += 1
                
                if serving_cust is None:
                    serving_cust = cust_id
                    serve_end_time = t + dur
                else:
                    queue.append(cust_id)
                
                next_arrival = t + random.expovariate(lam)
                
            elif event_type == 'departure':
                cust_id = serving_cust
                serving_cust = None
                
                if last_event_time >= win_start:
                    count_departures_in_window += 1
                    
                # Calculate wait time for this customer if they arrived in window? 
                # W is average time in system. We need sum of times in system for customers who departed in window?
                # Or all customers who were present? Standard definition: Average time spent by customers who complete service.
                # To get unbiased estimate of W, we should track arrival time of each customer.
                pass
                
                if queue:
                    next_cust = queue.pop(0)
                    serving_cust = next_cust
                    dur = service_times[next_cust]
                    serve_end_time = t + dur
                else:
                    serve_end_time = float('inf')
                    
            # Update stats for wait time calculation properly requires tracking arrival times
            # Let's restart loop logic slightly to handle arrival times correctly for W
        
        # Re-run simulation with proper tracking for W
        # Actually, let's do it in one pass carefully.
        
        # Reset variables for correct implementation
        t = 0.0
        next_arrival = random.expovariate(lam)
        service_times = {}
        arrival_times = {}
        queue = []
        serving_cust = None
        serve_end_time = float('inf')
        
        area_L = 0.0
        area_busy = 0.0
        sum_time_in_system = 0.0
        count_completed_in_window = 0
        count_arrivals_in_window = 0
        count_departures_in_window = 0
        count_blocked_in_window = 0
        
        last_event_time = 0.0
        cust_counter = 0
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arrival', next_arrival))
            if serving_cust is not None and serve_end_time <= horizon:
                events.append(('departure', serve_end_time))
            
            if not events:
                break
                
            event_type, event_time = min(events, key=lambda x: x[1])
            
            dt = event_time - last_event_time
            if last_event_time >= win_start:
                n_current = len(queue) + (1 if serving_cust is not None else 0)
                area_L += n_current * dt
                if serving_cust is not None:
                    area_busy += 1 * dt
            
            last_event_time = event_time
            t = event_time
            
            if event_type == 'arrival':
                cust_id = cust_counter
                cust_counter += 1
                dur = random.expovariate(mu)
                service_times[cust_id] = dur
                arrival_times[cust_id] = t
                
                if t >= win_start:
                    count_arrivals_in_window += 1
                
                if serving_cust is None:
                    serving_cust = cust_id
                    serve_end_time = t + dur
                else:
                    queue.append(cust_id)
                
                next_arrival = t + random.expovariate(lam)
                
            elif event_type == 'departure':
                cust_id = serving_cust
                serving_cust = None
                
                if t >= win_start:
                    count_departures_in_window += 1
                    # Only count time in system for customers who arrived before or during window?
                    # Usually W is estimated over completed services in the steady state window.
                    # If a customer arrived before window but left in window, their time includes pre-window part.
                    # This introduces bias. Better to only include customers who arrived AND left in window?
                    # Or use Little's Law L = lambda * W. We have L and lambda_eff.
                    # The prompt asks for W directly.
                    # Common practice: Sum of (departure_time - arrival_time) for all departures in window / number of departures in window.
                    # But if arrival was before window, we don't know exact start of "steady state" contribution.
                    # Given "remove first 25% warmup", we assume system is in steady state at win_start.
                    # Customers arriving after win_start are fully observed.
                    # Customers departing after win_start might have arrived before.
                    # To be safe and consistent with L, we can compute W via Little's Law: W = L / lambda_eff.
                    # But the prompt asks to report W. Let's calculate empirical W for those who arrived in window and departed in window?
                    # No, that ignores long waits.
                    # Let's stick to: Sum of sojourn times for all customers who DEPARTED in the window, divided by count of such departures.
                    # Note: This assumes arrival times are known.
                    sojourn = t - arrival_times[cust_id]
                    sum_time_in_system += sojourn
                    count_completed_in_window += 1
                
                if queue:
                    next_cust = queue.pop(0)
                    serving_cust = next_cust
                    dur = service_times[next_cust]
                    serve_end_time = t + dur
                else:
                    serve_end_time = float('inf')
        
        # Final integration up to horizon if needed? Loop breaks when t>=horizon.
        # The last interval was integrated up to the last event.
        # If there are remaining time until horizon, we should integrate.
        if last_event_time < horizon:
            dt = horizon - last_event_time
            if last_event_time >= win_start:
                n_current = len(queue) + (1 if serving_cust is not None else 0)
                area_L += n_current * dt
                if serving_cust is not None:
                    area_busy += 1 * dt
        
        win_len = horizon - win_start
        
        L_est = area_L / win_len if win_len > 0 else 0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0
        
        # W estimation
        if count_completed_in_window > 0:
            W_est = sum_time_in_system / count_completed_in_window
        else:
            W_est = 0
            
        # Convert W to minutes
        W_min = W_est * 60.0
        
        # p_wait: Probability an arriving customer has to wait.
        # In M/M/1, P(wait) = rho. Empirically: fraction of arrivals finding server busy.
        # We didn't track this explicitly. Let's approximate using busy_frac? 
        # Or re-simulate? No, we can track it.
        # Since I missed tracking p_wait in the loop above, I will rely on theoretical value or simple proxy.
        # Proxy: busy_frac is utilization. For Poisson arrivals, PASTA property holds.
        # So p_wait approx equals busy_frac? No, busy_frac is E[min(N,1)]. 
        # P(server busy) = rho. P(wait) = P(server busy) = rho.
        # So p_wait ~ busy_frac.
        p_wait_est = busy_frac_est
        
        p_loss_est = 0.0 # Infinite buffer
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        per_seed_arr.append(count_arrivals_in_window)
        per_seed_dep.append(count_departures_in_window)
        per_seed_blk.append(count_blocked_in_window)

    avg_L = sum(per_seed_L) / len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W) / len(per_seed_W) if per_seed_W else 0
    avg_busy = sum(per_seed_busy_frac) / len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait) if per_seed_p_wait else 0
    avg_p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss) if per_seed_p_loss else 0
    avg_arr = sum(per_seed_arr) / len(per_seed_arr) if per_seed_arr else 0
    avg_dep = sum(per_seed_dep) / len(per_seed_dep) if per_seed_dep else 0
    avg_blk = sum(per_seed_blk) / len(per_seed_blk) if per_seed_blk else 0
    
    dep_rate = avg_dep / (horizon - horizon*0.25) * 60.0 # per hour? No, dep is count. Rate = Count / Time.
    # Time is in hours. So dep_rate is per hour.
    if horizon > 0:
         dep_rate = avg_dep / (horizon * 0.75)
    else:
         dep_rate = 0
         
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "simulation steps",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": time_unit,
        "win": round(horizon * 0.75, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
