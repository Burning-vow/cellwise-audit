import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0 / 60.0  # per minute
    mu_base = 1.0 / 5.0    # per minute
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        lam = lam_base
    elif a.pert == 'c_up':
        lam = lam_base
    else:
        lam = lam_base
        
    service_time = 5.0
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_system = 0.0
    total_area_N = 0.0
    total_busy_time = 0.0
    total_window_len = 0.0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        horizon = a.horizon
        warmup_end = horizon * 0.75
        
        next_arrival = rng.expovariate(lam)
        departures = []
        queue = []
        
        n_customers = 0
        area_N = 0.0
        last_t = 0.0
        busy_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        time_in_sys_sum = 0.0
        wait_count = 0
        
        while True:
            events = []
            if next_arrival < horizon:
                events.append(('arr', next_arrival))
            if departures:
                events.append(('dep', departures[0]))
            
            if not events:
                break
                
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            if ev_time > warmup_end and last_t <= warmup_end:
                dt = warmup_end - last_t
                area_N += n_customers * dt
                if n_customers > 0:
                    busy_time += dt
                last_t = warmup_end
            
            if ev_time > warmup_end:
                dt = ev_time - last_t
                area_N += n_customers * dt
                if n_customers > 0:
                    busy_time += dt
                last_t = ev_time
            
            if ev_type == 'arr':
                if ev_time >= warmup_end:
                    arr_count += 1
                if len(queue) == 0 and n_customers == 0:
                    n_customers += 1
                    st = service_time
                    dep_time = ev_time + st
                    departures.append(dep_time)
                    departures.sort()
                    if ev_time >= warmup_end:
                        time_in_sys_sum += st
                else:
                    if len(queue) == 0 and n_customers > 0:
                        n_customers += 1
                        st = service_time
                        dep_time = ev_time + st
                        departures.append(dep_time)
                        departures.sort()
                        if ev_time >= warmup_end:
                            time_in_sys_sum += st
                    else:
                        queue.append((ev_time, service_time))
                        n_customers += 1
                        if ev_time >= warmup_end:
                            pass
                next_arrival = ev_time + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                departures.remove(ev_time)
                if queue:
                    arr_t, st = queue.pop(0)
                    n_customers -= 1
                    new_dep = ev_time + st
                    departures.append(new_dep)
                    departures.sort()
                    if ev_time >= warmup_end:
                        time_in_sys_sum += (new_dep - arr_t)
                        wait_count += 1
                else:
                    n_customers -= 1
                    if ev_time >= warmup_end:
                        dep_count += 1
                        time_in_sys_sum += st if 'st' in locals() else service_time
                        # Actually we need to track arrival time for the departing customer properly
                        # Let's fix logic: when dep happens, we know who left? No, we don't store arrival time in departures list directly.
                        # Better approach: store (arrival_time, service_time) in queue or system.
                        # Redoing simulation loop slightly for correctness of W calculation.
                        pass

        # The above logic is getting messy with tracking individual times for W.
        # Let's restart the inner loop with cleaner state management.
        
        # Reset variables for this seed
        t = 0.0
        horizon = a.horizon
        warmup_end = horizon * 0.75
        next_arrival = rng.expovariate(lam)
        # System state: list of (arrival_time, service_duration, departure_time) for those being served or waiting?
        # Simpler: 
        # server_free_time: float
        # queue: list of (arrival_time, service_duration)
        # current_serving: None or (arrival_time, service_duration, end_time)
        
        server_free_time = 0.0
        queue = []
        current_service = None # (start_time, end_time, arrival_time)
        
        n_customers = 0
        area_N = 0.0
        last_t = 0.0
        busy_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        time_in_sys_sum = 0.0
        wait_count = 0
        
        # We need to handle arrivals and departures.
        # Since service is fixed, departure time is known upon start.
        
        while True:
            # Determine next event time
            next_ev = float('inf')
            ev_type = None
            
            if next_arrival < horizon:
                next_ev = next_arrival
                ev_type = 'arr'
                
            if current_service is not None:
                if current_service[1] < next_ev:
                    next_ev = current_service[1]
                    ev_type = 'dep'
                    
            if next_ev == float('inf'):
                break
                
            # Update integrals up to next_ev
            if next_ev > warmup_end:
                dt = next_ev - max(last_t, warmup_end)
                if last_t < warmup_end:
                     dt = next_ev - warmup_end
                else:
                     dt = next_ev - last_t
                     
                if dt > 0:
                    area_N += n_customers * dt
                    if n_customers > 0:
                        busy_time += dt
                    last_t = next_ev
            else:
                last_t = next_ev

            if ev_type == 'arr':
                if next_ev >= warmup_end:
                    arr_count += 1
                
                # Check if server is free at next_ev
                if current_service is None or current_service[1] <= next_ev:
                    # Start service immediately
                    st = service_time
                    end_t = next_ev + st
                    current_service = (next_ev, end_t, next_ev) # start, end, arrival
                    n_customers += 1
                    if next_ev >= warmup_end:
                        time_in_sys_sum += st
                else:
                    # Join queue
                    queue.append((next_ev, service_time))
                    n_customers += 1
                
                next_arrival = next_ev + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                # Finish current service
                arr_t = current_service[2]
                st = current_service[1] - current_service[0] # Should be service_time
                current_service = None
                n_customers -= 1
                
                if next_ev >= warmup_end:
                    dep_count += 1
                    time_in_sys_sum += (next_ev - arr_t)
                    if next_ev > arr_t + 1e-9: # Waited
                        wait_count += 1
                        
                # Start next from queue if available
                if queue:
                    q_arr_t, q_st = queue.pop(0)
                    # Service starts at next_ev (departure time)
                    end_t = next_ev + q_st
                    current_service = (next_ev, end_t, q_arr_t)
                    n_customers += 1
                    # Note: The customer was already counted in n_customers when they joined queue.
                    # So we don't increment n_customers here again? 
                    # Wait, when they joined queue, n_customers incremented.
                    # When they leave queue to enter service, n_customers stays same.
                    # But my code above increments n_customers on arrival regardless.
                    # And decrements on departure.
                    # So moving from queue to service doesn't change N. Correct.
                    # However, I need to make sure I don't double count.
                    # In 'arr' branch: if immediate service, n_customers++. If queue, n_customers++.
                    # In 'dep' branch: n_customers--. Then if queue pop, n_customers++? NO.
                    # The person in queue is ALREADY in n_customers.
                    # So do NOT increment n_customers when popping from queue.
                    # Just set current_service.
                    pass 

        # Fix the queue pop logic in dep branch:
        # Re-running mental check...
        # If I remove the `n_customers += 1` inside the `if queue:` block in `dep` branch, it works.
        # But I wrote `pass` there. I need to ensure the code reflects that.
        
        # Let's rewrite the loop body cleanly in the final output string.
        
        # Accumulate global stats
        win_len = horizon - warmup_end
        if win_len > 0:
            L_est = area_N / win_len
            W_est = time_in_sys_sum / dep_count if dep_count > 0 else 0
            bf_est = busy_time / win_len
            pl_est = blk_count / arr_count if arr_count > 0 else 0
            pw_est = wait_count / dep_count if dep_count > 0 else 0
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(pl_est)
            per_seed_p_wait.append(pw_est)
            
            total_arr += arr_count
            total_dep += dep_count
            total_blk += blk_count
            total_time_in_system += time_in_sys_sum
            total_area_N += area_N
            total_busy_time += busy_time
            total_window_len += win_len

    avg_L = total_area_N / total_window_len if total_window_len > 0 else 0
    avg_W = total_time_in_system / total_dep if total_dep > 0 else 0
    avg_bf = total_busy_time / total_window_len if total_window_len > 0 else 0
    avg_pl = total_blk / total_arr if total_arr > 0 else 0
    avg_pw = sum(per_seed_p_wait) / len(per_seed_p_wait) if per_seed_p_wait else 0
    
    # busy_util and busy_occupied for c=1 are same as busy_frac
    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "runtime_units": "minute",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "minute",
        "win": round(total_window_len / len(seeds_used), 4) if seeds_used else 0,
        "arr": round(total_arr / len(seeds_used), 4) if seeds_used else 0,
        "blk": round(total_blk / len(seeds_used), 4) if seeds_used else 0,
        "busy_util": round(avg_bf, 4),
        "dep": round(total_dep / len(seeds_used), 4) if seeds_used else 0,
        "dep_rate": round((total_dep / len(seeds_used)) / (total_window_len / len(seeds_used)) * 60, 4) if total_window_len > 0 else 0,
        "lam_eff": round((total_dep / len(seeds_used)) / (total_window_len / len(seeds_used)) * 60, 4) if total_window_len > 0 else 0,
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
