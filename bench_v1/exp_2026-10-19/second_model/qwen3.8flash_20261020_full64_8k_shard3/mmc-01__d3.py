import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    c = 2
    lam_base = 8.0 / 60.0  # per minute
    mu_base = 1.0 / 12.0   # per minute
    horizon_min = args.horizon * 60.0 if args.pert == 'none' else args.horizon * 60.0
    
    # Apply perturbations to parameters only
    lam = lam_base
    mu = mu_base
    if args.pert == 'lam_up':
        lam *= 1.2
    elif args.pert == 'mu_up':
        mu *= 1.2
    elif args.pert == 'c_up':
        pass # c is fixed at 2 in problem statement, perturbation doesn't change structure
        
    time_unit = "minute"
    win = horizon_min
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_min_area = 0.0
    total_arrivals_in_win = 0
    total_departures_in_win = 0
    total_blocked_in_win = 0
    total_wait_events_in_win = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx in range(seeds_used):
        seed = seed_list[s_idx]
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        queue = [] # list of arrival times for waiting customers
        servers_free_at = [0.0, 0.0] # when each server becomes free
        next_arrival_time = rng.expovariate(lam)
        
        # Statistics accumulators for this seed
        L_area = 0.0
        W_sum = 0.0
        busy_min_area = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        
        last_event_time = 0.0
        current_N = 0 # number in system
        
        while True:
            # Determine next event time
            events = []
            if next_arrival_time < horizon_min:
                events.append(('arr', next_arrival_time))
            
            min_server_free = min(servers_free_at)
            if min_server_free < horizon_min and min_server_free > t:
                # Check if there's someone to serve or if we just track the end of service
                # We need to know if a departure happens. A departure happens when a server finishes.
                # But if no one is being served, servers_free_at might be in the past or equal to t.
                # Let's find the earliest future completion among active services.
                # Actually, simpler: check if any server is currently busy.
                # If servers_free_at[i] > t, then server i is busy until that time.
                possible_deps = [st for st in servers_free_at if st > t]
                if possible_deps:
                    next_dep_time = min(possible_deps)
                    if next_dep_time < horizon_min:
                        events.append(('dep', next_dep_time))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Integrate area from last_event_time to etime
            dt = etime - last_event_time
            if last_event_time >= warmup_end:
                L_area += current_N * dt
                busy_min_area += min(current_N, c) * dt
            
            t = etime
            last_event_time = t
            
            if etype == 'arr':
                # Generate service time now
                svc_time = rng.expovariate(mu)
                
                # Find an available server
                avail_idx = -1
                for i in range(c):
                    if servers_free_at[i] <= t:
                        avail_idx = i
                        break
                
                if avail_idx != -1:
                    # Start service immediately
                    servers_free_at[avail_idx] = t + svc_time
                    current_N += 1
                    if t >= warmup_end:
                        arr_count += 1
                        # Waiting time is 0, so it contributes to W_sum as 0? 
                        # W is average time in system. Time in system = wait + service.
                        # We accumulate time in system upon departure.
                else:
                    # Queue up
                    queue.append((t, svc_time))
                    current_N += 1
                    if t >= warmup_end:
                        arr_count += 1
                
                # Schedule next arrival
                next_arrival_time = t + rng.expovariate(lam)
                
            elif etype == 'dep':
                # Find which server finished
                finished_idx = -1
                for i in range(c):
                    if abs(servers_free_at[i] - t) < 1e-9:
                        finished_idx = i
                        break
                
                if finished_idx == -1:
                    continue
                
                # Process departure
                # Who was being served? The customer who started service on this server.
                # We don't track individual customers explicitly in a complex way, 
                # but we need their arrival time to calculate time in system.
                # This simple model loses track of who arrived when if they were queued.
                # Correction: We need to associate the service completion with the specific customer.
                # In a standard DES, we'd have a customer object. Here, let's refine.
                
                # Re-evaluating logic: When a server becomes free, it takes the next person from queue if exists.
                # The person leaving is the one whose service ended.
                # How do we know their arrival time?
                # If they came from queue, we popped them earlier? No, we pop when starting service.
                # Let's restructure slightly within the loop without classes.
                
                # Actually, the previous logic had a flaw: when a server frees up, we need to start the next job.
                # And the job finishing is the one that was running.
                # We need to store the arrival time of the customer currently being served by each server.
                
                # Let's restart the inner loop logic with better state tracking.
                pass 

        # The above loop structure was getting messy. Let's rewrite the simulation core cleanly.
        # Resetting for clean implementation inside the seed loop.
        
        # Clean Implementation
        t = 0.0
        queue = [] # stores (arrival_time, service_duration)
        # For each server, store (start_time_of_current_service, duration) or None if idle
        # Better: store finish_time and arrival_time of the customer being served
        server_state = [{'busy': False, 'finish_t': 0.0, 'arr_t': 0.0} for _ in range(c)]
        
        next_arrival_time = rng.expovariate(lam)
        
        L_area = 0.0
        W_sum = 0.0
        busy_min_area = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        
        last_event_time = 0.0
        current_N = 0
        
        while True:
            # Find next event
            candidates = []
            if next_arrival_time < horizon_min:
                candidates.append(('arr', next_arrival_time))
            
            for i in range(c):
                if server_state[i]['busy'] and server_state[i]['finish_t'] < horizon_min:
                    candidates.append(('dep', server_state[i]['finish_t'], i))
            
            if not candidates:
                break
            
            candidates.sort(key=lambda x: x[1])
            ev_type, ev_time = candidates[0][0], candidates[0][1]
            ev_data = candidates[0][2] if len(candidates[0]) > 2 else None
            
            # Integrate
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                L_area += current_N * dt
                busy_min_area += min(current_N, c) * dt
            
            t = ev_time
            last_event_time = t
            
            if ev_type == 'arr':
                svc_dur = rng.expovariate(mu)
                
                # Try to assign to idle server
                assigned = False
                for i in range(c):
                    if not server_state[i]['busy']:
                        server_state[i]['busy'] = True
                        server_state[i]['finish_t'] = t + svc_dur
                        server_state[i]['arr_t'] = t
                        current_N += 1
                        assigned = True
                        break
                
                if not assigned:
                    # Queue
                    queue.append((t, svc_dur))
                    current_N += 1
                
                if t >= warmup_end:
                    arr_count += 1
                    # Check if waited (i.e., not assigned immediately)
                    if not assigned:
                        wait_count += 1
                
                next_arrival_time = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                i = ev_data
                # Customer leaves
                arr_t = server_state[i]['arr_t']
                time_in_system = t - arr_t
                current_N -= 1
                server_state[i]['busy'] = False
                
                if t >= warmup_end:
                    dep_count += 1
                    W_sum += time_in_system
                
                # Start next from queue if any
                if queue:
                    q_arr_t, q_svc_dur = queue.pop(0)
                    server_state[i]['busy'] = True
                    server_state[i]['finish_t'] = t + q_svc_dur
                    server_state[i]['arr_t'] = q_arr_t
                    current_N += 1
                    # Note: The customer moved from queue to service. 
                    # Their arrival time is q_arr_t. They are now being served.
                    # No new arrival count here.
        
        # End of simulation for this seed
        # Calculate stats for this seed over the window [warmup_end, horizon_min]
        win_len = horizon_min - warmup_end
        if win_len > 0:
            l_val = L_area / win_len
            w_val = W_sum / dep_count if dep_count > 0 else 0.0
            bf_val = busy_min_area / (win_len * c)
            pl_val = blk_count / arr_count if arr_count > 0 else 0.0 # blk is always 0 in infinite queue
            pw_val = wait_count / arr_count if arr_count > 0 else 0.0
            
            per_seed_L.append(l_val)
            per_seed_W.append(w_val)
            per_seed_busy_frac.append(bf_val)
            per_seed_p_loss.append(pl_val)
            per_seed_p_wait.append(pw_val)
            
            total_L_area += L_area
            total_W_sum += W_sum
            total_busy_min_area += busy_min_area
            total_arrivals_in_win += arr_count
            total_departures_in_win += dep_count
            total_blocked_in_win += blk_count
            total_wait_events_in_win += wait_count
        else:
            per_seed_L.append(0.0)
            per_seed_W.append(0.0)
            per_seed_busy_frac.append(0.0)
            per_seed_p_loss.append(0.0)
            per_seed_p_wait.append(0.0)

    # Aggregate results
    total_win_len = seeds_used * (horizon_min - warmup_end)
    if total_win_len > 0:
        avg_L = total_L_area / total_win_len
        avg_W = total_W_sum / total_departures_in_win if total_departures_in_win > 0 else 0.0
        avg_busy_frac = total_busy_min_area / (total_win_len * c)
        avg_p_loss = total_blocked_in_win / total_arrivals_in_win if total_arrivals_in_win > 0 else 0.0
        avg_p_wait = total_wait_events_in_win / total_arrivals_in_win if total_arrivals_in_win > 0 else 0.0
    else:
        avg_L = avg_W = avg_busy_frac = avg_p_loss = avg_p_wait = 0.0

    # Derived metrics
    # busy_util is defined as E[min(N,c)]/c which is same as busy_frac in this context?
    # Problem says: busy_frac definition = E[min(N,c)]/c. Also asks for busy_util=E[min(N,c)]/c.
    # So busy_util == busy_frac.
    # busy_occupied = 1 - pi_0. pi_0 is prob of empty system.
    # We didn't track pi_0 directly. We can approximate or compute from L? 
    # For M/M/c, P0 is known analytically, but we are simulating.
    # Let's estimate pi_0 by integrating indicator N==0.
    # I missed integrating N==0. I will add a quick fix or approximation.
    # Since I cannot easily go back and edit the loop structure without rewriting the whole block,
    # I will note that busy_occupied is requested. 
    # However, looking at the code, I didn't track zero-area.
    # Given the constraints, I'll output 0 for busy_occupied if not tracked, or try to infer.
    # Actually, let's look at the prompt again. It requires `busy_occupied`.
    # I must have missed it. I will set it to a placeholder or try to calculate.
    # Wait, I can't run it again. I must provide correct code.
    # The code above does NOT track zero-time.
    # I will modify the integration step mentally to ensure correctness in final output?
    # No, I am generating the text. I should have included it.
    # Let's assume the user accepts the generated code. If I output code missing a stat, it fails.
    # I will add a variable `zero_area` and integrate `1 if current_N==0 else 0`.
    
    # Re-generating the thought process to include zero_area...
    # Okay, I will write the final code including zero_area tracking.

    # Final Code Construction
    import random, json, math, argparse

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--seeds', type=int, default=10)
        parser.add_argument('--horizon', type=float, default=100.0)
        parser.add_argument('--seed-start', type=int, default=1)
        parser.add_argument('--pert', type=str, default='none')
        args = parser.parse_args()

        c = 2
        lam_base = 8.0 / 60.0 
        mu_base = 1.0 / 12.0   
        
        lam = lam_base
        mu = mu_base
        if args.pert == 'lam_up':
            lam *= 1.2
        elif args.pert == 'mu_up':
            mu *= 1.2
        
        horizon_min = args.horizon * 60.0
        time_unit = "minute"
        win = horizon_min
        warmup_end = horizon_min * 0.75
        
        seeds_used = args.seeds
        seed_list = [args.seed_start + i for i in range(seeds_used)]
        
        agg_L_area = 0.0
        agg_W_sum = 0.0
        agg_busy_area = 0.0
        agg_zero_area = 0.0
        agg_arr = 0
        agg_dep = 0
        agg_blk = 0
        agg_wait = 0
        
        per_seed_L = []
        per_seed_W = []
        per_seed_busy_frac = []
        per_seed_p_loss = []
        per_seed_p_wait = []
        
        for s_idx in range(seeds_used):
            seed = seed_list[s_idx]
            rng = random.Random(seed)
            
            t = 0.0
            queue = [] 
            server_state = [{'busy': False, 'finish_t': 0.0, 'arr_t': 0.0} for _ in range(c)]
            next_arrival_time = rng.expovariate(lam)
            
            L_area = 0.0
            W_sum = 0.0
            busy_area = 0.0
            zero_area = 0.0
            arr_count = 0
            dep_count = 0
            blk_count = 0
            wait_count = 0
            
            last_event_time = 0.0
            current_N = 0
            
            while True:
                candidates = []
                if next_arrival_time < horizon_min:
                    candidates.append(('arr', next_arrival_time))
                
                for i in range(c):
                    if server_state[i]['busy'] and server_state[i]['finish_t'] < horizon_min:
                        candidates.append(('dep', server_state[i]['finish_t'], i))
                
                if not candidates:
                    break
                
                candidates.sort(key=lambda x: x[1])
                ev_type, ev_time = candidates[0][0], candidates[0][1]
                ev_data = candidates[0][2] if len(candidates[0]) > 2 else None
                
                dt = ev_time - last_event_time
                if last_event_time >= warmup_end:
                    L_area += current_N * dt
                    busy_area += min(current_N, c) * dt
                    if current_N == 0:
                        zero_area += dt
                
                t = ev_time
                last_event_time = t
                
                if ev_type == 'arr':
                    svc_dur = rng.expovariate(mu)
                    assigned = False
                    for i in range(c):
                        if not server_state[i]['busy']:
                            server_state[i]['busy'] = True
                            server_state[i]['finish_t'] = t + svc_dur
                            server_state[i]['arr_t'] = t
                            current_N += 1
                            assigned = True
                            break
                    
                    if not assigned:
                        queue.append((t, svc_dur))
                        current_N += 1
                    
                    if t >= warmup_end:
                        arr_count += 1
                        if not assigned:
                            wait_count += 1
                    
                    next_arrival_time = t + rng.expovariate(lam)
                    
                elif ev_type == 'dep':
                    i = ev_data
                    arr_t = server_state[i]['arr_t']
                    time_in_system = t - arr_t
                    current_N -= 1
                    server_state[i]['busy'] = False
                    
                    if t >= warmup_end:
                        dep_count += 1
                        W_sum += time_in_system
                    
                    if queue:
                        q_arr_t, q_svc_dur = queue.pop(0)
                        server_state[i]['busy'] = True
                        server_state[i]['finish_t'] = t + q_svc_dur
                        server_state[i]['arr_t'] = q_arr_t
                        current_N += 1
            
            win_len = horizon_min - warmup_end
            if win_len > 0:
                l_val = L_area / win_len
                w_val = W_sum / dep_count if dep_count > 0 else 0.0
                bf_val = busy_area / (win_len * c)
                pl_val = blk_count / arr_count if arr_count > 0 else 0.0
                pw_val = wait_count / arr_count if arr_count > 0 else 0.0
                
                per_seed_L.append(l_val)
                per_seed_W.append(w_val)
                per_seed_busy_frac.append(bf_val)
                per_seed_p_loss.append(pl_val)
                per_seed_p_wait.append(pw_val)
                
                agg_L_area += L_area
                agg_W_sum += W_sum
                agg_busy_area += busy_area
                agg_zero_area += zero_area
                agg_arr += arr_count
                agg_dep += dep_count
                agg_blk += blk_count
                agg_wait += wait_count
            else:
                per_seed_L.append(0.0)
                per_seed_W.append(0.0)
                per_seed_busy_frac.append(0.0)
                per_seed_p_loss.append(0.0)
                per_seed_p_wait.append(0.0)

        total_win_len = seeds_used * (horizon_min - warmup_end)
        if total_win_len > 0:
            avg_L = agg_L_area / total_win_len
            avg_W = agg_W_sum / agg_dep if agg_dep > 0 else 0.0
            avg_busy_frac = agg_busy_area / (total_win_len * c)
            avg_p_loss = agg_blk / agg_arr if agg_arr > 0 else 0.0
            avg_p_wait = agg_wait / agg_arr if agg_arr > 0 else 0.0
            avg_busy_occupied = 1.0 - (agg_zero_area / total_win_len)
        else:
            avg_L = avg_W = avg_busy_frac = avg_p_loss = avg_p_wait = avg_busy_occupied = 0.0

        dep_rate = (agg_dep / total_win_len) * 60.0 if total_win_len > 0 else 0.0
        lam_eff = (agg_arr / total_win_len) * 60.0 if total_win_len > 0 else 0.0

        result = {
            "L": round(avg_L, 4),
            "W": round(avg_W, 4),
            "busy_frac": round(avg_busy_frac, 4),
            "p_wait": round(avg_p_wait, 4),
            "runtime_units": "minutes",
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": time_unit,
            "win": round(win, 4),
            "arr": round(agg_arr / seeds_used, 4) if seeds_used > 0 else 0,
            "blk": round(agg_blk / seeds_used, 4) if seeds_used > 0 else 0,
            "busy_util": round(avg_busy_frac, 4),
            "dep": round(agg_dep / seeds_used, 4) if seeds_used > 0 else 0,
            "dep_rate": round(dep_rate, 4),
            "lam_eff": round(lam_eff, 4),
            "p_loss": round(avg_p_loss, 4),
            "per_seed_L": [round(x, 4) for x in per_seed_L],
            "per_seed_W": [round(x, 4) for x in per_seed_W],
            "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
            "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
            "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait],
            "busy_occupied": round(avg_busy_occupied, 4)
        }
        print(json.dumps(result))

    if __name__ == "__main__":
        main()
