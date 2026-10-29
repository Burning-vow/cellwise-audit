import json, math, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    
    if a.pert == 'lam_up': lam = lam_base * 1.2
    elif a.pert == 'mu_up': mu = mu_base * 1.2
    elif a.pert == 'c_up': lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L_area = []
    all_W_sum = []
    all_arr_count = []
    all_dep_count = []
    all_blk_count = []
    all_busy1_time = []
    all_busy2_time = []
    all_p_loss = []
    all_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = 0 # queue length at station 1 (including service)
        q2 = 0 # queue length at station 2 (including service)
        busy1 = False
        busy2 = False
        
        # Event list: (time, type, data)
        # types: 'arr', 'dep1', 'dep2'
        events = []
        
        # Generate first arrival
        next_arr_t = rng.expovariate(lam)
        events.append((next_arr_t, 'arr', None))
        
        # Statistics accumulators for this seed
        L_area_integrand = 0.0
        last_L_area_time = 0.0
        W_total_sum = 0.0
        dep_count = 0
        arr_count = 0
        blk_count = 0
        busy1_duration = 0.0
        busy2_duration = 0.0
        last_busy1_time = 0.0
        last_busy2_time = 0.0
        
        # For area integration of L (total items in system)
        # We need to integrate (q1+q2) over time.
        # We update integrand when state changes.
        
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, data = events.pop(0)
            
            if curr_t > horizon: break
            
            # Update area integrals and busy times up to curr_t
            dt = curr_t - last_L_area_time
            if dt > 0:
                L_area_integrand += (q1 + q2) * dt
                if busy1: busy1_duration += dt
                if busy2: busy2_duration += dt
                last_L_area_time = curr_t
                
            # Process event
            if ev_type == 'arr':
                arr_count += 1
                # Check capacity? Problem says "queue", implies infinite buffer unless specified. 
                # But "blk" is requested. Usually Jackson networks have infinite buffers. 
                # If finite, it would be stated. Let's assume infinite buffer -> blk=0 always?
                # Or maybe "blk" refers to something else? 
                # Re-reading: "两道工序各自排队". No capacity limit mentioned.
                # However, output requires blk. If infinite, blk=0.
                # Let's assume infinite buffer.
                
                # Service time drawn now
                svc_time = rng.expovariate(mu)
                
                if not busy1:
                    busy1 = True
                    dep1_t = curr_t + svc_time
                    events.append((dep1_t, 'dep1', {'start': curr_t, 'end': dep1_t}))
                else:
                    q1 += 1
                    # Store arrival time and service time requirement? 
                    # Actually, we just need to know when they leave station 1.
                    # We can store the job info in a queue structure.
                    # Since we are using discrete events, let's maintain explicit queues.
                    pass
                
                # Schedule next arrival
                inter_arr = rng.expovariate(lam)
                events.append((curr_t + inter_arr, 'arr', None))
                
            elif ev_type == 'dep1':
                # Job leaves station 1
                # It was either being served or from queue?
                # Logic: When dep1 happens, if q1>0, start next immediately.
                # Else stop serving.
                
                # The job that finished service moves to station 2
                # We need its arrival time at station 1 to calculate W later?
                # Wait, W is total stay time.
                # We need to track individual jobs.
                # Let's refine the simulation logic to track jobs properly.
                pass

            elif ev_type == 'dep2':
                # Job leaves system
                dep_count += 1
                # Calculate W contribution
                # Need arrival time of this specific job.
                pass

        # This simple loop above is flawed because I didn't implement job tracking.
        # Let's rewrite with proper job objects/queues.
        
        # Reset for correct implementation
        rng = random.Random(seed)
        t = 0.0
        q1 = [] # List of dicts: {'arrival_time': ..., 'service_time': ...}
        q2 = [] # List of dicts: {'arrival_time': ..., 'service_time': ...}
        busy1 = False
        busy2 = False
        current_job1 = None
        current_job2 = None
        
        events = []
        next_arr_t = rng.expovariate(lam)
        events.append((next_arr_t, 'arr', None))
        
        L_area_integrand = 0.0
        last_L_area_time = 0.0
        W_total_sum = 0.0
        dep_count = 0
        arr_count = 0
        blk_count = 0
        busy1_duration = 0.0
        busy2_duration = 0.0
        
        # Helper to add to area integral
        def update_area(curr_t):
            nonlocal L_area_integrand, last_L_area_time, busy1_duration, busy2_duration
            dt = curr_t - last_L_area_time
            if dt > 0:
                # Number of items in system = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
                # Note: q1/q2 here represent WAITING only? Or including service?
                # Standard definition: Queue usually means waiting. System includes service.
                # Let's define q1 as waiting queue, busy1 indicates one in service.
                n_in_sys = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
                L_area_integrand += n_in_sys * dt
                if busy1: busy1_duration += dt
                if busy2: busy2_duration += dt
                last_L_area_time = curr_t

        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, data = events.pop(0)
            
            if curr_t > horizon: break
            
            update_area(curr_t)
            
            if ev_type == 'arr':
                arr_count += 1
                svc_time = rng.expovariate(mu)
                job = {'arrival_time': curr_t, 'service_time': svc_time}
                
                # Infinite buffer assumption
                if not busy1:
                    busy1 = True
                    current_job1 = job
                    dep1_t = curr_t + svc_time
                    events.append((dep1_t, 'dep1', current_job1))
                else:
                    q1.append(job)
                    
                inter_arr = rng.expovariate(lam)
                events.append((curr_t + inter_arr, 'arr', None))
                
            elif ev_type == 'dep1':
                # current_job1 finishes
                job = data
                # Move to station 2
                if not busy2:
                    busy2 = True
                    current_job2 = job
                    dep2_t = curr_t + job['service_time']
                    events.append((dep2_t, 'dep2', current_job2))
                else:
                    q2.append(job)
                
                # Start next from q1 if any
                if q1:
                    next_job = q1.pop(0)
                    current_job1 = next_job
                    dep1_t = curr_t + next_job['service_time']
                    events.append((dep1_t, 'dep1', current_job1))
                else:
                    busy1 = False
                    current_job1 = None
                    
            elif ev_type == 'dep2':
                job = data
                dep_count += 1
                w_i = curr_t - job['arrival_time']
                W_total_sum += w_i
                
                # Start next from q2 if any
                if q2:
                    next_job = q2.pop(0)
                    current_job2 = next_job
                    dep2_t = curr_t + next_job['service_time']
                    events.append((dep2_t, 'dep2', current_job2))
                else:
                    busy2 = False
                    current_job2 = None
        
        # Final update area to horizon? 
        # The loop breaks when curr_t > horizon. 
        # We should integrate up to horizon exactly.
        # But events might be scheduled beyond. 
        # Let's force an update at horizon if needed.
        if last_L_area_time < horizon:
             update_area(horizon)
             
        # Warmup removal
        # We integrated over [0, horizon]. We need [win_start, horizon].
        # This approach is tricky because we don't have history of L(t).
        # Better: Only accumulate stats after win_start.
        
        # RE-WRITING FOR CORRECT WARMUP HANDLING
        # Restart simulation for this seed with warmup logic
        
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        busy1 = False
        busy2 = False
        current_job1 = None
        current_job2 = None
        
        events = []
        next_arr_t = rng.expovariate(lam)
        events.append((next_arr_t, 'arr', None))
        
        L_area_integrand = 0.0
        last_L_area_time = 0.0
        W_total_sum = 0.0
        dep_count = 0
        arr_count = 0
        blk_count = 0
        busy1_duration = 0.0
        busy2_duration = 0.0
        
        # Stats only collected after win_start
        # We need to handle the transition at win_start carefully.
        # Simplest: Run until win_start without collecting, then collect.
        # But we need to ensure state is consistent.
        
        # Let's use a flag
        collecting = False
        
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, data = events.pop(0)
            
            if curr_t > horizon: break
            
            # Determine if we are in collection window
            # If we crossed win_start between last event and this one, we need to split integration.
            
            prev_collecting = collecting
            if curr_t >= win_start:
                collecting = True
            
            # Integrate area/busy from last_L_area_time to curr_t
            dt = curr_t - last_L_area_time
            if dt > 0:
                n_in_sys = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
                
                if prev_collecting:
                    # Entire interval is in window
                    L_area_integrand += n_in_sys * dt
                    if busy1: busy1_duration += dt
                    if busy2: busy2_duration += dt
                elif collecting:
                    # Interval crosses win_start
                    dt_pre = win_start - last_L_area_time
                    dt_post = curr_t - win_start
                    # Pre part ignored
                    # Post part counted
                    L_area_integrand += n_in_sys * dt_post
                    if busy1: busy1_duration += dt_post
                    if busy2: busy2_duration += dt_post
                # Else: neither pre nor post, ignore entirely (all before win_start)
                
                last_L_area_time = curr_t

            if ev_type == 'arr':
                if collecting: arr_count += 1
                svc_time = rng.expovariate(mu)
                job = {'arrival_time': curr_t, 'service_time': svc_time}
                
                if not busy1:
                    busy1 = True
                    current_job1 = job
                    dep1_t = curr_t + svc_time
                    events.append((dep1_t, 'dep1', current_job1))
                else:
                    q1.append(job)
                    
                inter_arr = rng.expovariate(lam)
                events.append((curr_t + inter_arr, 'arr', None))
                
            elif ev_type == 'dep1':
                job = data
                if not busy2:
                    busy2 = True
                    current_job2 = job
                    dep2_t = curr_t + job['service_time']
                    events.append((dep2_t, 'dep2', current_job2))
                else:
                    q2.append(job)
                
                if q1:
                    next_job = q1.pop(0)
                    current_job1 = next_job
                    dep1_t = curr_t + next_job['service_time']
                    events.append((dep1_t, 'dep1', current_job1))
                else:
                    busy1 = False
                    current_job1 = None
                    
            elif ev_type == 'dep2':
                job = data
                if collecting:
                    dep_count += 1
                    w_i = curr_t - job['arrival_time']
                    W_total_sum += w_i
                
                if q2:
                    next_job = q2.pop(0)
                    current_job2 = next_job
                    dep2_t = curr_t + next_job['service_time']
                    events.append((dep2_t, 'dep2', current_job2))
                else:
                    busy2 = False
                    current_job2 = None

        # Handle final segment to horizon if needed
        if last_L_area_time < horizon:
            dt = horizon - last_L_area_time
            n_in_sys = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
            if collecting:
                L_area_integrand += n_in_sys * dt
                if busy1: busy1_duration += dt
                if busy2: busy2_duration += dt

        # Per-seed estimates
        est_L = L_area_integrand / win_len if win_len > 0 else 0
        est_W = W_total_sum / dep_count if dep_count > 0 else 0
        est_busy_frac = (busy1_duration + busy2_duration) / (2 * win_len) if win_len > 0 else 0
        est_p_loss = blk_count / arr_count if arr_count > 0 else 0
        # p_wait: fraction of arrivals who waited? 
        # Hard to track exactly without more state. 
        # Approximation: P(wait) = rho^2 / (1-rho) for M/M/1? 
        # Or count how many arrived to busy server.
        # Let's re-run quickly or modify loop to count waits.
        # Modifying loop is better.
        
        # Re-running with wait counting
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        busy1 = False
        busy2 = False
        current_job1 = None
        current_job2 = None
        events = []
        next_arr_t = rng.expovariate(lam)
        events.append((next_arr_t, 'arr', None))
        
        L_area_integrand = 0.0
        last_L_area_time = 0.0
        W_total_sum = 0.0
        dep_count = 0
        arr_count = 0
        blk_count = 0
        busy1_duration = 0.0
        busy2_duration = 0.0
        wait_count = 0 # Arrivals that found server busy
        
        collecting = False
        
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, data = events.pop(0)
            if curr_t > horizon: break
            
            prev_collecting = collecting
            if curr_t >= win_start: collecting = True
            
            dt = curr_t - last_L_area_time
            if dt > 0:
                n_in_sys = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
                if prev_collecting:
                    L_area_integrand += n_in_sys * dt
                    if busy1: busy1_duration += dt
                    if busy2: busy2_duration += dt
                elif collecting:
                    dt_post = curr_t - win_start
                    L_area_integrand += n_in_sys * dt_post
                    if busy1: busy1_duration += dt_post
                    if busy2: busy2_duration += dt_post
                last_L_area_time = curr_t

            if ev_type == 'arr':
                if collecting: 
                    arr_count += 1
                    if busy1: wait_count += 1
                svc_time = rng.expovariate(mu)
                job = {'arrival_time': curr_t, 'service_time': svc_time}
                if not busy1:
                    busy1 = True
                    current_job1 = job
                    events.append((curr_t + svc_time, 'dep1', current_job1))
                else:
                    q1.append(job)
                events.append((curr_t + rng.expovariate(lam), 'arr', None))
                
            elif ev_type == 'dep1':
                job = data
                if not busy2:
                    busy2 = True
                    current_job2 = job
                    events.append((curr_t + job['service_time'], 'dep2', current_job2))
                else:
                    q2.append(job)
                if q1:
                    nj = q1.pop(0)
                    current_job1 = nj
                    events.append((curr_t + nj['service_time'], 'dep1', current_job1))
                else:
                    busy1 = False
                    current_job1 = None
                    
            elif ev_type == 'dep2':
                job = data
                if collecting:
                    dep_count += 1
                    W_total_sum += curr_t - job['arrival_time']
                if q2:
                    nj = q2.pop(0)
                    current_job2 = nj
                    events.append((curr_t + nj['service_time'], 'dep2', current_job2))
                else:
                    busy2 = False
                    current_job2 = None

        if last_L_area_time < horizon:
            dt = horizon - last_L_area_time
            n_in_sys = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
            if collecting:
                L_area_integrand += n_in_sys * dt
                if busy1: busy1_duration += dt
                if busy2: busy2_duration += dt

        per_seed_L = L_area_integrand / win_len
        per_seed_W = W_total_sum / dep_count if dep_count > 0 else 0
        per_seed_busy_frac = (busy1_duration + busy2_duration) / (2 * win_len)
        per_seed_p_loss = blk_count / arr_count if arr_count > 0 else 0
        per_seed_p_wait = wait_count / arr_count if arr_count > 0 else 0
        
        all_L_area.append(L_area_integrand)
        all_W_sum.append(W_total_sum)
        all_arr_count.append(arr_count)
        all_dep_count.append(dep_count)
        all_blk_count.append(blk_count)
        all_busy1_time.append(busy1_duration)
        all_busy2_time.append(busy2_duration)
        all_p_loss.append(per_seed_p_loss)
        all_p_wait.append(per_seed_p_wait)

    # Aggregate
    avg_L = sum(all_L_area) / (seeds_used * win_len)
    total_W_sum = sum(all_W_sum)
    total_dep = sum(all_dep_count)
    avg_W = total_W_sum / total_dep if total_dep > 0 else 0
    
    avg_arr = sum(all_arr_count) / seeds_used
    avg_dep = sum(all_dep_count) / seeds_used
    avg_blk = sum(all_blk_count) / seeds_used
    avg_busy_frac = sum(b1+b2 for b1,b2 in zip(all_busy1_time, all_busy2_time)) / (2 * seeds_used * win_len)
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    
    dep_rate = avg_dep / (win_len / 60.0) # Convert minutes to hours? 
    # Time unit is minute. Horizon is in minutes? 
    # Prompt: "H 是整数样式的仿真时域长度，单位与你自报的 time_unit 一致"
    # I set time_unit = 'minute'.
    # Lam is per hour. So I converted lam to per minute? 
    # In code: rng.expovariate(lam). If lam=6/hr, and time is min, rate should be 6/60 = 0.1/min.
    # I used lam=6.0 directly. This assumes time unit is HOUR.
    # Let's check: "平均 6 分钟". mu = 10/hr.
    # If I use time_unit='hour', then H=100 means 100 hours.
    # Let's stick to time_unit='hour' to match lam/mu definitions easily.
    
    # Correction: Set time_unit = 'hour'
    # Then win_len is in hours.
    # dep_rate = avg_dep / win_len (per hour)
    
    dep_rate_val = avg_dep / win_len if win_len > 0 else 0
    lam_eff = avg_arr / win_len if win_len > 0 else 0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W * 60, 4), # W in minutes. If time_unit is hour, W calculated in hours. Multiply by 60.
        "runtime_units": "simulation steps",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x/win_len, 4) for x in all_L_area],
        "per_seed_W": [round((s/d)*60, 4) if d>0 else 0 for s,d in zip(all_W_sum, all_dep_count)],
        "per_seed_busy_frac": [round((b1+b2)/(2*win_len), 4) for b1,b2 in zip(all_busy1_time, all_busy2_time)],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
