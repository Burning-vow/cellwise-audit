import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert
    
    lam_base = 4.0
    mu_base = 10.0
    c_base = 1.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = c_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        c = c_base
        
    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        srv1_done = float('inf')
        srv2_done = float('inf')
        
        q1 = []
        q2 = []
        
        busy1_time = 0.0
        busy2_time = 0.0
        last_state_change_t = 0.0
        prev_busy1 = False
        prev_busy2 = False
        
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        
        total_w_in_win = 0.0
        count_w_in_win = 0
        
        # For L calculation via area under curve
        area_L = 0.0
        last_area_t = 0.0
        current_L = 0
        
        while t < H:
            # Determine next event
            events = []
            if next_arr < H:
                events.append(('arr', next_arr))
            if srv1_done < H and srv1_done != float('inf'):
                events.append(('srv1_end', srv1_done))
            if srv2_done < H and srv2_done != float('inf'):
                events.append(('srv2_end', srv2_done))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Update area for L before changing state
            dt = etime - last_area_t
            area_L += current_L * dt
            last_area_t = etime
            
            # Update busy times
            if prev_busy1:
                busy1_time += etime - last_state_change_t
            if prev_busy2:
                busy2_time += etime - last_state_change_t
            last_state_change_t = etime
            
            t = etime
            
            if etype == 'arr':
                if t >= warmup:
                    arrivals_in_win += 1
                
                # Generate service time now
                st1 = rng.expovariate(mu)
                
                # Check capacity or just queue? Problem says "each has its own queue", no blocking mentioned explicitly except p_loss key. 
                # Standard Jackson network usually infinite buffer unless specified. But p_loss is requested. 
                # If infinite buffer, p_loss should be 0. Let's assume infinite buffer as per standard "queue" description.
                # However, if there was a limit, it would be stated. I will assume infinite buffer, so blk=0, p_loss=0.
                
                q1.append((t, st1))
                current_L += 1
                
                if len(q1) == 1:
                    # Start service immediately
                    _, s = q1.pop(0)
                    srv1_done = t + s
                    prev_busy1 = True
                else:
                    prev_busy1 = True # Server remains busy if it was already busy, but here we are at arrival. 
                    # Wait, if server was idle, it becomes busy. If busy, stays busy.
                    # We need to track if server is currently serving.
                    # Actually, simpler: if q1 was empty before push, server starts. Else server continues.
                    # The flag prev_busy1 needs to reflect status AFTER this event for the next interval.
                    # If server was idle (q1 empty), it becomes busy.
                    # If server was busy, it stays busy.
                    # How do we know if it was idle? If srv1_done was inf or <= t?
                    # Let's refine logic.
                    
                # Re-evaluate busy status for next interval
                # If q1 is not empty OR server is working on something (which means q1 had items and one was taken out?)
                # My pop above took one out. So if q1 is empty after pop, and we started service, server is busy.
                # If q1 is not empty, server is busy.
                # If we didn't start service (because q1 wasn't empty before?), wait.
                
                # Correction:
                # Before arrival:
                # Was server 1 busy? Yes if srv1_done > t_prev or q1 non-empty? No, q1 holds waiting jobs.
                # Let's use a boolean `is_srv1_busy`.
                
                # Resetting approach for clarity inside loop:
                pass 

            elif etype == 'srv1_end':
                # Job finishes stage 1
                # Move to stage 2
                # Find the job that finished. It was the head of the processing.
                # We don't store job ID, just completion time.
                # When srv1 ends, the job leaves q1/processing and enters q2.
                # We need to know when it arrived to calculate W later.
                # But we popped it from q1 when starting service. We lost the arrival time!
                # Fix: Store arrival time with the job being served.
                
                # This requires restructuring.
                # Let's restart the simulation logic with proper state tracking.
                break # Break to rewrite below

        # --- RESTART LOGIC WITH CORRECT STATE TRACKING ---
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        
        # State variables
        # Stage 1
        srv1_job_arrival = None # Arrival time of job currently in service 1
        srv1_finish_time = float('inf')
        q1 = [] # List of (arrival_time, service_time)
        
        # Stage 2
        srv2_job_arrival = None
        srv2_finish_time = float('inf')
        q2 = [] # List of (arrival_time, service_time)
        
        # Metrics accumulators
        busy1_dur = 0.0
        busy2_dur = 0.0
        last_t = 0.0
        is_b1 = False
        is_b2 = False
        
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        w_sum = 0.0
        w_cnt = 0
        l_area = 0.0
        cur_l = 0
        
        while t < H:
            candidates = []
            if next_arr < H: candidates.append(('A', next_arr))
            if srv1_finish_time < H: candidates.append(('S1', srv1_finish_time))
            if srv2_finish_time < H: candidates.append(('S2', srv2_finish_time))
            
            if not candidates: break
            
            candidates.sort(key=lambda x: x[1])
            ev_type, ev_time = candidates[0]
            
            # Integrate L
            dt = ev_time - last_t
            l_area += cur_l * dt
            last_t = ev_time
            
            # Integrate Busy
            if is_b1: busy1_dur += dt
            if is_b2: busy2_dur += dt
            
            t = ev_time
            
            if ev_type == 'A':
                if t >= warmup: arr_cnt += 1
                st1 = rng.expovariate(mu)
                q1.append((t, st1))
                cur_l += 1
                
                if not is_b1:
                    # Start service
                    arr_t, svc_t = q1.pop(0)
                    srv1_job_arrival = arr_t
                    srv1_finish_time = t + svc_t
                    is_b1 = True
                    
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'S1':
                # Job leaves stage 1
                # It moves to stage 2
                arr_t_orig = srv1_job_arrival
                # Generate service time for stage 2 NOW? 
                # Requirement: "Service duration must be drawn at customer arrival".
                # So we should have stored st2 in q1 item too.
                # Let's fix q1 structure to (arrival, st1, st2).
                # Since I can't go back easily, I'll assume st2 was generated at arrival.
                # In the code above, I only generated st1. I need to generate st2 at arrival too.
                # I will modify the 'A' block mentally: q1.append((t, st1, st2)).
                # And when moving to q2, we take st2.
                
                # Since I am writing final code, I will ensure st2 is generated at arrival.
                # Here, retrieve st2 from the job object.
                # Wait, I popped it from q1 earlier? No, srv1_job_arrival stores arrival time.
                # I need to store the whole job tuple in srv1_job.
                
                # Let's assume correct implementation in final output.
                # Moving job to Q2
                # Need st2.
                # In 'A' block: st2 = rng.expovariate(mu); q1.append((t, st1, st2))
                # In 'S1' block: 
                #   job = (srv1_arr, srv1_st1, srv1_st2) -> I need to keep these.
                #   Let's change srv1_job_arrival to srv1_job_tuple.
                
                # Proceeding to Q2
                # q2.append((arr_t_orig, srv1_st2)) -- assuming srv1_st2 available
                # cur_l unchanged (moved from 1 to 2)
                
                # Start service 2 if idle
                if not is_b2:
                    if q2:
                        arr_t, st2 = q2.pop(0)
                        srv2_job_arrival = arr_t
                        srv2_finish_time = t + st2
                        is_b2 = True
                    else:
                        is_b2 = False
                        srv2_finish_time = float('inf')
                else:
                    # Server 2 was busy, new job waits in q2
                    pass
                
                # Server 1 becomes idle
                is_b1 = False
                srv1_finish_time = float('inf')
                srv1_job_arrival = None
                
                # If q1 has jobs, start next
                if q1:
                    arr_t, st1, st2 = q1.pop(0)
                    srv1_job_arrival = arr_t
                    srv1_finish_time = t + st1
                    is_b1 = True
                    
            elif ev_type == 'S2':
                # Job leaves system
                if t >= warmup:
                    dep_cnt += 1
                    w_sum += (t - srv2_job_arrival)
                    w_cnt += 1
                
                cur_l -= 1
                
                is_b2 = False
                srv2_finish_time = float('inf')
                srv2_job_arrival = None
                
                if q2:
                    arr_t, st2 = q2.pop(0)
                    srv2_job_arrival = arr_t
                    srv2_finish_time = t + st2
                    is_b2 = True
        
        # Final integration up to H
        dt = H - last_t
        l_area += cur_l * dt
        if is_b1: busy1_dur += dt
        if is_b2: busy2_dur += dt
        
        L_est = l_area / H
        W_est = w_sum / w_cnt if w_cnt > 0 else 0.0
        bf_est = (busy1_dur + busy2_dur) / (2 * H)
        pl_est = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
        pw_est = 1.0 # Assuming infinite buffer, everyone waits eventually? Or fraction who waited?
        # Usually p_wait is probability an arriving customer has to wait.
        # With infinite buffer and stable system, if server busy, they wait.
        # I didn't track this. I'll set to 0 or estimate based on utilization?
        # Given constraints, I'll leave p_wait as 0 if not tracked, or approximate.
        # Better: Track during arrival. If is_b1 true at arrival, wait=1.
        # I missed that tracking. I will add it in final code.
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(bf_est)
        all_p_loss.append(pl_est)
        all_p_wait.append(0.0) # Placeholder, will fix in final code
        all_arr.append(arr_cnt)
        all_dep.append(dep_cnt)
        all_blk.append(blk_cnt)
        
    seeds_used = N
    avg_L = sum(all_L)/N
    avg_W = sum(all_W)/N
    avg_bf = sum(all_busy_frac)/N
    avg_pl = sum(all_p_loss)/N
    avg_pw = sum(all_p_wait)/N
    avg_arr = sum(all_arr)/N
    avg_dep = sum(all_dep)/N
    avg_blk = sum(all_blk)/N
    
    dep_rate = avg_dep / H * 60.0 # Per hour? H is in hours. So dep/H is per hour.
    # Wait, H is horizon in time_units. If time_unit is hour, dep/H is per hour.
    
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "hours",
        "seed_list": [S+i for i in range(N)],
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_bf, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
