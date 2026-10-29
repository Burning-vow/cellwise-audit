import sys, json, random, math
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[k] = v
            i += 2
        else:
            i += 1
    
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0')) # hours
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min mean -> 1/5 hr = 12/hr)
    c = 1
    K = 4 # capacity including service
    
    if pert == 'lam_up': lam = lam_base * 1.2
    elif pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif pert == 'c_up': c = 2; K = 5; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    
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
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        events = []
        heapq.heappush(events, (rng.expovariate(lam), 'arr', 0))
        
        t = 0.0
        n_in_sys = 0
        next_event_time = events[0][0] if events else horizon
        
        warmup_end = horizon * 0.25
        
        area_N = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        wait_times = []
        
        last_t = 0.0
        
        while events:
            curr_t, etype, data = heapq.heappop(events)
            
            if curr_t > horizon: break
            
            dt = curr_t - last_t
            if last_t >= warmup_end:
                area_N += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            
            last_t = curr_t
            
            if etype == 'arr':
                if curr_t >= warmup_end:
                    count_arr += 1
                
                if n_in_sys < K:
                    n_in_sys += 1
                    svc_time = rng.expovariate(mu)
                    dep_time = curr_t + svc_time
                    heapq.heappush(events, (dep_time, 'dep', {'start': curr_t, 'end': dep_time}))
                    
                    if n_in_sys == 1:
                        pass # server becomes busy, handled by area calculation implicitly via n>0 check? 
                             # Actually busy_frac is 1-pi0. pi0 is prob empty. 
                             # We track area_busy as time when n>0.
                else:
                    if curr_t >= warmup_end:
                        count_blk += 1
                
                next_arr = curr_t + rng.expovariate(lam)
                if next_arr <= horizon:
                    heapq.heappush(events, (next_arr, 'arr', 0))
                    
            elif etype == 'dep':
                n_in_sys -= 1
                if curr_t >= warmup_end:
                    count_dep += 1
                    w = data['end'] - data['start'] # This is service time, not waiting time.
                    # Wait, W usually means total time in system or waiting time?
                    # Standard M/M/1/K: L = lambda_eff * W. W is average time in system.
                    # The prompt asks for W (minutes). Usually W is sojourn time.
                    # Let's calculate sojourn time.
                    # But we need to know arrival time.
                    # I didn't store arrival time in the event payload properly for waiting time calc if it's queueing.
                    # In M/M/1/K, if a customer arrives and finds server busy, they wait.
                    # If they find server idle, they start immediately.
                    # Sojourn time = Service Time + Waiting Time.
                    # My previous code stored 'start' which is when service starts.
                    # I need arrival time too.
                    # Let's fix the event structure.
                    pass

        # Re-implementing loop with correct state tracking for W (sojourn time)
        # Reset variables for this seed
        events = []
        rng = random.Random(seed)
        first_arr = rng.expovariate(lam)
        heapq.heappush(events, (first_arr, 'arr', None))
        
        t = 0.0
        n_in_sys = 0
        last_t = 0.0
        warmup_end = horizon * 0.25
        
        area_N = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_sojourn = 0.0
        sum_wait = 0.0 # For p_wait definition? p_wait is prob of waiting.
        count_waited = 0
        
        while events:
            curr_t, etype, data = heapq.heappop(events)
            if curr_t > horizon: break
            
            dt = curr_t - last_t
            if last_t >= warmup_end:
                area_N += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            last_t = curr_t
            
            if etype == 'arr':
                arr_time = curr_t
                if curr_t >= warmup_end:
                    count_arr += 1
                
                if n_in_sys < K:
                    n_in_sys += 1
                    svc_dur = rng.expovariate(mu)
                    start_svc = curr_t
                    if n_in_sys > 1: # Someone was already there, so this one waits? 
                                     # No, if n_in_sys becomes 2, it means 1 was in service, 1 joins queue.
                                     # So this new arrival waits until current service ends.
                                     # But we don't know when current service ends easily without tracking queue.
                                     # Simpler: Track completion times.
                                     # Actually, standard DES for M/M/1/K:
                                     # When arrival happens:
                                     # If server idle (n=0 before inc): Start service immediately.
                                     # If server busy (n>0 before inc): Join queue.
                                     
                    # Let's restart logic with explicit queue simulation
                    pass
                else:
                    if curr_t >= warmup_end:
                        count_blk += 1
                
                nxt = curr_t + rng.expovariate(lam)
                if nxt <= horizon:
                    heapq.heappush(events, (nxt, 'arr', None))

        # Correct Implementation for Seed Loop
        rng = random.Random(seed)
        events = []
        heapq.heappush(events, (rng.expovariate(lam), 'arr', None))
        
        n_in_sys = 0
        last_t = 0.0
        warmup_end = horizon * 0.25
        area_N = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_sojourn = 0.0
        count_waited = 0
        
        # Queue to hold customers waiting for service
        # Each element: (arrival_time)
        queue = deque()
        # Server status: end_time of current service, or None if idle
        server_free_at = None
        
        while events:
            curr_t, etype, _ = heapq.heappop(events)
            if curr_t > horizon: break
            
            dt = curr_t - last_t
            if last_t >= warmup_end:
                area_N += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            last_t = curr_t
            
            if etype == 'arr':
                if curr_t >= warmup_end:
                    count_arr += 1
                
                if n_in_sys < K:
                    n_in_sys += 1
                    queue.append(curr_t)
                    
                    # Check if server is free
                    if server_free_at is None or curr_t >= server_free_at:
                        # Start service immediately
                        cust_arr = queue.popleft()
                        svc_dur = rng.expovariate(mu)
                        server_free_at = curr_t + svc_dur
                        heapq.heappush(events, (server_free_at, 'dep', cust_arr))
                        # Sojourn time will be calculated at dep
                        # Did they wait? If curr_t == cust_arr, no wait.
                        # But here we just started.
                        # We need to distinguish between those who waited and those who didn't for p_wait?
                        # p_wait is probability an arriving customer has to wait.
                        # If server was busy when they arrived, they wait.
                        # How to know if server was busy?
                        # If n_in_sys > 1 after increment, then someone was already in system.
                        # Since FCFS, if n_in_sys > 1, the new arrival definitely waits (unless server just freed up exactly at curr_t?)
                        # If server_free_at <= curr_t, server was idle.
                        
                        if server_free_at is not None and server_free_at > curr_t:
                            # This branch shouldn't happen if we checked above correctly
                            pass
                            
                        # Determine if this specific arrival waited
                        # If the queue length BEFORE adding this person was > 0, OR if server was busy.
                        # Actually simpler: At arrival time `curr_t`, if `server_free_at` is not None AND `server_free_at > curr_t`, then server is busy.
                        # Also if there are people in queue.
                        # But we just added to queue.
                        # Let's check state BEFORE adding to queue?
                        # State: n_in_sys_old, server_free_at_old.
                        # If n_in_sys_old == 0, server idle. New arrival doesn't wait.
                        # If n_in_sys_old > 0, server busy (or queue non-empty). New arrival waits.
                        
                        # We incremented n_in_sys already. So old_n = n_in_sys - 1.
                        if (n_in_sys - 1) > 0:
                            if curr_t >= warmup_end:
                                count_waited += 1
                    else:
                        # Server busy, join queue
                        if curr_t >= warmup_end:
                            count_waited += 1
                else:
                    if curr_t >= warmup_end:
                        count_blk += 1
                
                nxt = curr_t + rng.expovariate(lam)
                if nxt <= horizon:
                    heapq.heappush(events, (nxt, 'arr', None))
                    
            elif etype == 'dep':
                # Customer leaves
                n_in_sys -= 1
                if curr_t >= warmup_end:
                    count_dep += 1
                    arr_time = _ # passed in event? No, I used _ for data. Need to pass arr_time.
                
                # Fix: Pass arr_time in event
                # Redoing loop slightly cleaner mentally...
                pass

        # Final Clean Implementation
        rng = random.Random(seed)
        events = []
        heapq.heappush(events, (rng.expovariate(lam), 'arr', None))
        
        n_in_sys = 0
        last_t = 0.0
        warmup_end = horizon * 0.25
        area_N = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_sojourn = 0.0
        count_waited = 0
        
        queue = deque()
        server_free_at = None
        
        while events:
            curr_t, etype, data = heapq.heappop(events)
            if curr_t > horizon: break
            
            dt = curr_t - last_t
            if last_t >= warmup_end:
                area_N += n_in_sys * dt
                if n_in_sys > 0:
                    area_busy += dt
            last_t = curr_t
            
            if etype == 'arr':
                if curr_t >= warmup_end:
                    count_arr += 1
                
                if n_in_sys < K:
                    n_in_sys += 1
                    queue.append(curr_t)
                    
                    if server_free_at is None or curr_t >= server_free_at:
                        # Start service
                        arr_t = queue.popleft()
                        svc_dur = rng.expovariate(mu)
                        server_free_at = curr_t + svc_dur
                        heapq.heappush(events, (server_free_at, 'dep', arr_t))
                        
                        # Check wait
                        # If queue was empty before pop? 
                        # We appended curr_t. Then popped it.
                        # If len(queue) was 0 before append, and server was idle, no wait.
                        # If server was idle but queue had others? Impossible in single server FCFS if we start service immediately.
                        # Condition for waiting: Arrival found server busy OR queue non-empty.
                        # Since we check `server_free_at <= curr_t` to start service, if that condition holds, server was idle.
                        # If server was idle, did they wait? No.
                        # If server was NOT idle (else branch), they wait.
                        # But what if server was idle but queue had people? 
                        # In our logic, if server_free_at <= curr_t, we pop from queue.
                        # If queue had people, we would have started them earlier?
                        # Yes, because when a dep happens, we check queue.
                        # So if we are at 'arr' and server_free_at <= curr_t, it implies server was idle.
                        # Thus, no wait.
                        pass
                    else:
                        # Server busy, must wait
                        if curr_t >= warmup_end:
                            count_waited += 1
                else:
                    if curr_t >= warmup_end:
                        count_blk += 1
                
                nxt = curr_t + rng.expovariate(lam)
                if nxt <= horizon:
                    heapq.heappush(events, (nxt, 'arr', None))
                    
            elif etype == 'dep':
                arr_t = data
                if curr_t >= warmup_end:
                    count_dep += 1
                    sum_sojourn += (curr_t - arr_t)
                
                # Try to start next service
                if queue:
                    next_arr_t = queue.popleft()
                    svc_dur = rng.expovariate(mu)
                    server_free_at = curr_t + svc_dur
                    heapq.heappush(events, (server_free_at, 'dep', next_arr_t))
                else:
                    server_free_at = None

        win_len = horizon - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_N / win_len
        W_est = (sum_sojourn / count_dep) * 60.0 if count_dep > 0 else 0.0 # Convert hours to minutes
        busy_frac_est = area_busy / win_len
        p_loss_est = count_blk / count_arr if count_arr > 0 else 0.0
        p_wait_est = count_waited / count_arr if count_arr > 0 else 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_blk.append(count_blk)
        all_dep.append(count_dep)
        
        # busy_util = E[min(N,c)]/c. Here c=1 (or 2 if pert c_up).
        # N is number in system. min(N, c).
        # We didn't track area_min_N_c directly.
        # Approximation: If c=1, min(N,1) is 1 if N>0 else 0. So area_min_N_1 == area_busy.
        # busy_util = area_busy / win_len / c = busy_frac / c.
        # If c=2, we need more complex tracking. Given constraints, assume c=1 mostly unless pert=c_up.
        # For c_up, c=2. We need area of min(N,2).
        # Let's add tracking for min_N_c area.
        
        # Re-run seed loop with min_N_c tracking? Too long.
        # Simplified: Calculate busy_util based on c.
        # If c==1: busy_util = busy_frac_est
        # If c==2: Need integral of min(n,2).
        # I'll modify the loop above to include area_min_nc.
        
        # Since I can't edit the loop easily now without rewriting whole block, 
        # I will assume c=1 for base case and handle c=2 approximation or rewrite.
        # Rewriting is safer.
        
        # ... [Rewrite inner loop to capture area_min_nc] ...
        
        # Due to length constraints, I will inline the corrected logic below.
        pass

    # Placeholder for final assembly to fit line limits
    # I will generate the full code in the output block
