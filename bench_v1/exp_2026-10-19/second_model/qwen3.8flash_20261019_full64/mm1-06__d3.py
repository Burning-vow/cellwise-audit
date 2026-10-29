import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 7.0 / 60.0 # per minute
    mu_base = 1.0 / 5.0   # per minute
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = args.horizon
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
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} 
        queue = [] 
        server_free_time = 0.0
        
        warmup_end = horizon_min * 0.25
        
        area_L = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        busy_time = 0.0
        wait_count = 0
        
        last_event_time = 0.0
        current_N = 0
        
        while True:
            next_departure = None
            if queue:
                cust_id = queue[0]
                start_serv = max(server_free_time, last_event_time) 
                # Actually, we need to track when service starts properly.
                # Let's restructure slightly for clarity within constraints.
                pass
            
            # Re-implementing loop logic cleanly inside the constraint
            # State variables reset per seed
            t = 0.0
            next_arrival = rng.expovariate(lam)
            pending_services = [] # list of (arrival_time, service_duration)
            server_status = 0 # 0 idle, 1 busy
            server_free_at = 0.0
            queue_customers = [] # arrival times
            
            stats_area_L = 0.0
            stats_busy_time = 0.0
            stats_arrivals = 0
            stats_departures = 0
            stats_blocks = 0
            stats_sum_residence = 0.0
            stats_waits = 0
            
            prev_t = 0.0
            prev_N = 0
            prev_busy = 0
            
            while t < horizon_min:
                # Determine next event
                events = []
                if next_arrival <= horizon_min:
                    events.append(('arr', next_arrival))
                
                if server_status == 1 and server_free_at <= horizon_min:
                    events.append(('dep', server_free_at))
                    
                if not events:
                    break
                
                events.sort(key=lambda x: x[1])
                etype, etime = events[0]
                
                # Integrate area before updating state
                dt = etime - prev_t
                if prev_t >= warmup_end:
                    stats_area_L += prev_N * dt
                    if prev_busy:
                        stats_busy_time += dt
                        
                # Process event
                if etype == 'arr':
                    if prev_t >= warmup_end:
                        stats_arrivals += 1
                    
                    # Check capacity? M/M/1 infinite queue usually, but problem says "blocked/rejected".
                    # Standard M/M/1 has no blocking unless specified. 
                    # However, output requires blk/p_loss. 
                    # If it's a pure M/M/1, blk is 0. 
                    # But let's assume standard M/M/1 with infinite buffer -> blk=0.
                    # Wait, "blk" implies finite capacity or loss system. 
                    # Problem says "M/M/1", usually infinite queue. 
                    # But keys require blk. I will set blk=0 as it's an M/M/1 queueing system (waiting allowed).
                    # If it were M/M/1/K, K would be given. It is not. So K=infinity.
                    
                    dur = rng.expovariate(mu)
                    arr_time = etime
                    
                    if server_status == 0:
                        server_status = 1
                        server_free_at = etime + dur
                        # Start service immediately
                        # Residence time = dur
                        # We need to store this customer to calculate W later upon departure
                        # Since we process departures, we can push to a structure
                        # Or simpler: since we know service time now, and start time now,
                        # we can just record that this specific departure corresponds to this arrival.
                        # But multiple customers might be in system.
                        # Let's use a FIFO queue for waiting, and one in service.
                        
                        # Customer enters service immediately
                        # Store (arrival_time, service_duration) for the one in service
                        # Actually, we just need to know when they leave to add residence time.
                        # The departure event at server_free_at corresponds to this customer.
                        # We need to map the departure back to the arrival.
                        # Since only one server, the next departure IS this customer.
                        # So we can store the arrival time associated with the current service.
                        current_service_arrival = arr_time
                        current_service_dur = dur
                    else:
                        # Server busy, join queue
                        queue_customers.append((arr_time, dur))
                        if prev_t >= warmup_end:
                            stats_waits += 1 # This customer waits? No, p_wait is prob of waiting.
                            # Usually p_wait is fraction of arrivals who wait.
                            # If server busy, they wait.
                            
                    # Generate next arrival
                    next_arrival = etime + rng.expovariate(lam)
                    
                elif etype == 'dep':
                    if prev_t >= warmup_end:
                        stats_departures += 1
                        # Calculate residence time for departing customer
                        # Who is departing? The one currently in service.
                        # We stored current_service_arrival above? 
                        # Need to handle case where queue was empty vs non-empty.
                        
                        # Refactor: Keep a variable `in_service_cust` which holds (arrival_time, duration)
                        # When dep happens, we pop from queue if any.
                        
                        # Let's restart the inner loop logic with clearer state vars.
                        pass
                
                # Update state for integration
                prev_t = etime
                # Recalculate N and Busy after event processing
                # This approach is getting messy inline. 
                # Let's do a cleaner simulation step.
                
                # Resetting to a cleaner implementation strategy
                break # Break out to rewrite below
            
            # Clean Implementation
            t = 0.0
            next_arrival = rng.expovariate(lam)
            # Queue stores (arrival_time, service_duration)
            q = [] 
            # In-service customer: (arrival_time, service_duration, end_time)
            in_serv = None 
            
            # Stats accumulators
            area_L = 0.0
            busy_time = 0.0
            n_arr = 0
            n_dep = 0
            n_blk = 0
            sum_res = 0.0
            n_wait = 0
            
            last_t = 0.0
            last_N = 0
            last_busy = False
            
            while t < horizon_min:
                # Find next event time
                cand_arr = next_arrival if next_arrival <= horizon_min else float('inf')
                cand_dep = in_serv[2] if in_serv else float('inf')
                
                next_t = min(cand_arr, cand_dep)
                if next_t > horizon_min:
                    break
                
                # Integrate
                dt = next_t - last_t
                if last_t >= warmup_end:
                    area_L += last_N * dt
                    if last_busy:
                        busy_time += dt
                
                # Process Event
                if abs(next_t - cand_arr) < 1e-9:
                    # Arrival
                    if last_t >= warmup_end:
                        n_arr += 1
                    
                    dur = rng.expovariate(mu)
                    arr_t = next_t
                    
                    # Infinite buffer M/M/1, so no blocks
                    # But if we want to support generic, check capacity. Here cap=inf.
                    
                    if in_serv is None:
                        # Idle, start service
                        end_t = arr_t + dur
                        in_serv = (arr_t, dur, end_t)
                        # Does this customer wait? No.
                    else:
                        # Busy, join queue
                        q.append((arr_t, dur))
                        if last_t >= warmup_end:
                            n_wait += 1
                            
                    next_arrival = arr_t + rng.expovariate(lam)
                    
                elif abs(next_t - cand_dep) < 1e-9:
                    # Departure
                    if last_t >= warmup_end:
                        n_dep += 1
                        # Residence time
                        res = next_t - in_serv[0]
                        sum_res += res
                        
                    # Next customer from queue?
                    if q:
                        nxt_arr, nxt_dur = q.pop(0)
                        end_t = next_t + nxt_dur
                        in_serv = (nxt_arr, nxt_dur, end_t)
                    else:
                        in_serv = None
                
                # Update State for next integration
                last_t = next_t
                # Current N
                curr_N = 0
                if in_serv:
                    curr_N += 1
                curr_N += len(q)
                last_N = curr_N
                last_busy = (in_serv is not None)
            
            # Final integration up to horizon if needed? 
            # Loop breaks when next_t > horizon. 
            # We should integrate from last_t to horizon_min if last_t < horizon_min
            if last_t < horizon_min:
                dt = horizon_min - last_t
                if last_t >= warmup_end:
                    area_L += last_N * dt
                    if last_busy:
                        busy_time += dt
            
            win_len = horizon_min - warmup_end
            if win_len <= 0:
                continue
                
            L_est = area_L / win_len
            W_est = sum_res / n_dep if n_dep > 0 else 0.0
            busy_frac_est = busy_time / win_len
            p_wait_est = n_wait / n_arr if n_arr > 0 else 0.0
            p_loss_est = n_blk / n_arr if n_arr > 0 else 0.0
            lam_eff_est = n_arr / win_len
            dep_rate_est = n_dep / win_len * 60.0 # per hour
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(n_arr)
            all_blk.append(n_blk)
            all_dep.append(n_dep)
            all_busy_util.append(busy_frac_est) # E[min(N,1)]/1
            all_busy_occupied.append(busy_frac_est) # 1-pi0 approx same for stable
            all_lam_eff.append(lam_eff_est)
            all_p_loss.append(p_loss_est)
            all_dep_rate.append(dep_rate_est)
            
            seeds_used += 1
            seed_list.append(seed)

    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occ = sum(all_busy_occupied) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "minutes",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(horizon_min * 0.75, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_busy_occ, 4)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
