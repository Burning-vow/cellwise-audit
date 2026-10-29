import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 7.0 # per hour
    mu_base = 10.0 # per hour (6 min mean)
    
    if args.pert == 'lam_up': lam = lam_base * 1.1
    elif args.pert == 'mu_up': mu = mu_base * 1.1
    elif args.pert == 'c_up': c = 2
    else: 
        lam = lam_base
        mu = mu_base
        c = 1
    
    if args.pert == 'c_up': c = 2
    else: c = 1

    horizon = args.horizon
    time_unit = 'hour'
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocked = 0
    total_wait_events = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} # id -> duration
        queue = [] # list of customer ids waiting
        serving_id = None
        serve_end_time = float('inf')
        cust_count = 0
        
        last_event_time = 0.0
        current_n = 0
        
        # State variables for integration
        area_L = 0.0
        busy_time = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        wait_cnt = 0
        w_sum = 0.0
        
        while t < horizon:
            # Determine next event
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if serving_id is not None and serve_end_time <= horizon:
                events.append(('dep', serve_end_time))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - t
            if dt > 0:
                # Integrate before state change
                if t >= win_start:
                    area_L += current_n * dt
                    if current_n > 0:
                        busy_time += dt
                
                t = etime
            
            if etype == 'arr':
                cid = cust_count
                cust_count += 1
                st = rng.expovariate(mu)
                service_times[cid] = st
                
                if len(queue) + (1 if serving_id is not None else 0) < c:
                    if serving_id is None:
                        serving_id = cid
                        serve_end_time = t + st
                        current_n += 1
                    else:
                        queue.append(cid)
                        current_n += 1
                    if t >= win_start:
                        arr_cnt += 1
                else:
                    if t >= win_start:
                        blk_cnt += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'dep':
                cid = serving_id
                if t >= win_start:
                    dep_cnt += 1
                    w = t - (serve_end_time - service_times[cid]) # Arrival time approx? No, need arrival time stored.
                    # Correction: We didn't store arrival time. Let's fix logic.
                    # Actually, we can compute W from L and lambda_eff later, or track it properly.
                    # To track W properly, we need arrival time.
                    pass 
                
                # Remove served customer
                serving_id = None
                current_n -= 1
                
                if queue:
                    next_cid = queue.pop(0)
                    serving_id = next_cid
                    serve_end_time = t + service_times[next_cid]
                    current_n += 1 # Wait, N decreases by 1 then increases by 1? Net 0 change in system size?
                    # No, the departing one leaves, the queued one starts service. System size stays same if queue was non-empty.
                    # But my current_n tracking above was flawed.
                    # Let's restart simulation loop with better state tracking.
                    
        # The previous loop had issues with tracking arrival times for W calculation directly.
        # Let's rewrite the inner loop cleanly.
        
        # Reset for this seed
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {}
        arrival_times = {}
        queue = []
        serving_id = None
        serve_end_time = float('inf')
        cust_count = 0
        current_n = 0
        
        area_L = 0.0
        busy_time = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        w_sum = 0.0
        wait_cnt = 0 # Customers who waited (queue length > 0 at arrival)
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append(('arr', next_arrival))
            if serving_id is not None and serve_end_time <= horizon:
                events.append(('dep', serve_end_time))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - t
            if dt > 0:
                if t >= win_start:
                    area_L += current_n * dt
                    if current_n > 0:
                        busy_time += dt
                t = etime
            
            if etype == 'arr':
                cid = cust_count
                cust_count += 1
                st = rng.expovariate(mu)
                service_times[cid] = st
                arrival_times[cid] = t
                
                # Check capacity
                # System has serving_id (if any) + queue
                sys_size = (1 if serving_id is not None else 0) + len(queue)
                
                if sys_size < c:
                    if serving_id is None:
                        serving_id = cid
                        serve_end_time = t + st
                        current_n += 1
                    else:
                        queue.append(cid)
                        current_n += 1
                    
                    if t >= win_start:
                        arr_cnt += 1
                        # Did they wait? If queue was not empty OR server was busy?
                        # In M/M/1, if server busy, they join queue. They wait.
                        # If server idle, they start immediately. They don't wait.
                        # "Wait" usually means time in queue > 0.
                        if serving_id != cid: # It was added to queue or started service but was there a wait?
                            # If it started service immediately, wait=0.
                            # If it joined queue, wait>0.
                            # How to know? If queue was non-empty before adding, or if server was busy?
                            # If server was busy, new customer goes to queue.
                            # If server was idle, new customer goes to service.
                            # So if serving_id was NOT None before this arrival, they waited.
                            # But we just changed serving_id.
                            # Let's check pre-state.
                            pass
                        # Better: Calculate W for each departure.
                        
                else:
                    if t >= win_start:
                        blk_cnt += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'dep':
                cid = serving_id
                if t >= win_start:
                    dep_cnt += 1
                    w = t - arrival_times[cid]
                    w_sum += w
                    # Was there a wait?
                    # If arrival time < start of service time.
                    # Start of service time = serve_end_time - service_times[cid]
                    start_serv = serve_end_time - service_times[cid]
                    if start_serv > arrival_times[cid]:
                        wait_cnt += 1
                
                serving_id = None
                current_n -= 1
                
                if queue:
                    next_cid = queue.pop(0)
                    serving_id = next_cid
                    serve_end_time = t + service_times[next_cid]
                    current_n += 1
        
        # End of seed loop
        if win_len > 0:
            l_est = area_L / win_len
            w_est = w_sum / dep_cnt if dep_cnt > 0 else 0
            bf_est = busy_time / win_len
            pl_est = blk_cnt / (arr_cnt + blk_cnt) if (arr_cnt + blk_cnt) > 0 else 0
            pw_est = wait_cnt / dep_cnt if dep_cnt > 0 else 0
            
            per_seed_L.append(l_est)
            per_seed_W.append(w_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(pl_est)
            per_seed_p_wait.append(pw_est)
            
            total_L_area += area_L
            total_W_sum += w_sum
            total_busy_time += busy_time
            total_arrivals += arr_cnt
            total_departures += dep_cnt
            total_blocked += blk_cnt
            total_wait_events += wait_cnt

    avg_L = total_L_area / (win_len * seeds_used) if seeds_used > 0 else 0
    avg_W = total_W_sum / total_departures if total_departures > 0 else 0
    avg_busy_frac = total_busy_time / (win_len * seeds_used) if seeds_used > 0 else 0
    avg_p_loss = total_blocked / (total_arrivals + total_blocked) if (total_arrivals + total_blocked) > 0 else 0
    avg_p_wait = total_wait_events / total_departures if total_departures > 0 else 0
    
    dep_rate = total_departures / (win_len * seeds_used) * 60.0 # per hour? No, time_unit is hour.
    # dep_rate is "个/每小时". Since time_unit is hour, rate is count/hour.
    dep_rate_val = total_departures / (win_len * seeds_used) if seeds_used > 0 else 0
    
    lam_eff = dep_rate_val
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W * 60, 4), # Convert hours to minutes
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(total_arrivals / seeds_used, 4) if seeds_used > 0 else 0,
        "blk": round(total_blocked / seeds_used, 4) if seeds_used > 0 else 0,
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(total_departures / seeds_used, 4) if seeds_used > 0 else 0,
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
