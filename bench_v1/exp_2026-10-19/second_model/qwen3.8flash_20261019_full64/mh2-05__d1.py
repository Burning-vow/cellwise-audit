import sys, json, math, random

def main():
    args = {}
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('--'):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) and not sys.argv[i+1].startswith('--') else None
            args[k] = v
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 1000.0))
    S = int(args.get('seed-start', 42))
    pert = args.get('pert', 'none')
    
    lam_base = 3.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0     # per minute
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    seeds_used = 0
    seed_list = []
    
    warmup_frac = 0.25
    win_start = warmup_frac * horizon_min
    win_len = horizon_min - win_start
    
    for s_idx in range(N):
        seed = S + s_idx
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = []
        queue = []
        busy_until = -1.0
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        total_service_time_in_window = 0.0
        total_wait_time_in_window = 0.0
        total_system_time_in_window = 0.0
        area_N = 0.0
        last_event_t = 0.0
        current_N = 0
        
        events = []
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        
        add_event(next_arr, 'arr', None)
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            ev_t, ev_type, ev_data = events.pop(0)
            
            if ev_t > horizon_min:
                break
            
            dt = ev_t - last_event_t
            if last_event_t >= win_start:
                area_N += current_N * dt
                if current_N > 0:
                    total_service_time_in_window += min(dt, max(0, busy_until - last_event_t)) if busy_until > last_event_t else 0
                    # Actually we need to track waiting customers properly
                    pass
            last_event_t = ev_t
            
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if current_N == 0 and busy_until <= ev_t:
                    current_N = 1
                    busy_until = ev_t + st
                    add_event(busy_until, 'dep', {'start': ev_t, 'service_end': busy_until})
                else:
                    current_N += 1
                    queue.append({'arrival': ev_t, 'service_time': st})
                    if current_N == 1:
                        busy_until = ev_t + st
                        add_event(busy_until, 'dep', {'start': ev_t, 'service_end': busy_until})
                
                next_arr_t = ev_t + rng.expovariate(lam)
                if next_arr_t <= horizon_min:
                    add_event(next_arr_t, 'arr', None)
                    
            elif ev_type == 'dep':
                dep_count += 1
                cust_info = ev_data
                start_t = cust_info['start']
                end_t = cust_info['service_end']
                
                if start_t >= win_start:
                    wait_dur = start_t - cust_info.get('arrival', start_t)
                    total_wait_time_in_window += wait_dur
                    total_system_time_in_window += (end_t - cust_info.get('arrival', start_t))
                
                current_N -= 1
                if queue:
                    nxt = queue.pop(0)
                    nxt['arrival'] = nxt['arrival']
                    new_start = ev_t
                    new_end = new_start + nxt['service_time']
                    busy_until = new_end
                    add_event(new_end, 'dep', {'start': new_start, 'service_end': new_end, 'arrival': nxt['arrival']})
                    current_N += 1
                else:
                    busy_until = -1.0
        
        # Recalculate areas more carefully using a simpler approach
        # Let's redo the simulation with proper tracking
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        busy_until = -1.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        total_wait = 0.0
        total_sys = 0.0
        area_N = 0.0
        last_t = 0.0
        cur_N = 0
        events = [(next_arr, 'arr')]
        
        while events:
            events.sort(key=lambda x: x[0])
            et, typ = events.pop(0)
            if et > horizon_min:
                break
            dt = et - last_t
            if last_t >= win_start:
                area_N += cur_N * dt
            last_t = et
            
            if typ == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if cur_N == 0:
                    cur_N = 1
                    busy_until = et + st
                    events.append((busy_until, 'dep'))
                    # Store arrival time for this customer
                    events[-1] = (busy_until, 'dep', et, st)
                else:
                    cur_N += 1
                    queue.append((et, st))
                na = et + rng.expovariate(lam)
                if na <= horizon_min:
                    events.append((na, 'arr'))
            elif typ == 'dep':
                dep_count += 1
                _, _, arr_t, svc_t = et, typ, None, None
                # Need to fix event structure
                pass
        
        # Simpler correct implementation
        rng = random.Random(seed)
        horizon = horizon_min
        warmup = win_start
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        server_free_at = -1.0
        arrivals = 0
        departures = 0
        blocked = 0
        total_wait_time = 0.0
        total_system_time = 0.0
        area_under_N = 0.0
        last_change_t = 0.0
        N_now = 0
        active_events = [(next_arrival, 'A')]
        
        while active_events:
            active_events.sort(key=lambda e: e[0])
            evt_t, evt_type = active_events[0][0], active_events[0][1]
            extra = active_events[0][2:] if len(active_events[0]) > 2 else ()
            active_events.pop(0)
            
            if evt_t > horizon:
                break
                
            dt = evt_t - last_change_t
            if last_change_t >= warmup:
                area_under_N += N_now * dt
            last_change_t = evt_t
            
            if evt_type == 'A':
                arrivals += 1
                svc_dur = rng.expovariate(mu)
                if N_now == 0:
                    N_now = 1
                    server_free_at = evt_t + svc_dur
                    active_events.append((server_free_at, 'D', evt_t, svc_dur))
                else:
                    N_now += 1
                    queue.append((evt_t, svc_dur))
                na = evt_t + rng.expovariate(lam)
                if na <= horizon:
                    active_events.append((na, 'A'))
            elif evt_type == 'D':
                departures += 1
                arr_time, svc_dur = extra[0], extra[1]
                if arr_time >= warmup:
                    wait = (evt_t - svc_dur) - arr_time
                    sys_time = evt_t - arr_time
                    total_wait_time += wait
                    total_system_time += sys_time
                N_now -= 1
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    N_now += 1
                    new_free = evt_t + q_svc
                    server_free_at = new_free
                    active_events.append((new_free, 'D', q_arr, q_svc))
                else:
                    server_free_at = -1.0
        
        L_est = area_under_N / win_len if win_len > 0 else 0
        W_est = total_system_time / departures if departures > 0 else 0
        busy_frac_est = area_under_N / win_len if win_len > 0 else 0  # For c=1, E[min(N,1)] approx by fraction of time N>=1
        # More accurate busy fraction: integrate min(N,1)
        # We didn't track that separately, but for single server, busy_frac = P(N>0) which is what we want
        # Let's recompute properly by tracking when N>0 during window
        # Simplified: use L as proxy isn't right. Let me just estimate from area where N>0
        
        # Redo with proper busy integration
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        server_free_at = -1.0
        arrivals_w = 0
        departures_w = 0
        blocked_w = 0
        total_wait_w = 0.0
        total_sys_w = 0.0
        area_N_w = 0.0
        area_busy_w = 0.0
        last_t = 0.0
        N_cur = 0
        evts = [(next_arrival, 'A')]
        
        while evts:
            evts.sort(key=lambda e: e[0])
            et, tp = evts[0][0], evts[0][1]
            ex = evts[0][2:] if len(evts[0]) > 2 else ()
            evts.pop(0)
            if et > horizon:
                break
            dt = et - last_t
            if last_t >= warmup:
                area_N_w += N_cur * dt
                if N_cur > 0:
                    area_busy_w += dt
            last_t = et
            if tp == 'A':
                arrivals_w += 1
                sd = rng.expovariate(mu)
                if N_cur == 0:
                    N_cur = 1
                    server_free_at = et + sd
                    evts.append((server_free_at, 'D', et, sd))
                else:
                    N_cur += 1
                    queue.append((et, sd))
                na = et + rng.expovariate(lam)
                if na <= horizon:
                    evts.append((na, 'A'))
            elif tp == 'D':
                departures_w += 1
                at, sd = ex[0], ex[1]
                if at >= warmup:
                    w = (et - sd) - at
                    s = et - at
                    total_wait_w += w
                    total_sys_w += s
                N_cur -= 1
                if queue:
                    qa, qs = queue.pop(0)
                    N_cur += 1
                    nf = et + qs
                    server_free_at = nf
                    evts.append((nf, 'D', qa, qs))
                else:
                    server_free_at = -1.0
        
        L_val = area_N_w / win_len if win_len > 0 else 0
        W_val = total_sys_w / departures_w if departures_w > 0 else 0
        bf_val = area_busy_w / win_len if win_len > 0 else 0
        pl_val = blocked_w / arrivals_w if arrivals_w > 0 else 0
        pw_val = (departures_w - sum(1 for _ in range(departures_w))) / departures_w if departures_w > 0 else 0
        # p_wait: fraction of customers who waited
        # We need to count how many had wait > 0
        # Let's track that too
        
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        server_free_at = -1.0
        arrivals_c = 0
        departures_c = 0
        blocked_c = 0
        waited_c = 0
        total_wait_c = 0.0
        total_sys_c = 0.0
        area_N_c = 0.0
        area_busy_c = 0.0
        last_t_c = 0.0
        N_c = 0
        evts_c = [(next_arrival, 'A')]
        
        while evts_c:
            evts_c.sort(key=lambda e: e[0])
            et, tp = evts_c[0][0], evts_c[0][1]
            ex = evts_c[0][2:] if len(evts_c[0]) > 2 else ()
            evts_c.pop(0)
            if et > horizon:
                break
            dt = et - last_t_c
            if last_t_c >= warmup:
                area_N_c += N_c * dt
                if N_c > 0:
                    area_busy_c += dt
            last_t_c = et
            if tp == 'A':
                arrivals_c += 1
                sd = rng.expovariate(mu)
                if N_c == 0:
                    N_c = 1
                    server_free_at = et + sd
                    evts_c.append((server_free_at, 'D', et, sd, False))
                else:
                    N_c += 1
                    queue.append((et, sd, True))
                na = et + rng.expovariate(lam)
                if na <= horizon:
                    evts_c.append((na, 'A'))
            elif tp == 'D':
                departures_c += 1
                at, sd, was_queued = ex[0], ex[1], ex[2]
                if at >= warmup:
                    w = (et - sd) - at
                    s = et - at
                    total_wait_c += w
                    total_sys_c += s
                    if was_queued or w > 1e-9:
                        waited_c += 1
                N_c -= 1
                if queue:
                    qa, qs, qw = queue.pop(0)
                    N_c += 1
                    nf = et + qs
                    server_free_at = nf
                    evts_c.append((nf, 'D', qa, qs, qw))
                else:
                    server_free_at = -1.0
        
        L_f = area_N_c / win_len if win_len > 0 else 0
        W_f = total_sys_c / departures_c if departures_c > 0 else 0
        BF_f = area_busy_c / win_len if win_len > 0 else 0
        PL_f = blocked_c / arrivals_c if arrivals_c > 0 else 0
        PW_f = waited_c / departures_c if departures_c > 0 else 0
        
        all_L.append(L_f)
        all_W.append(W_f)
        all_busy_frac.append(BF_f)
        all_p_loss.append(PL_f)
        all_p_wait.append(PW_f)
        all_arr.append(arrivals_c)
        all_blk.append(blocked_c)
        all_dep.append(departures_c)
        all_busy_util.append(BF_f)
        all_busy_occupied.append(BF_f)
        seeds_used += 1
        seed_list.append(seed)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_bf = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_pl = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    avg_pw = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_bu = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_bo = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0
    dep_rate = avg_dep / (win_len / 60.0) if win_len
