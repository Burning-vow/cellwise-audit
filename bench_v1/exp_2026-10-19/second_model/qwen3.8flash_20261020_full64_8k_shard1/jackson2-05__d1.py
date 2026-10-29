import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = float(args.horizon)
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 6.0 / 60.0  # arrivals per minute (6 per hour)
    mu1_base = 1.0 / 7.5   # service rate stage 1 per minute
    mu2_base = 1.0 / 6.0   # service rate stage 2 per minute

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        # Cost perturbation doesn't change dynamics for L/W, but we keep structure same
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base

    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    # Warmup fraction
    warmup_frac = 0.25
    warmup_time = horizon_min * warmup_frac
    stat_window_len = horizon_min - warmup_time

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seed_list = []

    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        # Queues: list of dicts {id, arrival_time, service_time}
        q1 = []
        q2 = []
        # Server states: None or dict {id, start_time, end_time}
        srv1 = None
        srv2 = None
        
        # Statistics accumulators (for area integration)
        # We need to integrate number in system over time
        # But standard DES usually tracks events. 
        # To get L (average number in system), we can use Little's Law W*L? No, we want direct estimate.
        # Let's track "area under curve" for number in system.
        # However, implementing continuous integration in discrete event simulation requires careful handling of state changes.
        # Alternative: Use the fact that L = lambda_eff * W. But the prompt asks for L and W separately.
        # Prompt says: "面积型量必须在改变状态之前积分". This implies we should compute integrals.
        
        # Let's maintain:
        # last_event_time
        # current_num_in_system (N_sys)
        # integral_N_sys (sum of N_sys * dt)
        # total_service_time_sum (for W calculation via sum of sojourn times)
        # count_completed (for W denominator)
        # count_arrivals (in window)
        # count_departures (in window)
        # count_blocked/lost (if any capacity limit? Problem says "各自排队", no explicit capacity limit mentioned, so blk=0 likely unless infinite queue is not allowed. Standard Jackson network has infinite queues. So p_loss=0.)
        
        # Wait, "blk" is rejected/lost. If queues are infinite, blk=0.
        
        # Event types: Arrival, ServiceEnd1, ServiceEnd2
        
        # Initialize first arrival
        next_arrival = rng.expovariate(lam)
        
        # Stats for this run
        num_in_sys = 0
        integral_num_in_sys = 0.0
        last_t = 0.0
        
        total_sojourn_time = 0.0
        completed_count = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        busy1_time = 0.0
        busy2_time = 0.0
        
        # We need to handle the warmup period correctly.
        # The problem says: "统计量只在去掉前 25% 预热后的窗口内累计".
        # This means we simulate up to horizon, but only accumulate stats after warmup_time.
        # For area-based L, we need to integrate from warmup_time to horizon.
        # For W, we need to average sojourn times of jobs that *complete* within the window? Or jobs that arrive within the window?
        # Usually, for steady-state estimation, we take jobs that complete in the window.
        # Let's assume:
        # L: Average number in system during [warmup, horizon].
        # W: Average sojourn time of jobs completing during [warmup, horizon].
        
        # To do this properly with discrete events:
        # We process events until t >= horizon.
        # When an event occurs at time t_ev:
        # 1. Update integrals for interval [last_t, min(t_ev, horizon)] considering warmup.
        # 2. Process event.
        # 3. Update last_t = t_ev.
        
        # Helper to add to integral
        def update_integrals(current_t, prev_t, n_sys, b1, b2):
            nonlocal integral_num_in_sys, busy1_time, busy2_time
            
            # Determine overlap with statistical window [warmup_time, horizon]
            win_start = max(prev_t, warmup_time)
            win_end = min(current_t, horizon_min)
            
            if win_start < win_end:
                dt = win_end - win_start
                integral_num_in_sys += n_sys * dt
                if b1: busy1_time += dt
                if b2: busy2_time += dt

        # Initial state
        # At t=0, num_in_sys=0, servers idle.
        
        while t < horizon_min:
            # Find next event time
            candidates = []
            if next_arrival < horizon_min:
                candidates.append(('arr', next_arrival))
            if srv1 is not None:
                candidates.append(('end1', srv1['end_time']))
            if srv2 is not None:
                candidates.append(('end2', srv2['end_time']))
            
            if not candidates:
                break
                
            evt_type, evt_time = min(candidates, key=lambda x: x[1])
            
            # Update integrals up to evt_time
            # Note: num_in_sys, srv1, srv2 reflect state BEFORE this event
            update_integrals(evt_time, t, num_in_sys, srv1 is not None, srv2 is not None)
            
            t = evt_time
            
            if evt_type == 'arr':
                # Job arrives
                # Generate service times now
                s1 = rng.expovariate(mu1)
                s2 = rng.expovariate(mu2)
                
                job = {'id': len(q1)+len(q2)+(1 if srv1 else 0)+(1 if srv2 else 0), 's1': s1, 's2': s2, 'arrival': t}
                
                # Check if server 1 is free
                if srv1 is None:
                    srv1 = {'job': job, 'start': t, 'end': t + s1}
                else:
                    q1.append(job)
                
                num_in_sys += 1
                
                # Count arrival if in window
                if t >= warmup_time:
                    arr_count_win += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif evt_type == 'end1':
                # Job finishes stage 1
                job = srv1['job']
                srv1 = None
                
                # Move to stage 2
                if srv2 is None:
                    srv2 = {'job': job, 'start': t, 'end': t + job['s2']}
                else:
                    q2.append(job)
                
                # Start next job on server 1 if available
                if q1:
                    next_job = q1.pop(0)
                    srv1 = {'job': next_job, 'start': t, 'end': t + next_job['s1']}
                
                # num_in_sys remains same (moved from srv1 to srv2/q2)
                
            elif evt_type == 'end2':
                # Job leaves system
                job = srv2['job']
                srv2 = None
                
                sojourn = t - job['arrival']
                
                # Count departure if in window
                if t >= warmup_time:
                    dep_count_win += 1
                    total_sojourn_time += sojourn
                    completed_count += 1
                
                num_in_sys -= 1
                
                # Start next job on server 2 if available
                if q2:
                    next_job = q2.pop(0)
                    srv2 = {'job': next_job, 'start': t, 'end': t + next_job['s2']}

        # Final update for remaining time if loop broke early? 
        # Loop condition t < horizon_min ensures we process events up to horizon.
        # But if no more events before horizon, we need to integrate the last segment.
        if t < horizon_min:
             update_integrals(horizon_min, t, num_in_sys, srv1 is not None, srv2 is not None)
             t = horizon_min

        # Calculate metrics for this seed
        # L = Integral / Window Length
        if stat_window_len > 0:
            L_est = integral_num_in_sys / stat_window_len
        else:
            L_est = 0.0
            
        # W = Total Sojourn Time / Completed Count
        if completed_count > 0:
            W_est = total_sojourn_time / completed_count
        else:
            W_est = 0.0
            
        # Busy fractions
        bf1 = busy1_time / stat_window_len if stat_window_len > 0 else 0.0
        bf2 = busy2_time / stat_window_len if stat_window_len > 0 else 0.0
        # Combined busy frac? Usually per server. The prompt asks for busy_frac. 
        # Given two servers, maybe average utilization? Or sum? 
        # "busy_util" might be overall system utilization? 
        # Let's report average of the two servers' utilizations as busy_frac? 
        # Or maybe it refers to a single bottleneck? 
        # In Jackson networks, often we look at individual stations. 
        # The output key is singular "busy_frac". 
        # Let's assume it's the average utilization across both servers.
        busy_frac_est = (bf1 + bf2) / 2.0
        
        # p_loss: Since queues are infinite, loss is 0.
        p_loss_est = 0.0
        
        # p_wait: Probability that an arriving job has to wait?
        # We didn't track this directly. 
        # Approximation: Fraction of time server 1 is busy? 
        # P(wait at 1) = rho1. P(wait at 2) = rho2.
        # Overall p_wait? Maybe probability that a job waits at ANY stage?
        # Or just stage 1? 
        # Let's calculate empirical: Did the job enter queue immediately?
        # We didn't store this flag. 
        # Re-evaluating: We can approximate p_wait using utilization.
        # For M/M/1, P(wait) = rho.
        # Here we have two stages. 
        # Let's define p_wait as the fraction of jobs that waited at least once.
        # We need to track this.
        
        # Correction: I need to track waiting status.
        # Let's restart the logic slightly to include wait tracking.
        
        # Actually, let's re-run the simulation logic mentally to ensure correctness.
        # I will rewrite the inner loop to capture 'waited' flag.
        
        pass 

    # Since I cannot easily patch the code above without rewriting, I will provide the corrected full code below.
    # The previous block was a draft. I will generate the final clean version.
    
    # Resetting to write the actual solution code
    
    results_L = []
    results_W = []
    results_bf = []
    results_pl = []
    results_pw = []
    results_arr = []
    results_dep = []
    results_blk = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        q1 = []
        q2 = []
        srv1 = None
        srv2 = None
        
        num_in_sys = 0
        integral_num_in_sys = 0.0
        last_t = 0.0
        
        total_sojourn_time = 0.0
        completed_count = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        busy1_time = 0.0
        busy2_time = 0.0
        
        wait_count_win = 0 # Jobs that waited at least once
        
        next_arrival = rng.expovariate(lam)
        
        while t < horizon_min:
            candidates = []
            if next_arrival < horizon_min:
                candidates.append(('arr', next_arrival))
            if srv1 is not None:
                candidates.append(('end1', srv1['end_time']))
            if srv2 is not None:
                candidates.append(('end2', srv2['end_time']))
            
            if not candidates:
                break
                
            evt_type, evt_time = min(candidates, key=lambda x: x[1])
            
            # Integrate
            win_start = max(last_t, warmup_time)
            win_end = min(evt_time, horizon_min)
            if win_start < win_end:
                dt = win_end - win_start
                integral_num_in_sys += num_in_sys * dt
                if srv1 is not None: busy1_time += dt
                if srv2 is not None: busy2_time += dt
            
            t = evt_time
            last_t = evt_time
            
            if evt_type == 'arr':
                s1 = rng.expovariate(mu1)
                s2 = rng.expovariate(mu2)
                job = {'s1': s1, 's2': s2, 'arrival': t, 'waited': False}
                
                if srv1 is None:
                    srv1 = {'job': job, 'start': t, 'end': t + s1}
                else:
                    q1.append(job)
                    job['waited'] = True
                
                num_in_sys += 1
                
                if t >= warmup_time:
                    arr_count_win += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif evt_type == 'end1':
                job = srv1['job']
                srv1 = None
                
                if srv2 is None:
                    srv2 = {'job': job, 'start': t, 'end': t + job['s2']}
                else:
                    q2.append(job)
                    job['waited'] = True
                
                if q1:
                    next_job = q1.pop(0)
                    srv1 = {'job': next_job, 'start': t, 'end': t + next_job['s1']}
                    
            elif evt_type == 'end2':
                job = srv2['job']
                srv2 = None
                
                sojourn = t - job['arrival']
                
                if t >= warmup_time:
                    dep_count_win += 1
                    total_sojourn_time += sojourn
                    completed_count += 1
                    if job['waited']:
                        wait_count_win += 1
                
                num_in_sys -= 1
                
                if q2:
                    next_job = q2.pop(0)
                    srv2 = {'job': next_job, 'start': t, 'end': t + next_job['s2']}

        if t < horizon_min:
            win_start = max(last_t, warmup_time)
            win_end = horizon_min
            if win_start < win_end:
                dt = win_end - win_start
                integral_num_in_sys += num_in_sys * dt
                if srv1 is not None: busy1_time += dt
                if srv2 is not None: busy2_time += dt

        L_est = integral_num_in_sys / stat_window_len if stat_window_len > 0 else 0.0
        W_est = total_sojourn_time / completed_count if completed_count > 0 else 0.0
        bf_est = ((busy1_time + busy2_time) / 2.0) / stat_window_len if stat_window_len > 0 else 0.0
        pl_est = 0.0
        pw_est = wait_count_win / arr_count_win if arr_count_win > 0 else 0.0
        
        results_L.append(L_est)
        results_W.append(W_est)
        results_bf.append(bf_est)
        results_pl.append(pl_est)
        results_pw.append(pw_est)
        results_arr.append(arr_count_win)
        results_dep.append(dep_count_win)
        results_blk.append(blk_count_win)
        seed_list.append(seed)

    avg_L = sum(results_L) / N
    avg_W = sum(results_W) / N
    avg_bf = sum(results_bf) / N
    avg_pl = sum(results_pl) / N
    avg_pw = sum(results_pw) / N
    avg_arr = sum(results_arr) / N
    avg_dep = sum(results_dep) / N
    avg_blk = sum(results_blk) / N
    
    # dep_rate in per hour
    # avg_dep is count in window. Window length in minutes.
    # Rate = (avg_dep / stat_window_len) * 60
    dep_rate = (avg_dep / stat_window_len) * 60 if stat_window_len > 0 else 0.0
    lam_eff = dep_rate / 60.0 # per minute? No, dep_rate is per hour. 
    # Let's stick to consistent units. 
    # dep_rate requested as "个/每小时".
    # lam_eff: effective arrival rate. Should match dep_rate if stable.
    # Let's calculate lam_eff as avg_arr / stat_window_len * 60
    lam_eff = (avg_arr / stat_window_len) * 60 if stat_window_len > 0 else 0.0

    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "minutes",
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(stat_window_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_bf, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in results_L],
        "per_seed_W": [round(x, 4) for x in results_W],
        "per_seed_busy_frac": [round(x, 4) for x in results_bf],
        "per_seed_p_loss": [round(x, 4) for x in results_pl],
        "per_seed_p_wait": [round(x, 4) for x in results_pw]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
