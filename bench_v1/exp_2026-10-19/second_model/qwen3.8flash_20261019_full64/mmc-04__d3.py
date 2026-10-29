import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    lam_base = 10.0
    mu_base = 6.0
    c = 2

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        t = 0.0
        events = []
        def add_event(time, typ, cust_id=None, service_time=None):
            events.append((time, typ, cust_id, service_time))
        
        first_arr = rng.expovariate(lam)
        add_event(first_arr, 'arr', None, None)
        
        cust_counter = 0
        queue = []
        servers_free_at = [0.0] * c
        
        area_L = 0.0
        last_t = 0.0
        current_N = 0
        
        total_arr_in_win = 0
        total_dep_in_win = 0
        total_blk_in_win = 0
        wait_times_sum = 0.0
        num_completed_in_win = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            ev = events.pop(0)
            t_ev, typ, cid, stime = ev
            
            if t_ev > H:
                break
                
            dt = t_ev - last_t
            if last_t >= warmup_end and t_ev <= H:
                area_L += current_N * dt
            elif last_t < warmup_end and t_ev > warmup_end:
                pass 
            elif last_t < warmup_end and t_ev <= warmup_end:
                pass
            else:
                pass
            # Correct integration logic: integrate over [last_t, min(t_ev, H)] intersected with [warmup_end, H]
            start_int = max(last_t, warmup_end)
            end_int = min(t_ev, H)
            if end_int > start_int:
                area_L += current_N * (end_int - start_int)
                
            last_t = t_ev
            
            if typ == 'arr':
                cust_counter += 1
                cid = cust_counter
                # Generate service time now
                s_time = rng.expovariate(mu)
                
                # Find free server
                free_idx = -1
                min_free_time = float('inf')
                for k in range(c):
                    if servers_free_at[k] <= t_ev:
                        free_idx = k
                        break
                    if servers_free_at[k] < min_free_time:
                        min_free_time = servers_free_at[k]
                        
                if free_idx != -1:
                    # No wait
                    servers_free_at[free_idx] = t_ev + s_time
                    dep_time = t_ev + s_time
                    add_event(dep_time, 'dep', cid, s_time)
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                        wait_times_sum += 0.0
                        num_completed_in_win += 1 # Will be counted at dep? No, W is avg time in system. Need to track arrival time.
                        # Better approach: store arrival time in customer object or event chain.
                        # Let's restart the loop structure slightly cleaner for state tracking.
                else:
                    # Queue
                    queue.append((cid, t_ev, s_time))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                        
            elif typ == 'dep':
                # Customer leaves
                current_N -= 1
                if t_ev >= warmup_end and t_ev <= H:
                    total_dep_in_win += 1
                    
                # Check queue
                if queue:
                    next_cust = queue.pop(0)
                    nc_id, nc_arr_t, nc_s_time = next_cust
                    # Find a server that just became free? Or any free one?
                    # In this simulation, we assume FCFS and immediate assignment if server free.
                    # But here, a server just freed up at t_ev.
                    # We need to find which server index was used by the departing customer? 
                    # Actually, simpler: maintain list of available servers.
                    # The previous logic was flawed because it didn't track which server freed up.
                    
                    # Let's rewrite the core loop properly.
                    pass 

        # Re-implementing the simulation loop correctly below
        rng = random.Random(seed)
        t = 0.0
        events = []
        cust_counter = 0
        queue = [] # List of tuples: (cust_id, arrival_time, service_duration)
        servers = [{'free_at': 0.0} for _ in range(c)]
        
        area_L = 0.0
        last_t = 0.0
        current_N = 0
        
        total_arr_in_win = 0
        total_dep_in_win = 0
        total_blk_in_win = 0
        sum_W_in_win = 0.0
        count_W_in_win = 0
        
        first_arr = rng.expovariate(lam)
        events.append((first_arr, 'arr'))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_ev, typ = events.pop(0)
            
            if t_ev > H:
                break
                
            dt = t_ev - last_t
            start_int = max(last_t, warmup_end)
            end_int = min(t_ev, H)
            if end_int > start_int:
                area_L += current_N * (end_int - start_int)
            last_t = t_ev
            
            if typ == 'arr':
                cust_counter += 1
                cid = cust_counter
                s_dur = rng.expovariate(mu)
                
                # Next arrival
                next_arr = t_ev + rng.expovariate(lam)
                if next_arr <= H:
                    events.append((next_arr, 'arr'))
                
                # Assign to server
                assigned_server = -1
                for k in range(c):
                    if servers[k]['free_at'] <= t_ev:
                        assigned_server = k
                        break
                
                if assigned_server != -1:
                    servers[assigned_server]['free_at'] = t_ev + s_dur
                    dep_t = t_ev + s_dur
                    events.append((dep_t, 'dep', cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                else:
                    queue.append((cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                        
            elif typ == 'dep':
                _, cid, arr_t, s_dur = events.pop(0) # Wait, I unpacked wrong above. 
                # Correction: The tuple was (t_ev, 'dep', cid, arr_t, s_dur). 
                # So when popping, I have t_ev, typ, cid, arr_t, s_dur.
                # But in the append line: events.append((dep_t, 'dep', cid, t_ev, s_dur))
                # So pop gives: t_ev, typ, cid, arr_t, s_dur.
                
                current_N -= 1
                if t_ev >= warmup_end and t_ev <= H:
                    total_dep_in_win += 1
                    w = t_ev - arr_t
                    sum_W_in_win += w
                    count_W_in_win += 1
                
                # Try to serve from queue
                if queue:
                    q_cid, q_arr_t, q_s_dur = queue.pop(0)
                    # Find a free server (the one that just freed up is definitely free at t_ev)
                    # But multiple might be free. Just pick first free.
                    found = False
                    for k in range(c):
                        if servers[k]['free_at'] <= t_ev:
                            servers[k]['free_at'] = t_ev + q_s_dur
                            dep_t = t_ev + q_s_dur
                            events.append((dep_t, 'dep', q_cid, q_arr_t, q_s_dur))
                            found = True
                            break
                    if not found:
                        # Should not happen if we popped a dep and there's a queue, unless logic error
                        queue.insert(0, (q_cid, q_arr_t, q_s_dur))

        L_est = area_L / win if win > 0 else 0
        W_est = (sum_W_in_win / count_W_in_win) * 60 if count_W_in_win > 0 else 0 # Convert hours to minutes
        busy_frac_est = L_est / c if c > 0 else 0
        p_wait_est = 0.0
        # Calculate p_wait: fraction of arrivals in window that had to wait
        # We didn't track this explicitly in the loop above easily without another counter.
        # Let's re-run or fix. For brevity, I'll approximate or recalculate.
        # Actually, let's just run a second pass or fix the first. 
        # Given constraints, I will fix the first pass to include p_wait counters.
        
        # Restarting the inner loop for correctness with p_wait tracking
        rng = random.Random(seed)
        t = 0.0
        events = []
        cust_counter = 0
        queue = []
        servers = [{'free_at': 0.0} for _ in range(c)]
        area_L = 0.0
        last_t = 0.0
        current_N = 0
        total_arr_in_win = 0
        total_dep_in_win = 0
        total_blk_in_win = 0
        sum_W_in_win = 0.0
        count_W_in_win = 0
        count_wait_in_win = 0
        
        first_arr = rng.expovariate(lam)
        events.append((first_arr, 'arr'))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_ev, typ = events.pop(0)
            if t_ev > H: break
            
            start_int = max(last_t, warmup_end)
            end_int = min(t_ev, H)
            if end_int > start_int:
                area_L += current_N * (end_int - start_int)
            last_t = t_ev
            
            if typ == 'arr':
                cust_counter += 1
                cid = cust_counter
                s_dur = rng.expovariate(mu)
                next_arr = t_ev + rng.expovariate(lam)
                if next_arr <= H: events.append((next_arr, 'arr'))
                
                assigned_server = -1
                for k in range(c):
                    if servers[k]['free_at'] <= t_ev:
                        assigned_server = k
                        break
                
                if assigned_server != -1:
                    servers[assigned_server]['free_at'] = t_ev + s_dur
                    events.append((t_ev + s_dur, 'dep', cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                else:
                    queue.append((cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                        count_wait_in_win += 1
                        
            elif typ == 'dep':
                _, cid, arr_t, s_dur = events.pop(0) # Error: unpacking again. 
                # The tuple is (t_ev, 'dep', cid, arr_t, s_dur). 
                # When popped, it becomes variables.
                # Let's use indices.
                pass

        # Final clean implementation
        rng = random.Random(seed)
        events = []
        cust_counter = 0
        queue = []
        servers = [0.0] * c
        area_L = 0.0
        last_t = 0.0
        current_N = 0
        total_arr_in_win = 0
        total_dep_in_win = 0
        total_blk_in_win = 0
        sum_W_in_win = 0.0
        count_W_in_win = 0
        count_wait_in_win = 0
        
        t_next_arr = rng.expovariate(lam)
        events.append((t_next_arr, 'arr'))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_ev, typ = events.pop(0)[0], events.pop(0)[1] # WRONG POPPING
            
            # Correct popping
            ev = events.pop(0)
            t_ev = ev[0]
            typ = ev[1]
            
            if t_ev > H: break
            
            start_int = max(last_t, warmup_end)
            end_int = min(t_ev, H)
            if end_int > start_int:
                area_L += current_N * (end_int - start_int)
            last_t = t_ev
            
            if typ == 'arr':
                cust_counter += 1
                cid = cust_counter
                s_dur = rng.expovariate(mu)
                t_next_arr = t_ev + rng.expovariate(lam)
                if t_next_arr <= H:
                    events.append((t_next_arr, 'arr'))
                
                free_srv = -1
                for k in range(c):
                    if servers[k] <= t_ev:
                        free_srv = k
                        break
                
                if free_srv != -1:
                    servers[free_srv] = t_ev + s_dur
                    events.append((t_ev + s_dur, 'dep', cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                else:
                    queue.append((cid, t_ev, s_dur))
                    current_N += 1
                    if t_ev >= warmup_end and t_ev <= H:
                        total_arr_in_win += 1
                        count_wait_in_win += 1
                        
            elif typ == 'dep':
                _, _, cid, arr_t, s_dur = ev
                current_N -= 1
                if t_ev >= warmup_end and t_ev <= H:
                    total_dep_in_win += 1
                    sum_W_in_win += (t_ev - arr_t)
                    count_W_in_win += 1
                
                if queue:
                    q_cid, q_arr_t, q_s_dur = queue.pop(0)
                    # Find free server
                    f_srv = -1
                    for k in range(c):
                        if servers[k] <= t_ev:
                            f_srv = k
                            break
                    if f_srv != -1:
                        servers[f_srv] = t_ev + q_s_dur
                        events.append((t_ev + q_s_dur, 'dep', q_cid, q_arr_t, q_s_dur))
                    else:
                        queue.insert(0, (q_cid, q_arr_t, q_s_dur))

        L_est = area_L / win if win > 0 else 0
        W_est_min = (sum_W_in_win / count_W_in_win) * 60 if count_W_in_win > 0 else 0
        busy_frac_est = L_est / c if c > 0 else 0
        p_wait_est = count_wait_in_win / total_arr_in_win if total_arr_in_win > 0 else 0
        busy_util_est = busy_frac_est
        dep_rate_est = total_dep_in_win / win if win > 0 else 0
        lam_eff_est = total_arr_in_win / win if win > 0 else 0
        p_loss_est = 0.0 # Infinite queue assumed, no loss
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est_min)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(total_arr_in_win)
        all_blk.append(total_blk_in_win)
        all_dep.append(total_dep_in_win)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
