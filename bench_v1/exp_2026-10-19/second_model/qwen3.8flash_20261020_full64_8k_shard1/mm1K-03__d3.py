import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # hours
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    lam_base = 8.0 # per hour
    mu_base = 10.0 # per hour (6 min mean -> 1/0.1 hr)
    c = 1
    K = 4 # capacity including service

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
    
    if pert != 'c_up' and pert != 'none':
         pass # keep base c,K unless c_up

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_p_wait = []
    all_busy_util = []
    all_busy_occupied = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        queue = [] # list of dicts {arrival_time, service_time}
        server_free_time = 0.0
        
        # State variables for integration
        last_event_time = 0.0
        current_N = 0 # number in system (queue + service)
        is_server_busy = False
        
        # Accumulators for the whole run (before warmup removal logic applied to stats)
        # We need to track events to compute area integrals correctly.
        # Instead of storing all events, we integrate on the fly.
        
        total_area_N = 0.0
        total_time_busy = 0.0
        total_time_nonempty = 0.0 # For busy_frac = 1 - pi_0, i.e., time N > 0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_waiting_times = 0.0 # Sum of W_i for completed services
        count_completed_services = 0
        sum_wait_in_queue_times = 0.0 # Time spent waiting before service starts
        count_waited = 0 # Number who waited > 0
        
        # Warmup handling: 
        # Requirement: Stats only in window after removing first 25% warmup.
        # Horizon H is total simulation time. Warmup ends at 0.25 * H.
        # We need to reset accumulators or subtract pre-warmup contributions.
        # Easier approach: Run simulation, record event times and states, then filter?
        # Or: Integrate from start, but also integrate from 0 to warmup_end separately?
        # Let's use a flag. When t crosses warmup_end, we snapshot current accumulated values 
        # and subtract them from final totals? No, that's tricky for counts.
        # Better: Only accumulate stats AFTER warmup_end.
        # But we must simulate through warmup to get correct state at warmup_end.
        
        warmup_end = 0.25 * H
        
        # To handle "area type quantities must be integrated before changing state":
        # We maintain `last_event_time`. At each event, we add `(t - last_event_time) * value` to areas.
        # If `last_event_time < warmup_end` and `t > warmup_end`, we split the interval.
        
        def add_area_and_counts(t_curr, t_prev, n_val, busy_val, nonempty_val):
            # This helper is complex due to splitting. 
            # Let's do it inline in the loop.
            pass

        # Simulation Loop
        while True:
            # Determine next event time
            next_departure = float('inf')
            if queue:
                # The head of queue is being served? 
                # Our model: queue[0] is currently in service if server is busy.
                # Actually, let's manage server explicitly.
                # If server is busy, next departure is when current service finishes.
                # Who is in service? The one at front of queue?
                # Let's say: queue holds people WAITING. A separate variable tracks person IN SERVICE.
                # But problem says "waiting room + doctor room".
                # Let's stick to: 
                # `in_service`: dict or None.
                # `waiting_queue`: list of dicts.
                
                # Correction: Simpler M/M/1/K model.
                # System state: N customers.
                # Server status: Busy or Idle.
                # If Busy, there is a customer in service with remaining time.
                # If not Busy, no one in service.
                # Waiting customers are in a FIFO queue.
                
                # Let's refactor state:
                # `server_customer`: None or {'start_time': ..., 'service_time': ...}
                # `wait_queue`: list of {'arrival_time': ...}
                
                # Next departure time:
                if server_customer:
                    next_departure = server_customer['end_time']
            
            next_event = min(next_arrival, next_departure, H)
            
            if next_event >= H:
                break
            
            # Process time passage up to next_event
            dt = next_event - t
            
            # Update integrals
            # Area of N: N * dt
            # Area of Busy: 1 * dt if server busy else 0
            # Area of NonEmpty: 1 * dt if N > 0 else 0
            
            # Check if this interval overlaps with warmup period
            # We want stats ONLY for [warmup_end, H].
            # So we only add to accumulators if t >= warmup_end.
            # If t < warmup_end and next_event > warmup_end, we split.
            
            if t < warmup_end:
                if next_event <= warmup_end:
                    # Entirely in warmup, ignore stats
                    pass
                else:
                    # Split at warmup_end
                    dt_warmup = warmup_end - t
                    dt_stat = next_event - warmup_end
                    
                    # Add stat part
                    total_area_N += current_N * dt_stat
                    if server_customer:
                        total_time_busy += dt_stat
                        total_time_nonempty += dt_stat # Since server busy implies N>=1
                    elif len(wait_queue) > 0:
                        total_time_nonempty += dt_stat
                        
                    # Counts don't happen during time passage, only at events.
                    # But wait, counts of arrivals/departures/blocks happen AT events.
                    # We need to check if the EVENT itself is after warmup.
                    
                    t = warmup_end # Advance to boundary? No, we process event at next_event.
                    # We just advanced time logically for integration.
                    # Now set t to next_event to process event.
                    # But we already added the stat portion.
                    # We need to ensure we don't double count or miss.
                    # Let's just advance t to next_event and handle integration carefully.
            
            # Re-evaluating integration strategy:
            # It is cleaner to just run the sim, and at the end, if we stored history, filter.
            # But memory might be an issue? H=100, lam=8 -> ~800 events. Small.
            # Let's store event history.
            
            # History: list of tuples (time, type, data)
            # Types: 'arr', 'dep', 'blk'
            # Also need state changes for area calculation.
            # Storing state at every event allows exact area calc.
            
            # Let's restart the inner loop logic with history storage.
            
            # Reset for this seed
            t = 0.0
            next_arrival = rng.expovariate(lam)
            server_customer = None
            wait_queue = []
            events = [] # (time, type, payload)
            states = [] # (time, N, is_busy)
            
            # Initial state
            states.append((0.0, 0, False))
            
            while True:
                next_dep = float('inf')
                if server_customer:
                    next_dep = server_customer['end_time']
                
                next_ev_t = min(next_arrival, next_dep, H)
                
                if next_ev_t >= H:
                    break
                
                # Record state change? No, state changes at events.
                # We need to know N and Busy status DURING intervals.
                # Current N = (1 if server_customer else 0) + len(wait_queue)
                # Current Busy = bool(server_customer)
                
                # Before processing event, we are at time t.
                # The interval [t, next_ev_t] has constant N and Busy.
                # We can calculate area contribution later using states list.
                
                if abs(next_ev_t - next_arrival) < 1e-9:
                    # Arrival
                    ev_type = 'arr'
                    t = next_ev_t
                    next_arrival = t + rng.expovariate(lam)
                    
                    # Service time drawn NOW
                    svc_time = rng.expovariate(mu)
                    
                    N_current = (1 if server_customer else 0) + len(wait_queue)
                    
                    if N_current < K:
                        # Accept
                        cust = {'arrival_time': t, 'service_time': svc_time}
                        if not server_customer:
                            server_customer = {'start_time': t, 'end_time': t + svc_time, 'data': cust}
                        else:
                            wait_queue.append(cust)
                        events.append((t, 'arr', cust))
                    else:
                        # Block
                        events.append((t, 'blk', None))
                        
                elif abs(next_ev_t - next_dep) < 1e-9:
                    # Departure
                    ev_type = 'dep'
                    t = next_ev_t
                    
                    # Complete service
                    cust = server_customer['data']
                    w_time = server_customer['start_time'] - cust['arrival_time']
                    s_time = server_customer['end_time'] - server_customer['start_time']
                    total_time_in_sys = w_time + s_time
                    
                    events.append((t, 'dep', {'cust': cust, 'w': w_time, 's': s_time, 'total': total_time_in_sys}))
                    
                    server_customer = None
                    
                    if wait_queue:
                        next_cust = wait_queue.pop(0)
                        server_customer = {'start_time': t, 'end_time': t + next_cust['service_time'], 'data': next_cust}
                
                # Record state AFTER event processing? 
                # The state for the NEXT interval is determined now.
                N_new = (1 if server_customer else 0) + len(wait_queue)
                Busy_new = bool(server_customer)
                states.append((t, N_new, Busy_new))
            
            # Finalize last interval
            if t < H:
                N_last = (1 if server_customer else 0) + len(wait_queue)
                B_last = bool(server_customer)
                states.append((H, N_last, B_last))
            
            # Calculate Statistics from History
            # 1. Areas (L, busy_frac, etc.)
            # Integrate over [warmup_end, H]
            
            area_N = 0.0
            time_busy = 0.0
            time_nonempty = 0.0
            
            for i in range(len(states)-1):
                t_start, N_val, B_val = states[i]
                t_end, _, _ = states[i+1]
                
                # Clip to [warmup_end, H]
                seg_start = max(t_start, warmup_end)
                seg_end = min(t_end, H)
                
                if seg_start < seg_end:
                    dt = seg_end - seg_start
                    area_N += N_val * dt
                    if B_val:
                        time_busy += dt
                    if N_val > 0:
                        time_nonempty += dt
            
            win_len = H - warmup_end
            L_avg = area_N / win_len if win_len > 0 else 0
            busy_frac_avg = time_nonempty / win_len if win_len > 0 else 0 # 1 - pi_0
            busy_util_avg = time_busy / win_len if win_len > 0 else 0 # E[min(N,c)]/c approx? 
            # For M/M/1, busy_util = P(Busy). Problem asks for busy_util=E[min(N,c)]/c.
            # In single server, min(N,1) is 1 if N>0, 0 if N=0. So E[min(N,1)] = P(N>0) = busy_frac.
            # Wait, definition: busy_util = E[min(N,c)]/c.
            # If c=1, min(N,1) is 1 if N>=1, 0 if N=0. So E[...] = P(N>0).
            # So busy_util should equal busy_frac for c=1?
            # Let's re-read: "busy_frac ... = 站不空的时间比例 1−π₀".
            # "busy_util=E[min(N,c)]/c".
            # For c=1, these are identical.
            # However, usually busy_util refers to server utilization.
            # I will calculate both as defined.
            
            # 2. Counts and Times from Events
            count_arr = 0
            count_blk = 0
            count_dep = 0
            sum_W = 0.0
            count_W = 0
            sum_wait_q = 0.0
            count_waited = 0
            
            for ev in events:
                t_ev, typ, data = ev
                if t_ev < warmup_end:
                    continue
                
                if typ == 'arr':
                    count_arr += 1
                elif typ == 'blk':
                    count_blk += 1
                elif typ == 'dep':
                    count_dep += 1
                    d = data
                    sum_W += d['total']
                    count_W += 1
                    if d['w'] > 1e-9:
                        sum_wait_q += d['w']
                        count_waited += 1
            
            W_avg = sum_W / count_W if count_W > 0 else 0
            p_loss_avg = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0
            # Note: p_loss is prob of rejection upon arrival.
            # Total arrivals attempted = accepted + blocked.
            # Accepted arrivals = count_arr (since arr event only logged if accepted? 
            # My code logs 'arr' only if accepted. Logs 'blk' if rejected.
            # So total attempts = count_arr + count_blk.
            
            p_wait_avg = count_waited / count_W if count_W > 0 else 0
            # Probability of waiting given service completion? Or given arrival?
            # Usually P(Wait) = P(N >= c upon arrival).
            # Here I calculated fraction of completed services that had wait > 0.
            # Let's stick to this interpretation or standard Little's law context.
            # Standard P_wait often means probability an arriving customer waits.
            # We don't have easy access to state at arrival time in post-processing without more work.
            # But we can infer: if they were queued, they waited.
            # Count of those who waited = count of departures where w > 0.
            # Denominator: Should be total accepted arrivals? Or total completions?
            # In steady state, rate of arrivals = rate of departures.
            # Let's use count_W as denominator for consistency with W.
            
            dep_rate = count_dep / win_len if win_len > 0 else 0
            
            all_L.append(L_avg)
            all_W.append(W_avg)
            all_busy_frac.append(busy_frac_avg)
            all_p_loss.append(p_loss_avg)
            all_arr.append(count_arr)
            all_blk.append(count_blk)
            all_dep.append(count_dep)
            all_p_wait.append(p_wait_avg)
            all_busy_util.append(busy_util_avg)
            all_busy_occupied.append(busy_frac_avg) # Same as busy_frac for c=1

    # Aggregate results
    seeds_used = len(all_L)
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occ = sum(all_busy_occupied) / seeds_used
    
    # Dep rate average
    avg_dep_rate = sum([d/(H*0.75) for d in all_dep]) / seeds_used if seeds_used > 0 else 0
    # Or better: total deps / total win time
    total_deps = sum(all_dep)
    total_win_time = seeds_used * (H * 0.75)
    overall_dep_rate = total_deps / total_win_time if total_win_time > 0 else 0
    
    lam_eff = overall_dep_rate # Effective arrival rate = departure rate in stable system
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H * 0.75, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(overall_dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_busy_occ, 4)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
