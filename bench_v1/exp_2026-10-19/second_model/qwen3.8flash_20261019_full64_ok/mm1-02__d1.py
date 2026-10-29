import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam = 4.0
    mu = 12.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        t = 0.0
        N = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        # For W calculation: track arrival times of customers currently in system
        # and their service durations (pre-drawn at arrival)
        cust_in_sys = []  # list of (arrival_time, service_duration)
        
        # Statistics accumulators over the whole run, but we only integrate from win_start
        area_N = 0.0
        last_stat_t = 0.0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0  # number who had to wait (arrival found server busy)
        
        # We need to compute L as time-average of N over window
        # And W as average sojourn time of customers departing in window? 
        # Or Little's law based? The problem asks for steady-state estimates via simulation.
        # Typically W is estimated by averaging sojourn times of customers that complete service within the window, or all customers that arrived and departed. Let's use customers that depart during the statistical window.
        
        # Actually, standard approach: 
        # L = (integral of N(t) dt over window) / window_length
        # W = (sum of sojourn times of customers departing in window) / (number of such customers)
        # But this can be biased. Alternative: use all customers that arrive and depart fully within window? 
        # Let's stick with: L from area integral, W from average sojourn time of customers whose departure falls in window.
        
        # To get sojourn times, when a customer departs, we know their arrival time.
        # We'll collect sojourn times for departures in window.
        
        sojourn_times_window = []
        
        # Track state changes for integration
        prev_t = 0.0
        prev_N = 0
        
        while t < horizon:
            # Determine next event
            if next_arr <= next_dep:
                # Arrival
                t = next_arr
                # Integrate N from prev_t to t
                if t > win_start:
                    seg_start = max(prev_t, win_start)
                    if t > seg_start:
                        area_N += prev_N * (t - seg_start)
                
                # Process arrival
                if N < 1:
                    # Server free, start service immediately
                    svc_dur = rng.expovariate(mu)
                    next_dep = t + svc_dur
                    cust_in_sys.append((t, svc_dur))
                    N += 1
                    arr_count += 1
                    # No wait
                else:
                    # Server busy -> blocked/lost since single server no queue? 
                    # Wait, M/M/1 has infinite queue capacity typically. "打印店只有1名值班员" usually implies M/M/1 with queue.
                    # If it were M/M/1/1 (no queue), then arrivals when busy are lost.
                    # Standard M/M/1 assumes queue exists. Let's assume M/M/1 with infinite queue.
                    # So arrival joins queue.
                    svc_dur = rng.expovariate(mu)
                    cust_in_sys.append((t, svc_dur))
                    N += 1
                    arr_count += 1
                    wait_count += 1  # Had to wait because server was busy
                    
                prev_t = t
                prev_N = N
                next_arr = t + rng.expovariate(lam)
            else:
                # Departure
                t = next_dep
                if t > win_start:
                    seg_start = max(prev_t, win_start)
                    if t > seg_start:
                        area_N += prev_N * (t - seg_start)
                
                # Process departure
                if not cust_in_sys:
                    # Shouldn't happen if logic correct
                    break
                
                # Find the customer being served. In FCFS, it's the first one.
                # But we pre-drew service duration at arrival. The one at front of queue starts service when server becomes free.
                # This model needs careful handling. 
                # Simpler: maintain queue of waiting customers and one in service.
                # Let me restructure slightly mentally but keep code compact.
                # Actually, let's use a different approach: 
                # Keep track of when each customer enters service.
                # When server becomes free, take next from queue, set their service end time.
                
                # Let me rewrite the loop logic more carefully.
                pass
            
            # This is getting complex inline. Let me restart the inner loop with clearer structure.
            break
        
        # I need to redo the simulation loop properly.
        # Reset and do it right.
        rng = random.Random(seed)
        t = 0.0
        N = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        # Queue: list of (arrival_time, service_duration) for those waiting
        # In-service: None or (arrival_time, service_duration, service_end_time)
        in_service = None
        queue = []
        
        area_N = 0.0
        prev_t = 0.0
        prev_N = 0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        
        sojourn_times_window = []
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                if t > win_start:
                    seg_start = max(prev_t, win_start)
                    if t > seg_start:
                        area_N += prev_N * (t - seg_start)
                
                svc_dur = rng.expovariate(mu)
                arr_count += 1
                
                if in_service is None:
                    # Start service immediately
                    in_service = (t, svc_dur, t + svc_dur)
                    next_dep = t + svc_dur
                    N += 1
                else:
                    # Join queue
                    queue.append((t, svc_dur))
                    N += 1
                    wait_count += 1
                
                prev_t = t
                prev_N = N
                next_arr = t + rng.expovariate(lam)
            else:
                t = next_dep
                if t > win_start:
                    seg_start = max(prev_t, win_start)
                    if t > seg_start:
                        area_N += prev_N * (t - seg_start)
                
                # Complete service
                if in_service is not None:
                    arr_t, svc_dur, _ = in_service
                    sojourn = t - arr_t
                    if t >= win_start:
                        sojourn_times_window.append(sojourn)
                    dep_count += 1
                    N -= 1
                    in_service = None
                    
                    # Start next from queue if any
                    if queue:
                        next_cust = queue.pop(0)
                        arr_t_q, svc_dur_q = next_cust
                        in_service = (arr_t_q, svc_dur_q, t + svc_dur_q)
                        next_dep = t + svc_dur_q
                    else:
                        next_dep = float('inf')
                
                prev_t = t
                prev_N = N
        
        # Final integration up to horizon
        if horizon > win_start:
            seg_start = max(prev_t, win_start)
            if horizon > seg_start:
                area_N += prev_N * (horizon - seg_start)
        
        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = sum(sojourn_times_window) / len(sojourn_times_window) if sojourn_times_window else 0.0
        # Convert W to minutes: internal time unit is hour, so multiply by 60
        W_min = W_est * 60.0
        
        busy_frac_est = 1.0 - (area_N / win_len) / 1.0 if False else 0.0
        # Busy fraction: proportion of time server is busy
        # We didn't track busy time directly. Let's estimate from L and rho? No.
        # Better: track busy time.
        # Since I already ran the loop, let me just approximate busy_frac as min(L/rho, 1)? Not accurate.
        # Let me add busy time tracking. But I'm constrained on lines.
        # Alternative: busy_frac ≈ 1 - P(N=0). We can estimate P(N=0) from area where N==0.
        # I didn't track that either.
        # Given constraints, let's use theoretical relation for validation but report simulated.
        # Actually, let's just compute busy time by noting that whenever in_service is not None, server is busy.
        # I'll modify the loop to track busy_area.
        
        # Due to line limit, I'll make a simplified version that tracks busy time.
        # Restarting with minimal code...
        
        # Let me just output reasonable values based on theory for stability check, 
        # but the task requires simulation.
        
        # I will implement a cleaner short version now.
        pass
    
    # Given complexity and line limits, here is a concise working implementation:
    results = {}
    total_L = 0.0
    total_W = 0.0
    total_busy = 0.0
    total_pwait = 0.0
    total_arr = 0.0
    total_dep = 0.0
    total_blk = 0.0
    total_busyutil = 0.0
    total_busyocc = 0.0
    total_deprate = 0.0
    total_lameff = 0.0
    total_ploss = 0.0
    
    ps_L = []
    ps_W = []
    ps_bf = []
    ps_pl = []
    ps_pw = []
    
    for seed in seed_list:
        rng = random.Random(seed)
        t = 0.0
        N = 0
        na = rng.expovariate(lam)
        nd = float('inf')
        q = []
        ins = None
        areaN = 0.0
        pt = 0.0
        pn = 0
        ac = 0
        dc = 0
        bc = 0
        wc = 0
        stw = []
        busy_area = 0.0
        pbn = 0.0
        
        while t < horizon:
            if na <= nd:
                t = na
                if t > win_start:
                    sa = max(pt, win_start)
                    if t > sa:
                        areaN += pn * (t - sa)
                        if pbn > 0:
                            busy_area += (t - sa)
                sd = rng.expovariate(mu)
                ac += 1
                if ins is None:
                    ins = (t, sd, t + sd)
                    nd = t + sd
                    N += 1
                    pbn = 1
                else:
                    q.append((t, sd))
                    N += 1
                    wc += 1
                pt = t
                pn = N
                na = t + rng.expovariate(lam)
            else:
                t = nd
                if t > win_start:
                    sa = max(pt, win_start)
                    if t > sa:
                        areaN += pn * (t - sa)
                        if pbn > 0:
                            busy_area += (t - sa)
                if ins:
                    at, sd, _ = ins
                    soj = t - at
                    if t >= win_start:
                        stw.append(soj)
                    dc += 1
                    N -= 1
                    ins = None
                    pbn = 0
                    if q:
                        nt, nsd = q.pop(0)
                        ins = (nt, nsd, t + nsd)
                        nd = t + nsd
                        pbn = 1
                    else:
                        nd = float('inf')
                pt = t
                pn = N
        
        if horizon > win_start:
            sa = max(pt, win_start)
            if horizon > sa:
                areaN += pn * (horizon - sa)
                if pbn > 0:
                    busy_area += (horizon - sa)
        
        Ls = areaN / win_len
        Ws = (sum(stw)/len(stw)*60) if stw else 0
        bfs = busy_area / win_len
        pws = wc / ac if ac else 0
        pls = bc / ac if ac else 0
        
        ps_L.append(Ls)
        ps_W.append(Ws)
        ps_bf.append(bfs)
        ps_pl.append(pls)
        ps_pw.append(pws)
        
        total_L += Ls
        total_W += Ws
        total_busy += bfs
        total_pwait += pws
        total_arr += ac
        total_dep += dc
        total_blk += bc
        total_busyutil += bfs
        total_busyocc += bfs
        total_deprate += dc / win_len
        total_lameff += ac / win_len
        total_ploss += pls
    
    n = seeds_used
    out = {
        "L": total_L/n,
        "W": total_W/n,
        "busy_frac": total_busy/n,
        "p_wait": total_pwait/n,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win_len,
        "arr": total_arr/n,
        "blk": total_blk/n,
        "busy_util": total_busyutil/n,
        "dep": total_dep/n,
        "dep_rate": total_deprate/n,
        "lam_eff": total_lameff/n,
        "p_loss": total_ploss/n,
        "per_seed_L": ps_L,
        "per_seed_W": ps_W,
        "per_seed_busy_frac": ps_bf,
        "per_seed_p_loss": ps_pl,
        "per_seed_p_wait": ps_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
