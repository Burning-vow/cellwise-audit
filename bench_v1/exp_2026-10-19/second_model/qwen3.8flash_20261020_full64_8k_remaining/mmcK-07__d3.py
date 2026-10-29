import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    # Parameters in hours
    lam_base = 8.0
    mu_base = 5.0  # 60/12 = 5 per hour
    c = 3
    K = 4  # max capacity including in service

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
        K = 5
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win = H * 0.75  # after removing first 25% warmup
    warmup_end = H * 0.25

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_busy_occupied = []

    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)

        # Event simulation
        # Events: arrival, departure
        # State: number of cars in system (0..K), list of (arrival_time, service_duration) for each car in system
        # We track: total area under L(t) over [warmup_end, H], total waiting time sum, arrivals, blocks, departures
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Queue as list of tuples: (arrival_time, service_completion_time)
        # But we need to know when service starts. Let's store (arrival_time, start_service_time, end_service_time)
        # Actually simpler: maintain a list of active services with their end times.
        # For W calculation, we need wait time = start_service - arrival.
        
        # Let's use a different approach: event-driven with priority queue or just sorted events.
        # Since it's small, we can simulate step by step.
        
        # State variables
        n_in_system = 0
        # List of (arrival_time, service_end_time) for those currently in system
        # When a new car arrives, if n < K, it enters. If n >= c, it waits.
        # We need to track which cars are waiting vs serving.
        # Better: keep a list of cars in system with their status.
        # Each car: {arrival_time, service_duration, start_service_time, end_service_time}
        
        cars_in_system = []  # list of dicts
        # To find next departure, we look at min end_service_time among served cars.
        # But when a car finishes, the next waiting car starts immediately.
        
        # Let's pre-generate service durations upon arrival.
        
        # Accumulators for statistics within window [warmup_end, H]
        area_L = 0.0  # integral of n(t) dt
        sum_W = 0.0   # sum of waiting times for cars that departed within window? 
                      # Standard definition: W is average time in system. 
                      # Time in system = end_service - arrival.
                      # We accumulate time-in-system for each departure.
        count_departures_window = 0
        count_arrivals_window = 0
        count_blocks_window = 0
        busy_time = 0.0  # time when n(t) > 0
        
        # We also need to handle cars that are still in system at H.
        # Typically, we only count completed services for W, or include partial?
        # Common practice: only count completed. Or truncate.
        # Let's count only completed departures for W and dep counts.
        # For L and busy_frac, we integrate up to H.
        
        # Initial state
        last_event_time = 0.0
        
        # Generate initial arrival
        # We'll process events until H
        
        # Priority queue of events: (time, type, data)
        # type: 'A' for arrival, 'D' for departure
        import heapq
        events = []
        
        # First arrival
        heapq.heappush(events, (next_arrival, 'A', None))
        
        # Track current time for integration
        prev_t = 0.0
        prev_n = 0
        
        while events:
            t_curr, etype, edata = heapq.heappop(events)
            
            if t_curr > H:
                break
            
            # Integrate from prev_t to t_curr
            dt = t_curr - prev_t
            if dt > 0:
                # Area under L
                if prev_t < warmup_end:
                    # Split interval
                    if t_curr <= warmup_end:
                        pass  # entirely in warmup
                    else:
                        # Partly in warmup, partly in window
                        # Window part: [warmup_end, t_curr]
                        area_L += prev_n * (t_curr - warmup_end)
                        if prev_n > 0:
                            busy_time += (t_curr - warmup_end)
                else:
                    area_L += prev_n * dt
                    if prev_n > 0:
                        busy_time += dt
            
            prev_t = t_curr
            
            if etype == 'A':
                # Arrival
                if t_curr >= warmup_end:
                    count_arrivals_window += 1
                
                if len(cars_in_system) < K:
                    # Accept
                    svc_dur = rng.expovariate(mu)
                    # Determine start service time
                    # Find how many are being served (those with end_service_time > t_curr? No.)
                    # Cars in system have: arrival, svc_dur, start, end.
                    # A car is "served" if its start <= t_curr < end.
                    # A car is "waiting" if start > t_curr.
                    # Count currently served:
                    num_serving = sum(1 for car in cars_in_system if car['start'] <= t_curr < car['end'])
                    
                    if num_serving < c:
                        start_t = t_curr
                    else:
                        # Must wait. Find earliest end among served cars.
                        # The next available server time is min(end) among those with end > t_curr and start <= t_curr
                        # Actually, since we process events chronologically, any car that has ended would have been removed.
                        # So all cars in cars_in_system have end > t_curr.
                        # Those with start <= t_curr are being served.
                        # Those with start > t_curr are waiting.
                        # If num_serving == c, then this new car must wait.
                        # Its start time will be determined when a server frees up.
                        # We don't set start yet. We set it later when a departure happens.
                        start_t = None
                    
                    car = {'arrival': t_curr, 'svc_dur': svc_dur, 'start': start_t, 'end': None}
                    if start_t is not None:
                        car['end'] = start_t + svc_dur
                        heapq.heappush(events, (car['end'], 'D', id(car)))
                    cars_in_system.append(car)
                    prev_n = len(cars_in_system)
                else:
                    # Block
                    if t_curr >= warmup_end:
                        count_blocks_window += 1
                    prev_n = len(cars_in_system)
                
                # Schedule next arrival
                next_arrival = t_curr + rng.expovariate(lam)
                heapq.heappush(events, (next_arrival, 'A', None))
                
            elif etype == 'D':
                # Departure
                # Find the car
                car_idx = None
                for idx, car in enumerate(cars_in_system):
                    if id(car) == edata:
                        car_idx = idx
                        break
                
                if car_idx is not None:
                    car = cars_in_system.pop(car_idx)
                    # This car has finished service
                    if t_curr >= warmup_end:
                        count_departures_window += 1
                        time_in_sys = t_curr - car['arrival']
                        sum_W += time_in_sys
                    
                    # Now check if there are waiting cars that can start
                    # Waiting cars are those with start is None
                    waiting_cars = [c for c in cars_in_system if c['start'] is None]
                    # Sort by arrival time (FIFO)
                    waiting_cars.sort(key=lambda x: x['arrival'])
                    
                    # How many servers are free now?
                    # After removal, count how many are being served
                    num_serving_now = sum(1 for c in cars_in_system if c['start'] is not None and c['start'] <= t_curr < c['end'])
                    free_servers = c - num_serving_now
                    
                    for wc in waiting_cars[:free_servers]:
                        wc['start'] = t_curr
                        wc['end'] = t_curr + wc['svc_dur']
                        heapq.heappush(events, (wc['end'], 'D', id(wc)))
                    
                    prev_n = len(cars_in_system)
        
        # Final integration from prev_t to H if needed
        if prev_t < H:
            dt = H - prev_t
            if prev_t < warmup_end:
                if H > warmup_end:
                    area_L += prev_n * (H - warmup_end)
                    if prev_n > 0:
                        busy_time += (H - warmup_end)
            else:
                area_L += prev_n * dt
                if prev_n > 0:
                    busy_time += dt
        
        # Compute stats for this seed
        L_est = area_L / win if win > 0 else 0.0
        W_est = sum_W / count_departures_window if count_departures_window > 0 else 0.0
        busy_frac_est = busy_time / win if win > 0 else 0.0
        p_loss_est = count_blocks_window / count_arrivals_window if count_arrivals_window > 0 else 0.0
        p_wait_est = 0.0
        # p_wait: probability that an arriving customer has to wait?
        # Or fraction of time someone is waiting? Usually P(wait) = prob that an arrival finds all servers busy.
        # We didn't track that directly. Let's approximate: 
        # In M/M/c/K, P(wait) is related to Erlang C. But here we can estimate from simulation.
        # We need to count arrivals that had to wait.
        # I didn't track that. Let me add tracking.
        
        # Re-run logic mentally: I need to track arrivals that waited.
        # Since I already ran the loop, I'll modify the code above to track it.
        # But I'm writing final code. Let me adjust.
        
        # Actually, let me restructure slightly to capture p_wait properly.
        # I'll rewrite the inner loop to track waited_arrivals.
        
        # For now, placeholder. I'll fix in final code.
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(0.0)  # Will fix
        all_arr.append(count_arrivals_window)
        all_blk.append(count_blocks_window)
        all_dep.append(count_departures_window)
        all_busy_util.append(0.0)  # E[min(N,c)]/c
        all_dep_rate.append(count_departures_window / win if win > 0 else 0.0)
        all_lam_eff.append(count_arrivals_window / win if win > 0 else 0.0)
        all_busy_occupied.append(busy_frac_est)

    # Need to redo with proper tracking. Let me write cleaner version.
    
    # Reset and do it properly
    results = []
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        events = []
        next_arrival = rng.expovariate(lam)
        heapq.heappush(events, (next_arrival, 'A', None))
        
        cars_in_system = []
        prev_t = 0.0
        prev_n = 0
        area_L = 0.0
        sum_W = 0.0
        count_dep_win = 0
        count_arr_win = 0
        count_blk_win = 0
        count_waited_arr_win = 0
        busy_time = 0.0
        area_min_N_c = 0.0  # for busy_util
        
        while events:
            t_curr, etype, edata = heapq.heappop(events)
            if t_curr > H:
                break
            
            dt = t_curr - prev_t
            if dt > 0:
                # Update integrals
                if prev_t < warmup_end:
                    if t_curr > warmup_end:
                        w_dt = t_curr - warmup_end
                        area_L += prev_n * w_dt
                        if prev_n > 0:
                            busy_time += w_dt
                        area_min_N_c += min(prev_n, c) * w_dt
                else:
                    area_L += prev_n * dt
                    if prev_n > 0:
                        busy_time += dt
                    area_min_N_c += min(prev_n, c) * dt
            
            prev_t = t_curr
            
            if etype == 'A':
                if t_curr >= warmup_end:
                    count_arr_win += 1
                
                if len(cars_in_system) < K:
                    svc_dur = rng.expovariate(mu)
                    num_serving = sum(1 for car in cars_in_system if car['start'] is not None and car['start'] <= t_curr < car['end'])
                    
                    if num_serving < c:
                        start_t = t_curr
                        end_t = start_t + svc_dur
                        car = {'arrival': t_curr, 'svc_dur': svc_dur, 'start': start_t, 'end': end_t}
                        heapq.heappush(events, (end_t, 'D', id(car)))
                    else:
                        car = {'arrival': t_curr, 'svc_dur': svc_dur, 'start': None, 'end': None}
                        if t_curr >= warmup_end:
                            count_waited_arr_win += 1
                    
                    cars_in_system.append(car)
                    prev_n = len(cars_in_system)
                else:
                    if t_curr >= warmup_end:
                        count_blk_win += 1
                    prev_n = len(cars_in_system)
                
                next_arrival = t_curr + rng.expovariate(lam)
                heapq.heappush(events, (next_arrival, 'A', None))
                
            elif etype == 'D':
                car_idx = None
                for idx, car in enumerate(cars_in_system):
                    if id(car) == edata:
                        car_idx = idx
                        break
                
                if car_idx is not None:
                    car = cars_in_system.pop(car_idx)
                    if t_curr >= warmup_end:
                        count_dep_win += 1
                        sum_W += t_curr - car['arrival']
                    
                    waiting_cars = [c for c in cars_in_system if c['start'] is None]
                    waiting_cars.sort(key=lambda x: x['arrival'])
                    
                    num_serving_now = sum(1 for c in cars_in_system if c['start'] is not None and c['start'] <= t_curr < c['end'])
                    free_servers = c - num_serving_now
                    
                    for wc in waiting_cars[:free_servers]:
                        wc['start'] = t_curr
                        wc['end'] = t_curr + wc['svc_dur']
                        heapq.heappush(events, (wc['end'], 'D', id(wc)))
                    
                    prev_n = len(cars_in_system)
        
        if prev_t < H:
            dt = H - prev_t
            if prev_t < warmup_end:
                if H > warmup_end:
                    w_dt = H - warmup_end
                    area_L += prev_n * w_dt
                    if prev_n > 0:
                        busy_time += w_dt
                    area_min_N_c += min(prev_n, c) * w_dt
            else:
                area_L += prev_n * dt
                if prev_n > 0:
                    busy_time += dt
                area_min_N_c += min(prev_n, c) * dt
        
        L_est = area_L / win if win > 0 else 0.0
        W_est = sum_W / count_dep_win if count_dep_win > 0 else 0.0
        busy_frac_est = busy_time / win if win > 0 else 0.0
        p_loss_est = count_blk_win / count_arr_win if count_arr_win > 0 else 0.0
        p_wait_est = count_waited_arr_win / count_arr_win if count_arr_win > 0 else 0.0
        busy_util_est = (area_min_N_c / win) / c if win > 0 else 0.0
        dep_rate_est = count_dep_win / win if win > 0 else 0.0
        lam_eff_est = count_arr_win / win if win > 0 else 0.0
        
        results.append({
            'L': L_est, 'W': W_est, 'busy_frac': busy_frac_est, 'p_loss': p_loss_est,
            'p_wait': p_wait_est, 'arr': count_arr_win, 'blk': count_blk_win,
            'dep': count_dep_win, 'busy_util': busy_util_est, 'dep_rate': dep_rate_est,
            'lam_eff': lam_eff_est, 'busy_occupied': busy_frac_est
        })
    
    seeds_used = len(results)
    seed_list = [seed_start + i for i in range(seeds_used)]
    
    avg_L = sum(r['L'] for r in results) / seeds_used
    avg_W = sum(r['W'] for r in results) / seeds_used
    avg_busy_frac = sum(r['busy_frac'] for r in results) / seeds_used
    avg_p_loss = sum(r['p_loss'] for r in results) / seeds_used
    avg_p_wait = sum(r['p_wait'] for r in results) / seeds_used
    avg_arr = sum(r['arr'] for r in results) / seeds_used
    avg_blk = sum(r['blk'] for r in results) / seeds_used
    avg_dep = sum(r['dep'] for r in results) / seeds_used
    avg_busy_util = sum(r['busy_util'] for r in results) / seeds_used
    avg_dep_rate = sum(r['dep_rate'] for r in results) / seeds_used
    avg_lam_eff = sum(r['lam_eff'] for r in results) / seeds_used
    
    out = {
        'L': round(avg_L, 6),
        'W': round(avg_W, 6),
        'busy_frac': round(avg_busy_frac, 6),
        'p_loss': round(avg_p_loss, 6),
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': round(win, 6),
        'arr': round(avg_arr, 6),
        'blk': round(avg_blk, 6),
        'busy_util': round(avg_busy_util, 6),
        'dep': round(avg_dep, 6),
        'dep_rate': round(avg_dep_rate, 6),
        'lam_eff': round(avg_lam_eff, 6),
        'p_wait': round(avg_p_wait, 6),
        'per_seed_L': [round(r['L'], 6) for r in results],
        'per_seed_W': [round(r['W'], 6) for r in results],
        'per_seed_busy_frac': [round(r['busy_frac'], 6) for r in results],
        'per_seed_p_loss': [round(r['p_loss'], 6) for r in results],
        'per_seed_p_wait': [round(r['p_wait'], 6) for r in results]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
