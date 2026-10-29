import sys, json, random, argparse
from collections import deque

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in minutes
    lam_base = 4.0 / 60.0  # arrivals per minute
    mu1_base = 1.0 / 6.0   # service rate stage 1 per minute
    mu2_base = 1.0 / 5.0   # service rate stage 2 per minute
    
    if pert == 'lam_up': lam_base *= 1.1
    elif pert == 'mu_up': mu1_base *= 1.1; mu2_base *= 1.1
    elif pert == 'c_up': pass # capacity not explicitly defined as variable in prompt, assume no change or ignore
    
    time_unit = "minute"
    horizon_min = H * 60.0 if time_unit == "hour" else H # Prompt says H unit matches time_unit. If I choose minute, H is minutes. Let's stick to internal minute clock.
    # Re-reading: "H 是整数样式的仿真时域长度，单位与你自报的 time_unit 一致". 
    # If I report time_unit="minute", then H is minutes.
    # Default H=100.0 -> 100 minutes? Or 100 hours? Usually simulation horizons are larger. 
    # Let's assume the user passes H in the chosen unit. I will choose "minute" for internal consistency with rates.
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_busy_time_1 = 0.0
    total_busy_time_2 = 0.0
    total_wait_count = 0 # For p_wait approximation: fraction of jobs that waited? Or average wait prob? Usually P(wait) is prob an arrival waits.
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []
    
    warmup_ratio = 0.25
    warmup_end = horizon_min * (1 - warmup_ratio)
    window_len = horizon_min - warmup_end
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        seed_list.append(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        queue1 = deque() # Jobs waiting for stage 1
        queue2 = deque() # Jobs waiting for stage 2
        job_in_service_1 = None # (id, start_time, service_duration)
        job_in_service_2 = None
        
        # Statistics accumulators for this seed
        area_L = 0.0 # Integral of number of jobs in system
        last_event_time = 0.0
        current_jobs_in_system = 0
        
        sum_W = 0.0
        count_completed = 0
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0 # In this model, blocking usually means buffer full. Here queues are infinite? 
        # "两道工序各自排队" implies infinite buffers unless specified. So blk should be 0.
        
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        wait_events = 0 # Number of arrivals that found server busy
        
        events = []
        
        def add_event(time, type, data=None):
            events.append((time, type, data))
            
        # Initial event
        add_event(next_arrival, 'ARRIVAL')
        
        while events:
            events.sort(key=lambda x: x[0])
            t, etype, edata = events.pop(0)
            
            if t > horizon_min: break
            
            # Update Area L before changing state
            dt = t - last_event_time
            if last_event_time < warmup_end and t > warmup_end:
                # Split interval
                dt_pre = warmup_end - last_event_time
                dt_post = t - warmup_end
                area_L += current_jobs_in_system * dt_post
            elif last_event_time >= warmup_end:
                area_L += current_jobs_in_system * dt
            # If both before warmup, do nothing
            
            last_event_time = t
            
            if etype == 'ARRIVAL':
                # Generate service times immediately
                s1 = rng.expovariate(mu1_base)
                s2 = rng.expovariate(mu2_base)
                job = {'id': len(queue1)+len(queue2)+(1 if job_in_service_1 else 0)+(1 if job_in_service_2 else 0), 's1': s1, 's2': s2, 'arrival_time': t}
                
                if t >= warmup_end:
                    count_arrivals_window += 1
                
                current_jobs_in_system += 1
                
                if job_in_service_1 is None:
                    job_in_service_1 = job
                    add_event(t + s1, 'DEP1', job)
                    if t >= warmup_end: busy_time_1 += s1 # Approximation, better to track intervals
                else:
                    queue1.append(job)
                    if t >= warmup_end: wait_events += 1
                    
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam_base)
                add_event(next_arrival, 'ARRIVAL')
                
            elif etype == 'DEP1':
                job = edata
                # Remove from service
                if job_in_service_1 == job:
                    job_in_service_1 = None
                    # Calculate actual busy duration contribution properly via intervals is hard here without storing prev state.
                    # Simpler: Track busy intervals separately.
                    
                # Move to Stage 2
                if job_in_service_2 is None:
                    job_in_service_2 = job
                    add_event(t + job['s2'], 'DEP2', job)
                else:
                    queue2.append(job)
                    
            elif etype == 'DEP2':
                job = edata
                if job_in_service_2 == job:
                    job_in_service_2 = None
                
                current_jobs_in_system -= 1
                
                w = t - job['arrival_time']
                if t >= warmup_end:
                    sum_W += w
                    count_completed += 1
                    count_departures_window += 1
                
                # Start next job in Stage 1 if available
                if queue1:
                    next_job = queue1.popleft()
                    job_in_service_1 = next_job
                    add_event(t + next_job['s1'], 'DEP1', next_job)
                
                # Start next job in Stage 2 if available
                if queue2:
                    next_job = queue2.popleft()
                    job_in_service_2 = next_job
                    add_event(t + next_job['s2'], 'DEP2', next_job)

        # Post-processing for busy fractions using a more robust method would require tracking intervals.
        # Given constraints, we approximate busy fraction by summing service times of completed jobs in window / window length?
        # No, that misses partial services. 
        # Let's re-calculate busy time by integrating server status.
        # To keep code short and within limits, I'll use a simplified accumulation during events if possible, 
        # but the above loop doesn't easily capture partial busy times at boundaries.
        # Alternative: Run a discrete event sim that tracks `server1_free_at` and `server2_free_at`.
        
        # Restarting logic with simpler state machine for accuracy on busy times
        # This second pass replaces the first complex one to ensure correctness within line limits.
        
        # Reset stats for this seed
        area_L = 0.0
        sum_W = 0.0
        count_completed = 0
        count_arrivals_window = 0
        count_departures_window = 0
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        wait_events = 0
        current_jobs_in_system = 0
        last_event_time = 0.0
        
        q1 = deque()
        q2 = deque()
        srv1_end = 0.0
        srv2_end = 0.0
        srv1_active = False
        srv2_active = False
        
        # We need to simulate again or fix the previous loop. 
        # Fixing previous loop is risky for lines. Let's write a compact simulator.
        
        # Compact Simulator
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        # Pre-generate all events? No, dynamic.
        
        # Use a priority queue approach manually since heapq is stdlib
        import heapq
        evq = []
        heapq.heappush(evq, (next_arr, 0, None)) # 0=arr, 1=dep1, 2=dep2
        
        # State: 
        # n_sys, area_L, W_sum, dep_count, arr_count, b1_time, b2_time, wait_count
        
        # Helper to update area
        def upd_area(now_t, n_now):
            nonlocal area_L, last_event_time, current_jobs_in_system
            dt = now_t - last_event_time
            if last_event_time < warmup_end:
                if now_t > warmup_end:
                    area_L += current_jobs_in_system * (now_t - warmup_end)
            else:
                area_L += current_jobs_in_system * dt
            last_event_time = now_t
            current_jobs_in_system = n_now

        # Initialize
        last_event_time = 0.0
        current_jobs_in_system = 0
        area_L = 0.0
        sum_W = 0.0
        count_completed = 0
        count_arrivals_window = 0
        count_departures_window = 0
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        wait_events = 0
        
        # Need to track when servers become free to calculate busy time accurately
        # Actually, busy time is just integral of (server is working).
        # Server 1 works if it has a job.
        
        # Let's restart the loop structure completely for clarity and correctness
        q1 = deque()
        q2 = deque()
        srv1_job = None
        srv2_job = None
        srv1_finish = 0.0
        srv2_finish = 0.0
        
        # Clear heap
        evq = []
        heapq.heappush(evq, (next_arr, 0, None))
        
        while evq:
            t, typ, data = heapq.heappop(evq)
            if t > horizon_min: break
            
            # Update Area L based on current n_sys BEFORE processing event
            # But n_sys changes in event. So we integrate up to t.
            dt = t - last_event_time
            if last_event_time < warmup_end:
                if t > warmup_end:
                    area_L += current_jobs_in_system * (t - warmup_end)
            else:
                area_L += current_jobs_in_system * dt
            last_event_time = t
            
            # Update Busy Times
            # Server 1 was busy if srv1_job is not None during [last_event_time-dt, t]
            # Wait, we updated last_event_time. We need old_last.
            # Let's store old_last.
            pass 

        # The above integration logic is getting messy inside the loop.
        # Standard trick: Keep track of `prev_time`.
        
        prev_time = 0.0
        n_sys = 0
        area_L = 0.0
        sum_W = 0.0
        cnt_dep = 0
        cnt_arr = 0
        b1 = 0.0
        b2 = 0.0
        w_cnt = 0
        
        q1 = deque()
        q2 = deque()
        s1_job = None
        s2_job = None
        s1_end = 0.0
        s2_end = 0.0
        
        evq = []
        heapq.heappush(evq, (rng.expovariate(lam_base), 0, None))
        
        while evq:
            t, typ, data = heapq.heappop(evq)
            if t > horizon_min: break
            
            dt = t - prev_time
            # Accumulate Area L
            if prev_time < warmup_end:
                if t > warmup_end:
                    area_L += n_sys * (t - warmup_end)
            else:
                area_L += n_sys * dt
            
            # Accumulate Busy Time
            if s1_job is not None:
                if prev_time < warmup_end:
                    if t > warmup_end: b1 += (t - warmup_end)
                else: b1 += dt
            if s2_job is not None:
                if prev_time < warmup_end:
                    if t > warmup_end: b2 += (t - warmup_end)
                else: b2 += dt
                
            prev_time = t
            
            if typ == 0: # Arrival
                s1 = rng.expovariate(mu1_base)
                s2 = rng.expovariate(mu2_base)
                job = {'a': t, 's1': s1, 's2': s2}
                n_sys += 1
                if t >= warmup_end: cnt_arr += 1
                
                if s1_job is None:
                    s1_job = job
                    s1_end = t + s1
                    heapq.heappush(evq, (s1_end, 1, job))
                else:
                    q1.append(job)
                    if t >= warmup_end: w_cnt += 1
                
                nxt = t + rng.expovariate(lam_base)
                heapq.heappush(evq, (nxt, 0, None))
                
            elif typ == 1: # Dep from 1
                job = data
                if s1_job == job:
                    s1_job = None
                    if q1:
                        nxt_job = q1.popleft()
                        s1_job = nxt_job
                        s1_end = t + nxt_job['s1']
                        heapq.heappush(evq, (s1_end, 1, nxt_job))
                
                # Move to Stage 2
                if s2_job is None:
                    s2_job = job
                    s2_end = t + job['s2']
                    heapq.heappush(evq, (s2_end, 2, job))
                else:
                    q2.append(job)
                    
            elif typ == 2: # Dep from 2
                job = data
                if s2_job == job:
                    s2_job = None
                    if q2:
                        nxt_job = q2.popleft()
                        s2_job = nxt_job
                        s2_end = t + nxt_job['s2']
                        heapq.heappush(evq, (s2_end, 2, nxt_job))
                
                n_sys -= 1
                w = t - job['a']
                if t >= warmup_end:
                    sum_W += w
                    cnt_dep += 1
        
        # End of seed loop calculations
        if window_len > 0:
            L_est = area_L / window_len
            W_est = sum_W / cnt_dep if cnt_dep > 0 else 0.0
            bf1 = b1 / window_len
            bf2 = b2 / window_len
            avg_bf = (bf1 + bf2) / 2.0 # Or max? Usually utilization per server. Let's report average of two or specific? 
            # Output key is busy_frac. Ambiguous. I'll report average utilization of the two stages.
            p_loss = 0.0 # Infinite buffers
            p_wait = w_cnt / cnt_arr if cnt_arr > 0 else 0.0
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(avg_bf)
            per_seed_p_loss.append(p_loss)
            per_seed_p_wait.append(p_wait)
            
            total_L_sum += L_est
            total_W_sum += W_est
            total_arr += cnt_arr
            total_dep += cnt_dep
            total_blk += 0
            total_busy_time_1 += b1
            total_busy_time_2 += b2
            total_wait_count += w_cnt
            
        seeds_used += 1

    if seeds_used == 0:
        print(json.dumps({"L":0,"W":0,"runtime_units":"minute","seed_list":[],"seeds_used":0,"time_unit":"minute","win":0}))
        return

    avg_L = total_L_sum / seeds_used
    avg_W = total_W_sum / seeds_used
    avg_arr = total_arr / seeds_used
    avg_dep = total_dep / seeds_used
    avg_blk = total_blk / seeds_used
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used
    avg_util = avg_busy_frac # Same
    avg_dep_rate = (avg_dep / window_len) * 60.0 # Per hour
    lam_eff = avg_dep_rate / 60
