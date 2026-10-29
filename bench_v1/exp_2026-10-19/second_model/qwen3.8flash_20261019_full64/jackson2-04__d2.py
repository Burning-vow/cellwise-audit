import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 4.0 / 60.0  # jobs per minute
    mu1_base = 1.0 / 6.0   # service rate stage 1 (jobs/min)
    mu2_base = 1.0 / 5.0   # service rate stage 2 (jobs/min)

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
        lam = lam_base
    elif pert == 'c_up':
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base

    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else H * 60.0
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seeds_used_list = []
    
    for i in range(N):
        seed = S_start + i
        seeds_used_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = deque() # waiting in stage 1
        q2 = deque() # waiting in stage 2
        s1_free_at = -1.0
        s2_free_at = -1.0
        
        # Statistics accumulators (for area integration)
        # We need to integrate L over time. 
        # L is number of items in system.
        # We track last_time and current_L to compute area incrementally.
        last_time = 0.0
        curr_L = 0
        
        area_L = 0.0
        total_service_time_sum = 0.0 # Sum of W for completed jobs? No, we need avg W.
        # Better: accumulate sum of sojourn times for completed jobs in window.
        # And count completions.
        
        # Warmup handling: discard first 25% of horizon
        warmup_end = 0.25 * horizon_min
        
        # Counters for the statistical window only
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0 # Jobs that had to wait (arrival time < start service time)
        
        # For busy fraction, we need to track when servers are busy within the window.
        # This is tricky with discrete events. 
        # Alternative: Track total time server was busy during [warmup_end, horizon].
        # We can do this by checking state transitions or integrating.
        # Let's use event-driven integration for busy time as well.
        
        # To simplify, let's run simulation until horizon.
        # We will record events.
        
        # Event queue: (time, type, data)
        # Types: 'arr', 'dep1', 'dep2'
        events = []
        
        # Generate initial arrival
        next_arr_t = rng.expovariate(lam)
        events.append((next_arr_t, 'arr', None))
        
        # Pre-generate service times? Requirement: "service duration must be drawn at arrival".
        # So when an item arrives, we draw its service time for stage 1 and stage 2 immediately.
        # Store them in the job object.
        
        # Job structure: dict {id, arr_t, svc1, svc2, enter_q1_t, start_s1_t, end_s1_t, enter_q2_t, start_s2_t, end_s2_t}
        # But we don't know future arrivals. We process events chronologically.
        
        # We need to handle the fact that we might not have enough jobs to fill queues initially.
        
        # Simulation Loop
        while events:
            # Peek next event
            t_next, ev_type, _ = min(events, key=lambda x: x[0])
            
            # Before processing event, update integrals from last_time to t_next
            dt = t_next - last_time
            if dt > 0:
                # Update Area L
                # Only count if interval overlaps with statistical window [warmup_end, horizon]
                overlap_start = max(last_time, warmup_end)
                overlap_end = min(t_next, horizon_min)
                if overlap_start < overlap_end:
                    area_L += curr_L * (overlap_end - overlap_start)
                
                # Update Busy Times
                # Server 1 busy if s1_free_at > last_time (roughly)
                # More precise: Server 1 is busy during [start_s1, end_s1].
                # We don't track individual intervals easily without storing history.
                # Instead, let's track "server busy time" by checking if server is currently busy.
                # If s1_free_at > t_next, it means server 1 is busy throughout [last_time, t_next]?
                # Not necessarily. It could finish before t_next.
                # Actually, s1_free_at is the time the CURRENT job finishes.
                # If there is a queue, the next job starts immediately.
                # So if q1 is not empty OR a job is being served, server is busy.
                # Condition for Server 1 Busy: (q1 has items) OR (s1_free_at > last_time AND s1_free_at <= t_next? No.)
                # Simpler: Server 1 is busy if there is any job in stage 1 (in service or waiting).
                # Wait, if waiting, server is busy serving the one in front.
                # So Server 1 is busy if len(q1) > 0 OR (a job is currently in service).
                # How to know if a job is in service? 
                # If s1_free_at > last_time, it implies the previous job finished after last_time?
                # Let's maintain a boolean `is_s1_busy` updated on events.
                pass
            
            # Process event
            events.remove((t_next, ev_type, _))
            
            if t_next > horizon_min:
                break
                
            if ev_type == 'arr':
                # Draw service times now
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                job = {'arr_t': t_next, 'svc1': svc1, 'svc2': svc2}
                
                # Check capacity? Problem says "queueing", usually infinite buffer unless specified.
                # "blk" suggests blocking/loss. Standard Jackson network has infinite buffers.
                # However, output requires p_loss. If infinite buffer, p_loss is 0.
                # Maybe finite buffer? Problem doesn't specify size. 
                # Usually "Jackson" implies infinite. But "blk" field exists.
                # If no loss mechanism defined, assume infinite buffer -> blk=0, p_loss=0.
                # Let's assume infinite buffer as standard for "Jackson network" description unless "finite capacity" mentioned.
                # The prompt mentions "blk" and "p_loss" in output requirements, suggesting they might be non-zero or just reported as 0.
                # I will implement infinite buffer.
                
                q1.append(job)
                curr_L += 1
                
                # Try to start service on S1
                if s1_free_at <= t_next:
                    # Start immediately
                    j = q1.popleft()
                    start_t = t_next
                    end_t = t_next + j['svc1']
                    s1_free_at = end_t
                    j['start_s1_t'] = start_t
                    j['end_s1_t'] = end_t
                    # Schedule departure from S1
                    events.append((end_t, 'dep1', j))
                    
                # Schedule next arrival
                next_arr_t = t_next + rng.expovariate(lam)
                events.append((next_arr_t, 'arr', None))
                
            elif ev_type == 'dep1':
                _, _, job = events.pop(events.index((t_next, ev_type, _))) # Re-fetch properly
                # Actually, I removed it above. Need to get the job data.
                # My loop logic above removes the tuple. I need the job object.
                # Let's restructure slightly.
                pass

            elif ev_type == 'dep2':
                pass

        # This manual event loop is getting complex to write compactly without classes.
        # Let's restart the simulation logic with a cleaner approach using heapq.
        
        import heapq
        
        # Reset stats for this seed
        area_L = 0.0
        sum_W = 0.0
        count_dep_win = 0
        count_arr_win = 0
        count_blk_win = 0
        count_wait_win = 0
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        
        # State
        q1 = deque()
        q2 = deque()
        s1_free_at = -1.0
        s2_free_at = -1.0
        curr_L = 0
        last_time = 0.0
        
        heap = []
        next_arr_t = rng.expovariate(lam)
        heapq.heappush(heap, (next_arr_t, 0, None)) # 0=arr
        
        # Helper to add busy time
        def add_busy_time(server_id, start, end, free_at_prev):
            # Overlap with window
            w_start = max(start, warmup_end)
            w_end = min(end, horizon_min)
            if w_start < w_end:
                return w_end - w_start
            return 0.0

        while heap:
            t, typ, data = heapq.heappop(heap)
            
            if t > horizon_min:
                break
                
            # Integrate L and Busy Time from last_time to t
            dt = t - last_time
            if dt > 0:
                # L Integration
                ws = max(last_time, warmup_end)
                we = min(t, horizon_min)
                if ws < we:
                    area_L += curr_L * (we - ws)
                
                # Busy Time Integration
                # Server 1 is busy if it was working on something that spans into this interval
                # Or if queue is non-empty? No, if queue is non-empty, server is busy serving head.
                # If server is idle, s1_free_at <= last_time.
                # If server is busy, s1_free_at > last_time.
                # The busy period ends at s1_free_at.
                
                # Check S1
                if s1_free_at > last_time:
                    bs = max(last_time, warmup_end)
                    be = min(s1_free_at, t, horizon_min)
                    if bs < be:
                        busy_time_1 += be - bs
                
                # Check S2
                if s2_free_at > last_time:
                    bs = max(last_time, warmup_end)
                    be = min(s2_free_at, t, horizon_min)
                    if bs < be:
                        busy_time_2 += be - bs

            last_time = t
            
            if typ == 0: # Arrival
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                job = {'arr_t': t, 'svc1': svc1, 'svc2': svc2}
                
                # Infinite buffer assumption
                q1.append(job)
                curr_L += 1
                
                # Count arrival in window
                if t >= warmup_end:
                    count_arr_win += 1
                
                # Try start S1
                if s1_free_at <= t:
                    j = q1.popleft()
                    start_t = t
                    end_t = t + j['svc1']
                    s1_free_at = end_t
                    j['start_s1_t'] = start_t
                    j['end_s1_t'] = end_t
                    heapq.heappush(heap, (end_t, 1, j)) # 1=dep1
                    
                    # Did it wait?
                    if t >= warmup_end:
                        # If it started immediately, did it wait? 
                        # Waiting means arrival time < start time. Here equal.
                        # But if queue was empty, no wait.
                        # If queue was NOT empty, it would have been appended and not popped here?
                        # Logic: If s1_free_at <= t, server is idle. Queue MUST be empty before append?
                        # Yes, because if queue wasn't empty, server would be busy (unless just freed).
                        # If server just freed at exactly t, and queue was empty, then new job arrives.
                        # If queue was not empty, server wouldn't be free.
                        # So if we pop immediately, wait time is 0.
                        pass
                    else:
                        # If we didn't pop immediately, it waits.
                        # But we check `if s1_free_at <= t`. If false, it goes to queue.
                        # So if it goes to queue, it waits.
                        # We need to detect if it waited.
                        # Easier: Record start time later.
                        pass
                
                # Next arrival
                next_arr_t = t + rng.expovariate(lam)
                heapq.heappush(heap, (next_arr_t, 0, None))
                
            elif typ == 1: # Departure from Stage 1
                j = data
                # Move to Stage 2
                q2.append(j)
                # curr_L remains same (moved from S1 to S2 queue/service)
                
                # Try start S2
                if s2_free_at <= t:
                    j2 = q2.popleft()
                    start_t = t
                    end_t = t + j2['svc2']
                    s2_free_at = end_t
                    j2['start_s2_t'] = start_t
                    j2['end_s2_t'] = end_t
                    heapq.heappush(heap, (end_t, 2, j2)) # 2=dep2
                else:
                    # Will wait in Q2
                    pass
                    
            elif typ == 2: # Departure from Stage 2 (System Exit)
                j = data
                # Calculate Sojourn Time W
                w_time = t - j['arr_t']
                
                # Check if this completion falls in window
                # Usually, we count departures in window.
                if t >= warmup_end:
                    count_dep_win += 1
                    sum_W += w_time
                    
                    # Check if it waited anywhere
                    # Waited in S1 if start_s1_t > arr_t
                    # Waited in S2 if start_s2_t > end_s1_t
                    if j['start_s1_t'] > j['arr_t'] or j['start_s2_t'] > j['end_s1_t']:
                        count_wait_win += 1
                
                curr_L -= 1
                
                # Try start S1 from Q1
                if q1:
                    j_new = q1.popleft()
                    start_t = t
                    end_t = t + j_new['svc1']
                    s1_free_at = end_t
                    j_new['start_s1_t'] = start_t
                    j_new['end_s1_t'] = end_t
                    heapq.heappush(heap, (end_t, 1, j_new))
                
                # Try start S2 from Q2
                if q2:
                    j_new = q2.popleft()
                    start_t = t
                    end_t = t + j_new['svc2']
                    s2_free_at = end_t
                    j_new['start_s2_t'] = start_t
                    j_new['end_s2_t'] = end_t
                    heapq.heappush(heap, (end_t, 2, j_new))

        # Final integration up to horizon if needed? 
        # The loop breaks when t > horizon. 
        # We should ensure we integrated up to horizon.
        # The last event processed was <= horizon.
        # If there are pending busy periods extending beyond horizon, we truncated them in the loop.
        # But what about the final segment from last_time to horizon?
        # In the loop, we integrate from last_time to t.
        # After loop, last_time is the time of the last processed event <= horizon.
        # We need to integrate from last_time to horizon.
        
        dt_final = horizon_min - last_time
        if dt_final > 0:
            ws = max(last_time, warmup_end)
            we = horizon_min
            if ws < we:
                area_L += curr_L * (we - ws)
            
            if s1_free_at > last_time:
                bs = max(last_time, warmup_end)
                be = min(s1_free_at, horizon_min)
                if bs < be:
                    busy_time_1 += be - bs
            
            if s2_free_at > last_time:
                bs = max(last_time, warmup_end)
                be = min(s2_free_at, horizon_min)
                if bs < be:
                    busy_time_2 += be - bs
