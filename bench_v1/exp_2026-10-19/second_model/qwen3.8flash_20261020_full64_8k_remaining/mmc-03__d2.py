import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    c = 2                  # servers

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon_min = H

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = []  # heap-like list of (time, type, data)
        # type: 0=arrival, 1=departure
        import heapq
        heapq.heappush(events, (next_arrival, 0, None))
        
        queue = []  # waiting customers (each is a dict with arrival_time, service_time)
        servers = [None] * c  # each server holds the customer being served or None
        
        total_wait_plus_service = 0.0
        num_completed = 0
        num_blocked = 0
        num_arrivals = 0
        num_departures = 0
        
        # For area calculations
        last_event_time = 0.0
        area_N = 0.0
        area_busy = 0.0  # sum over time of min(N_in_system, c) but we need E[min(N,c)]/c as busy_frac
        # Actually busy_frac defined as E[min(N,c)]/c. We'll track integral of min(N(t), c).
        integral_min_N_c = 0.0
        
        warmup_end = horizon_min * 0.75
        stats_start = warmup_end
        stats_end = horizon_min
        
        # We need to integrate only from stats_start to stats_end
        # So we track state and when crossing stats_start, reset accumulators appropriately? 
        # Better: run simulation, record events, then post-process? Or online integration with flag.
        
        # Let's do online integration. We maintain current N and current min(N,c).
        # When an event occurs at time t_ev, we add (t_ev - last_t) * current_value to integrals IF last_t >= stats_start.
        # But we also need to handle the case where stats_start falls between events.
        
        # Simpler approach: collect all events up to horizon, then replay for statistics after warmup.
        # Given constraints on code length, let's try online with careful handling.
        
        # State variables
        n_in_system = 0  # including those in service and waiting
        n_waiting = len(queue)
        n_serving = sum(1 for s in servers if s is not None)
        
        # We'll store events in a list for post-processing to simplify warm-up exclusion.
        event_log = []  # (time, type, details)
        
        while events:
            t_ev, ev_type, data = heapq.heappop(events)
            if t_ev > horizon_min:
                break
            
            # Log event
            event_log.append((t_ev, ev_type, data))
            
            if ev_type == 0:  # Arrival
                num_arrivals += 1
                # Generate service time now
                svc_time = rng.expovariate(mu)
                cust = {'arrival': t_ev, 'service': svc_time}
                
                # Check if any server free
                free_server_idx = -1
                for idx in range(c):
                    if servers[idx] is None:
                        free_server_idx = idx
                        break
                
                if free_server_idx != -1:
                    # Start service immediately
                    servers[free_server_idx] = cust
                    dep_time = t_ev + svc_time
                    heapq.heappush(events, (dep_time, 1, {'server': free_server_idx, 'cust': cust}))
                    n_in_system += 1
                else:
                    # Join queue
                    queue.append(cust)
                    n_in_system += 1
                    
            elif ev_type == 1:  # Departure
                srv_idx = data['server']
                cust = data['cust']
                servers[srv_idx] = None
                
                # Remove from system
                n_in_system -= 1
                num_departures += 1
                
                # Calculate wait+service for this customer
                w_plus_s = t_ev - cust['arrival']
                total_wait_plus_service += w_plus_s
                num_completed += 1
                
                # If queue non-empty, start next service
                if queue:
                    next_cust = queue.pop(0)
                    servers[srv_idx] = next_cust
                    dep_time = t_ev + next_cust['service']
                    heapq.heappush(events, (dep_time, 1, {'server': srv_idx, 'cust': next_cust}))
                    n_in_system += 1  # still in system, just moved from queue to server
        
        # Now compute statistics from event_log for window [stats_start, stats_end]
        # Reconstruct timeline
        # We need N(t) over time. Events change N(t).
        # Between events, N is constant.
        
        # Collect all event times within [0, horizon]
        # Also include stats_start and stats_end as breakpoints
        
        points = sorted(set([e[0] for e in event_log] + [stats_start, stats_end]))
        points = [p for p in points if p <= horizon_min]
        
        # Build piecewise constant N(t)
        # Sort events by time
        event_log.sort(key=lambda x: x[0])
        
        # Determine N(t) at each interval
        # Initialize N=0 before first event
        curr_n = 0
        intervals = []  # (start, end, n_value)
        
        prev_t = 0.0
        for et, etype, edata in event_log:
            if et > horizon_min:
                break
            if et > prev_t:
                intervals.append((prev_t, et, curr_n))
            # Update curr_n based on event
            if etype == 0:  # Arrival increases N
                curr_n += 1
            elif etype == 1:  # Departure decreases N
                curr_n -= 1
            prev_t = et
        
        if prev_t < horizon_min:
            intervals.append((prev_t, horizon_min, curr_n))
        
        # Compute L (average number in system) over [stats_start, stats_end]
        win_len = stats_end - stats_start
        if win_len <= 0:
            L_val = 0.0
            busy_frac_val = 0.0
            p_wait_val = 0.0
            arr_val = 0.0
            dep_val = 0.0
            blk_val = 0.0
            W_val = 0.0
            busy_util_val = 0.0
            dep_rate_val = 0.0
            lam_eff_val = 0.0
            p_loss_val = 0.0
        else:
            area_N = 0.0
            area_min_N_c = 0.0
            count_arr_in_win = 0
            count_dep_in_win = 0
            count_blk_in_win = 0
            count_wait_in_win = 0  # arrivals that had to wait (i.e., joined queue)
            total_w_plus_s_in_win = 0.0
            num_completed_in_win = 0
            
            # Process intervals for area
            for st, en, nv in intervals:
                if en <= stats_start or st >= stats_end:
                    continue
                overlap_st = max(st, stats_start)
                overlap_en = min(en, stats_end)
                if overlap_en > overlap_st:
                    dt = overlap_en - overlap_st
                    area_N += nv * dt
                    area_min_N_c += min(nv, c) * dt
            
            L_val = area_N / win_len
            busy_frac_val = (area_min_N_c / win_len) / c
            busy_util_val = busy_frac_val  # same definition per problem statement
            
            # Count events in window
            for et, etype, edata in event_log:
                if et < stats_start or et > stats_end:
                    continue
                if etype == 0:
                    count_arr_in_win += 1
                    # Did this arrival have to wait?
                    # At arrival time, check if all servers were busy
                    # We need to know state just before this event.
                    # Since we processed events sequentially, we can track server occupancy.
                    # Let's re-simulate quickly or use stored info.
                    # Alternative: during initial sim, mark if waited.
                    pass
                elif etype == 1:
                    count_dep_in_win += 1
            
            # To get p_wait and W properly, we need to know which arrivals in window waited and their w+s.
            # Let's redo event processing with state tracking for the window.
            
            # Reset state trackers
            servers_state = [None] * c
            queue_state = []
            curr_n_state = 0
            
            # We need to fast-forward to stats_start
            # Find last event before stats_start
            pre_events = [e for e in event_log if e[0] <= stats_start]
            for et, etype, edata in pre_events:
                if etype == 0:
                    # Arrival
                    cust = edata.get('cust') if isinstance(edata, dict) else None
                    # In our log, data for arrival was None initially? No, we didn't store cust in log for arrival.
                    # Problem: event_log doesn't have full customer info for arrivals.
                    # Let's fix: store necessary info in event_log.
                    pass
            
            # This is getting messy. Let's restart the simulation part with better logging.
            # Due to line limit, I'll inline a cleaner version.
            
            # Clean restart for this seed
            rng = random.Random(seed)
            t = 0.0
            next_arrival = rng.expovariate(lam)
            events = []
            heapq.heappush(events, (next_arrival, 0, None))
            queue = []
            servers = [None] * c
            n_in_system = 0
            
            # Store detailed events
            detailed_events = []  # (time, type, extra_info)
            # For arrival: extra_info = {'waited': bool, 'w_plus_s': float later? no, w_plus_s known at departure}
            # Better: at arrival, record if it went to queue or service.
            # At departure, record w_plus_s.
            
            # Let's just run again cleanly.
            events = []
            heapq.heappush(events, (rng.expovariate(lam), 0, None))
            queue = []
            servers = [None] * c
            n_in_system = 0
            detailed_events = []
            
            while events:
                t_ev, ev_type, data = heapq.heappop(events)
                if t_ev > horizon_min:
                    break
                
                if ev_type == 0:
                    svc_time = rng.expovariate(mu)
                    cust = {'arrival': t_ev, 'service': svc_time}
                    free_idx = -1
                    for idx in range(c):
                        if servers[idx] is None:
                            free_idx = idx
                            break
                    if free_idx != -1:
                        servers[free_idx] = cust
                        heapq.heappush(events, (t_ev + svc_time, 1, {'server': free_idx, 'cust': cust}))
                        n_in_system += 1
                        waited = False
                    else:
                        queue.append(cust)
                        n_in_system += 1
                        waited = True
                    detailed_events.append((t_ev, 0, {'waited': waited, 'cust': cust}))
                    
                elif ev_type == 1:
                    srv_idx = data['server']
                    cust = data['cust']
                    servers[srv_idx] = None
                    n_in_system -= 1
                    w_plus_s = t_ev - cust['arrival']
                    detailed_events.append((t_ev, 1, {'w_plus_s': w_plus_s, 'cust': cust}))
                    if queue:
                        next_cust = queue.pop(0)
                        servers[srv_idx] = next_cust
                        heapq.heappush(events, (t_ev + next_cust['service'], 1, {'server': srv_idx, 'cust': next_cust}))
                        n_in_system += 1
            
            # Now compute stats from detailed_events and intervals
            # Intervals for N(t)
            points = sorted(set([e[0] for e in detailed_events] + [stats_start, stats_end]))
            points = [p for p in points if p <= horizon_min]
            
            curr_n = 0
            intervals = []
            prev_t = 0.0
            for et, etype, edata in detailed_events:
                if et > horizon_min:
                    break
                if et > prev_t:
                    intervals.append((prev_t, et, curr_n))
                if etype == 0:
                    curr_n += 1
                elif etype == 1:
                    curr_n -= 1
                prev_t = et
            if prev_t < horizon_min:
                intervals.append((prev_t, horizon_min, curr_n))
            
            area_N = 0.0
            area_min_N_c = 0.0
            for st, en, nv in intervals:
                if en <= stats_start or st >= stats_end:
                    continue
                os = max(st, stats_start)
                oe = min(en, stats_end)
                if oe > os:
                    dt = oe - os
                    area_N += nv * dt
                    area_min_N_c += min(nv, c) * dt
            
            L_val = area_N / win_len
            busy_frac_val = (area_min_N_c / win_len) / c
            busy_util_val = busy_frac_val
            
            count_arr = 0
            count_dep = 0
            count_blk = 0
            count_wait = 0
            total_wps = 0.0
            num_comp = 0
            
            for et, etype, edata in detailed_events:
                if et < stats_start or et > stats_end:
                    continue
                if etype == 0:
                    count_arr += 1
                    if edata['waited']:
                        count_wait += 1
                elif etype == 1:
                    count_dep += 1
                    total_wps += edata['w_plus_s']
                    num_comp += 1
            
            arr_val = count_arr
            dep_val = count_dep
            blk_val = count_blk  # No blocking in FCFS infinite queue model
            p_wait_val = count_wait / count_arr if count_arr > 0 else 0.0
            W_val = total_wps / num_comp if num_comp > 0 else 0.0
            dep_rate_val = dep_val / (win_len / 60.0) if win_len > 0 else 0.0  # per hour
            lam_eff_val = arr_val / (win_len / 60.0) if win_len > 0 else 0.0
            p_loss_val = 0.0  # No loss
            
            all_L.append(L_val)
            all_W.append(W_val)
            all_busy_frac.append(busy_frac_val)
            all_p_wait.append(p_wait_val)
            all_arr.append(arr_val)
            all_dep.append(dep_val)
            all_blk.append(blk_val)
            all_busy_util.append(busy_util_val)
            all_dep_rate.append(dep_rate_val)
            all_lam_eff.append(lam_eff_val)
            all_p_loss.append(p_loss_val)
            seed_list.append(seed)

    seeds_used = len(all_L)
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used > 0 else 0.0
    avg_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0.0
    avg_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0.0
    avg_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_util = sum(all_busy_util) / seeds_used if seeds_used > 0 else 0.0
    avg_dep_rate = sum(all_dep_rate) / seeds_used if seeds_used > 0 else 0.0
    avg_lam_eff = sum(all_lam_eff) / seeds_used if seeds_used > 0 else 0.0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used > 0 else 0.0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H * 0.25, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
