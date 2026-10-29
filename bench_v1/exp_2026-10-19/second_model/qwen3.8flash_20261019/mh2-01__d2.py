import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 3.0
    mu_base = 10.0
    c_base = 1
    
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': c_base += 1
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time_busy = 0.0
    total_time_idle = 0.0
    total_wait_time_sum = 0.0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # Generate arrival times and service durations upfront
        arrivals = []
        t = 0.0
        while t < horizon:
            inter = rng.expovariate(lam_base)
            t += inter
            if t >= horizon: break
            # Two-stage hyperexponential with mean 6 min (0.1 hr) and CV 1.5
            # Mean = 0.1, Var = (1.5*0.1)^2 = 0.0225
            # H2: p*mean1 + (1-p)*mean2 = 0.1
            # E[X^2] = p*2*mean1^2 + (1-p)*2*mean2^2 = Var + Mean^2 = 0.0225 + 0.01 = 0.0325
            # Let's use standard H2 construction or just sample from mixture of two exps
            # To keep it simple and valid: choose p=0.5, then solve for means? 
            # Actually, any distribution with correct mean/CV works for P-K approx, but we simulate exact.
            # Let's pick a specific H2: p=0.5, mu1, mu2 such that mean=0.1, cv=1.5
            # m = 0.5*(1/mu1 + 1/mu2) = 0.1 => 1/mu1 + 1/mu2 = 0.2
            # v = 0.5*(2/mu1^2 + 2/mu2^2) - 0.01 = 0.0225 => 1/mu1^2 + 1/mu2^2 = 0.065
            # Let x=1/mu1, y=1/mu2. x+y=0.2, x^2+y^2=0.065
            # (x+y)^2 = x^2+y^2+2xy => 0.04 = 0.065 + 2xy => xy = -0.0125 -> Impossible for real positive rates.
            # Need different p. Try p small.
            # General H2: mean = p*m1 + (1-p)*m2, var = p*m1^2+(1-p)*m2^2 - mean^2
            # Let's just use Erlang-2 scaled? No, CV must be 1.5 > 1. So H2 is needed.
            # Let's try p=0.1.
            # 0.1*m1 + 0.9*m2 = 0.1
            # 0.1*m1^2 + 0.9*m2^2 - 0.01 = 0.0225 => 0.1*m1^2 + 0.9*m2^2 = 0.0325
            # From first: m1 = (0.1 - 0.9*m2)/0.1 = 1 - 9*m2
            # Sub into second: 0.1*(1-9m2)^2 + 0.9*m2^2 = 0.0325
            # 0.1*(1 - 18m2 + 81m2^2) + 0.9m2^2 = 0.0325
            # 0.1 - 1.8m2 + 8.1m2^2 + 0.9m2^2 = 0.0325
            # 9m2^2 - 1.8m2 + 0.0675 = 0
            # Discriminant: 1.8^2 - 4*9*0.0675 = 3.24 - 2.43 = 0.81 > 0
            # m2 = (1.8 +/- 0.9) / 18
            # m2a = 2.7/18 = 0.15, m2b = 0.9/18 = 0.05
            # If m2=0.15, m1 = 1 - 1.35 = -0.35 (Invalid)
            # If m2=0.05, m1 = 1 - 0.45 = 0.55
            # So p=0.1, m1=0.55, m2=0.05 works.
            # Rates: mu1 = 1/0.55, mu2 = 1/0.05
            if rng.random() < 0.1:
                svc = rng.expovariate(1.0/0.55)
            else:
                svc = rng.expovariate(1.0/0.05)
            arrivals.append((t, svc))
            
        # Simulation
        queue = [] # list of (arrival_time, service_duration)
        busy_until = 0.0
        current_time = 0.0
        n_in_sys = 0
        
        # For area integration
        last_event_time = 0.0
        area_n = 0.0
        area_busy = 0.0
        wait_sum = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        # Process events
        idx = 0
        while idx < len(arrivals) or queue:
            next_arr_t = arrivals[idx][0] if idx < len(arrivals) else float('inf')
            next_dep_t = busy_until if queue else float('inf')
            
            if next_arr_t <= next_dep_t:
                # Arrival
                t = next_arr_t
                # Integrate up to t
                dt = t - last_event_time
                if last_event_time >= win_start:
                    area_n += n_in_sys * dt
                    if n_in_sys > 0: area_busy += dt
                
                # Update state
                if t < win_start:
                    pass # Just update counts/state for future, but don't integrate yet? 
                         # Wait, the problem says "statistics only in window". 
                         # But we need to know the state at win_start.
                         # The integration logic above handles it if we start integrating from win_start.
                         # However, we need to handle the transition at win_start carefully.
                
                # Actually, simpler: track global time, and when crossing win_start, reset accumulators?
                # Or just check if interval overlaps with [win_start, horizon].
                
                # Let's refine integration:
                # We are moving from last_event_time to t.
                # Overlap with [win_start, horizon]:
                s = max(last_event_time, win_start)
                e = min(t, horizon)
                if e > s:
                    dt_win = e - s
                    area_n += n_in_sys * dt_win
                    if n_in_sys > 0: area_busy += dt_win
                
                # Handle arrival
                arr_count += 1
                if n_in_sys < c_base:
                    # Start service immediately
                    queue.append((arrivals[idx][1], t)) # store duration and arrival time for wait calc?
                    # Actually, we need to know when service starts to calculate wait.
                    # If server free, start now.
                    # We need to manage the single server timeline properly.
                    # Let's restart the simulation loop structure to be more robust.
                    pass
                else:
                    # Queue or Block? M/M/1/K? Problem doesn't specify capacity limit.
                    # "Call center" usually implies infinite queue unless stated.
                    # But "blk" (blocked/lost) is requested. 
                    # Standard M/M/1 has no blocking. 
                    # Maybe it's M/M/1 with finite buffer? Not specified.
                    # Assuming infinite queue, blk should be 0.
                    # But if blk is requested, maybe there is a hidden assumption?
                    # Re-read: "average hourly 3 calls", "service time...". No capacity mentioned.
                    # I will assume infinite queue, so blk=0.
                    queue.append((arrivals[idx][1], t))
                
                n_in_sys += 1
                if n_in_sys == 1:
                    # Server becomes busy
                    dur = arrivals[idx][1]
                    busy_until = t + dur
                idx += 1
                last_event_time = t
                
            else:
                # Departure
                t = next_dep_t
                s = max(last_event_time, win_start)
                e = min(t, horizon)
                if e > s:
                    dt_win = e - s
                    area_n += n_in_sys * dt_win
                    if n_in_sys > 0: area_busy += dt_win
                
                # Complete service
                # Pop from queue? 
                # My previous logic was flawed regarding queue management.
                # Let's rewrite the inner simulation loop cleanly.
                break # Exit this broken attempt to rewrite below.
        
        # --- Clean Rewrite of Simulation Loop ---
        rng = random.Random(seed)
        events = [] # (time, type, data)
        t = 0.0
        while t < horizon:
            inter = rng.expovariate(lam_base)
            t += inter
            if t >= horizon: break
            if rng.random() < 0.1:
                svc = rng.expovariate(1.0/0.55)
            else:
                svc = rng.expovariate(1.0/0.05)
            events.append((t, 'A', svc))
        
        q = [] # List of (arrival_time, service_duration) waiting or being served?
        # Better: Track server status separately.
        # State: server_free_at (time), queue (list of (arr_time, svc_dur))
        server_free_at = 0.0
        queue = []
        
        area_n = 0.0
        area_busy = 0.0
        wait_sum = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        
        last_t = 0.0
        n_curr = 0
        
        # Sort events by time (already sorted)
        for ev_t, ev_type, ev_data in events:
            # Advance time to ev_t
            dt = ev_t - last_t
            s = max(last_t, win_start)
            e = min(ev_t, horizon)
            if e > s:
                dt_win = e - s
                area_n += n_curr * dt_win
                if n_curr > 0: area_busy += dt_win
            
            # Process Event
            if ev_type == 'A':
                arr_cnt += 1
                # Check if blocked? Assume infinite queue, so never blocked.
                # If capacity C was defined, we'd check here.
                # Since not defined, blk=0.
                
                # Add to system
                n_curr += 1
                queue.append((ev_t, ev_data))
                
                # If server was idle, start service immediately
                if n_curr == 1:
                    # Service starts now
                    pass # Handled in departure logic effectively?
                    # Actually, we need to schedule departure.
                    # But with multiple servers or queues, it's complex.
                    # With 1 server:
                    # If server is free (server_free_at <= ev_t), start service.
                    if server_free_at <= ev_t:
                        start_t = ev_t
                        end_t = ev_t + ev_data
                        server_free_at = end_t
                        # Remove from queue head? It's the only one.
                        # We need to track which customer is being served.
                        # Let's pop it.
                        cust = queue.pop(0)
                        # Calculate wait
                        w = start_t - cust[0]
                        if start_t >= win_start:
                            wait_sum += w
                        # Schedule departure? 
                        # We can just let the loop continue. 
                        # But we need to know when the next event is.
                        # The next event could be another arrival OR this departure.
                        # This approach requires inserting departure events dynamically.
                        # Simpler: Use a priority queue for events.
                        pass
                    else:
                        # Server busy, customer waits
                        pass
                else:
                    # Server busy, customer joins queue
                    pass
                    
            # This manual loop is getting messy because departures aren't in `events`.
            # Let's use a proper event queue.
            break
        
        # --- Proper Event Queue Simulation ---
        rng = random.Random(seed)
        pq = [] # (time, type, id/data)
        # Generate all arrivals first
        t = 0.0
        arr_id = 0
        while t < horizon:
            inter = rng.expovariate(lam_base)
            t += inter
            if t >= horizon: break
            if rng.random() < 0.1:
                svc = rng.expovariate(1.0/0.55)
            else:
                svc = rng.expovariate(1.0/0.05)
            pq.append((t, 'A', (arr_id, svc)))
            arr_id += 1
        
        import heapq
        heapq.heapify(pq)
        
        server_free_at = 0.0
        queue = [] # (arrival_time, service_duration)
        
        area_n = 0.0
        area_busy = 0.0
        wait_sum = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        
        last_t = 0.0
        n_curr = 0
        
        while pq:
            curr_t, typ, data = heapq.heappop(pq)
            
            # Integrate
            s = max(last_t, win_start)
            e = min(curr_t, horizon)
            if e > s:
                dt_win = e - s
                area_n += n_curr * dt_win
                if n_curr > 0: area_busy += dt_win
            
            if typ == 'A':
                arr_cnt += 1
                _, svc_dur = data
                n_curr += 1
                queue.append((curr_t, svc_dur))
                
                # If server free, start service
                if server_free_at <= curr_t:
                    # Start service for head of queue
                    arr_t, dur = queue.pop(0)
                    start_t = curr_t
                    end_t = curr_t + dur
                    server_free_at = end_t
                    w = start_t - arr_t
                    if start_t >= win_start:
                        wait_sum += w
                    # Push departure event
                    heapq.heappush(pq, (end_t, 'D', None))
                    
            elif typ == 'D':
                dep_cnt += 1
                n_curr -= 1
                # If queue not empty, start next service
                if queue:
                    arr_t, dur = queue.pop(0)
                    start_t = curr_t
                    end_t = curr_t + dur
                    server_free_at = end_t
                    w = start_t - arr_t
                    if start_t >= win_start:
                        wait_sum += w
                    heapq.heappush(pq, (end_t, 'D', None))
                else:
                    server_free_at = curr_t # Idle
            
            last_t = curr_t
            
        # Final integration to horizon
        s = max(last_t, win_start)
        e = horizon
        if e > s:
            dt_win = e - s
            area_n += n_curr * dt_win
            if n_curr > 0: area_busy += dt_win
            
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = wait_sum / dep_cnt if dep_cnt > 0 else 0
        Busy_est = area_busy / win_len if win_len > 0 else 0
        Loss_est = blk_cnt / arr_cnt if arr_cnt > 0 else 0
        Wait_est = (dep_cnt - arr_cnt + blk_cnt) / arr_cnt if arr_cnt > 0 else 0 # Approx prob wait?
        # P(wait) is fraction of customers who waited.
        # We
