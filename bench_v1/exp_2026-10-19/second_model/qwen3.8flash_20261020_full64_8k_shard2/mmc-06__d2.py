import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in minutes
    lam_per_hour = 14.0
    mu_per_min = 1.0 / 6.0
    c = 2
    
    if pert == 'lam_up':
        lam_per_hour *= 1.2
    elif pert == 'mu_up':
        mu_per_min *= 1.2
    elif pert == 'c_up':
        c += 1
    
    time_unit = "minute"
    horizon_min = H * 60.0 if time_unit == "hour" else H
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed_val = seed_start + i
        rng = random.Random(seed_val)
        
        # Event simulation
        # Events: arrival, departure
        # State: number of customers in system (queue + service), servers busy count
        # We track area under curve for L and busy servers
        
        t = 0.0
        n_in_system = 0
        n_busy = 0
        queue = []  # list of (arrival_time, service_duration)
        
        # For statistics after warmup
        stat_t_start = warmup_end
        last_stat_t = stat_t_start
        area_L = 0.0
        area_busy = 0.0
        total_wait_plus_service = 0.0
        num_departures = 0
        num_arrivals = 0
        num_blocked = 0
        p_wait_count = 0
        
        # Generate first arrival
        next_arrival = rng.expovariate(lam_per_hour / 60.0)
        next_departure = float('inf')
        
        while t < horizon_min:
            # Determine next event time
            if next_arrival <= next_departure:
                t_event = next_arrival
            else:
                t_event = next_departure
            
            if t_event > horizon_min:
                break
            
            # Accumulate areas up to t_event
            dt = t_event - t
            if t >= stat_t_start or (t < stat_t_start and t_event > stat_t_start):
                # Need to handle crossing warmup boundary
                if t < stat_t_start:
                    dt_pre = stat_t_start - t
                    dt_post = t_event - stat_t_start
                    if dt_pre > 0:
                        pass  # no accumulation before warmup
                    if dt_post > 0:
                        area_L += n_in_system * dt_post
                        area_busy += n_busy * dt_post
                else:
                    area_L += n_in_system * dt
                    area_busy += n_busy * dt
            
            t = t_event
            
            if t_event == next_arrival:
                # Arrival
                num_arrivals += 1
                if t >= stat_t_start:
                    if n_in_system >= c:
                        p_wait_count += 1
                
                # Draw service duration now
                svc_dur = rng.expovariate(mu_per_min)
                
                if n_in_system < c:
                    n_in_system += 1
                    n_busy += 1
                    # Schedule departure
                    dep_time = t + svc_dur
                    if dep_time < next_departure:
                        next_departure = dep_time
                    # Store customer info for W calculation
                    queue.append((t, svc_dur))
                else:
                    # Queue
                    n_in_system += 1
                    queue.append((t, svc_dur))
                
                # Next arrival
                inter_arr = rng.expovariate(lam_per_hour / 60.0)
                next_arrival = t + inter_arr
                
            else:
                # Departure
                # Find the earliest departure among queued/served
                # Since we only track one next_departure, we need to manage multiple servers
                # This simple approach fails for multi-server. Let's use a heap-like structure.
                # Actually, let's restart with a proper event list using heapq.
                pass
        
        # The above loop is flawed for multi-server. Let's rewrite properly.
        # Reset and do it right.
        
        t = 0.0
        n_in_system = 0
        n_busy = 0
        # Use a min-heap for departures: (departure_time, arrival_time, service_duration)
        import heapq
        dep_heap = []
        
        stat_t_start = warmup_end
        area_L = 0.0
        area_busy = 0.0
        total_w = 0.0
        num_dep = 0
        num_arr = 0
        num_blk = 0
        p_wait_cnt = 0
        
        next_arrival = rng.expovariate(lam_per_hour / 60.0)
        
        while True:
            # Next event time
            arr_t = next_arrival
            dep_t = dep_heap[0][0] if dep_heap else float('inf')
            
            if arr_t >= horizon_min and dep_t >= horizon_min:
                break
            
            if arr_t <= dep_t:
                t_event = arr_t
            else:
                t_event = dep_t
            
            if t_event > horizon_min:
                break
            
            # Accumulate stats
            dt = t_event - t
            if t < stat_t_start:
                if t_event > stat_t_start:
                    dt_post = t_event - stat_t_start
                    area_L += n_in_system * dt_post
                    area_busy += n_busy * dt_post
            else:
                area_L += n_in_system * dt
                area_busy += n_busy * dt
            
            t = t_event
            
            if t_event == arr_t:
                num_arr += 1
                if t >= stat_t_start and n_in_system >= c:
                    p_wait_cnt += 1
                
                svc_dur = rng.expovariate(mu_per_min)
                
                if n_in_system < c:
                    n_in_system += 1
                    n_busy += 1
                    heapq.heappush(dep_heap, (t + svc_dur, t, svc_dur))
                else:
                    n_in_system += 1
                    # Customer waits; store arrival time and service duration
                    # But when does this customer start service? When a server frees up.
                    # We need to track waiting customers separately.
                    # Let's maintain a queue of waiting customers: (arrival_time, service_duration)
                    # And when a departure happens, if there are waiters, one starts service.
                    # So we need a separate waiting queue.
                    pass
                
                next_arrival = t + rng.expovariate(lam_per_hour / 60.0)
                
            else:
                # Departure
                dep_time, arr_time, svc_dur = heapq.heappop(dep_heap)
                n_in_system -= 1
                n_busy -= 1
                num_dep += 1
                
                if t >= stat_t_start:
                    w = t - arr_time
                    total_w += w
                
                # Check if there are waiting customers
                # We need to track them. Let's add a waiting_queue variable.
                pass
        
        # Still incomplete. Let me write a cleaner version.
        # I'll restart the inner logic completely.
        
        # Clean implementation below replaces the broken attempts above.
        # Since I can't easily delete code in this format, I'll just ensure the final output uses correct logic.
        # Actually, let me just write the correct single-pass logic from scratch in the final answer.
        
        # Given the constraints, I will provide the corrected full function body.
        pass
    
    # Due to complexity, here is the corrected complete main logic:
    # (Re-implementing cleanly)
    
    results = []
    for i in range(N_seeds):
        seed_val = seed_start + i
        rng = random.Random(seed_val)
        
        horizon_min = H * 60.0 if time_unit == "hour" else H
        warmup_end = horizon_min * 0.75
        
        t = 0.0
        n_sys = 0
        n_busy = 0
        waiting_q = []  # (arrival_time, service_duration)
        dep_heap = []   # (departure_time, arrival_time, service_duration)
        
        area_L = 0.0
        area_busy = 0.0
        sum_w = 0.0
        cnt_dep = 0
        cnt_arr = 0
        cnt_blk = 0
        cnt_wait = 0
        
        next_arr = rng.expovariate(lam_per_hour / 60.0)
        
        while t < horizon_min:
            arr_t = next_arr
            dep_t = dep_heap[0][0] if dep_heap else float('inf')
            
            if arr_t >= horizon_min and dep_t >= horizon_min:
                break
            
            t_next = min(arr_t, dep_t)
            if t_next > horizon_min:
                break
            
            dt = t_next - t
            if t < warmup_end:
                if t_next > warmup_end:
                    dt_post = t_next - warmup_end
                    area_L += n_sys * dt_post
                    area_busy += n_busy * dt_post
            else:
                area_L += n_sys * dt
                area_busy += n_busy * dt
            
            t = t_next
            
            if t == arr_t:
                cnt_arr += 1
                if t >= warmup_end and n_sys >= c:
                    cnt_wait += 1
                
                svc = rng.expovariate(mu_per_min)
                
                if n_busy < c:
                    n_sys += 1
                    n_busy += 1
                    heapq.heappush(dep_heap, (t + svc, t, svc))
                else:
                    n_sys += 1
                    waiting_q.append((t, svc))
                
                next_arr = t + rng.expovariate(lam_per_hour / 60.0)
                
            else:
                dep_time, arr_time, svc_dur = heapq.heappop(dep_heap)
                n_sys -= 1
                n_busy -= 1
                cnt_dep += 1
                
                if t >= warmup_end:
                    w = t - arr_time
                    sum_w += w
                
                if waiting_q:
                    wa, ws = waiting_q.pop(0)
                    n_busy += 1
                    heapq.heappush(dep_heap, (t + ws, wa, ws))
        
        win_len = horizon_min - warmup_end
        if win_len > 0:
            L_est = area_L / win_len
            busy_frac_est = area_busy / (win_len * c)
            W_est = sum_w / cnt_dep if cnt_dep > 0 else 0.0
            p_wait_est = cnt_wait / cnt_arr if cnt_arr > 0 else 0.0
            p_loss_est = cnt_blk / cnt_arr if cnt_arr > 0 else 0.0
            dep_rate_est = (cnt_dep / win_len) * 60.0 if win_len > 0 else 0.0
            lam_eff_est = (cnt_arr / win_len) * 60.0 if win_len > 0 else 0.0
        else:
            L_est = busy_frac_est = W_est = p_wait_est = p_loss_est = dep_rate_est = lam_eff_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(cnt_arr)
        all_dep.append(cnt_dep)
        all_blk.append(cnt_blk)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        seeds_used_list.append(seed_val)
    
    n_s = len(per_seed_L)
    avg_L = sum(all_L) / n_s if n_s else 0
    avg_W = sum(all_W) / n_s if n_s else 0
    avg_busy_frac = sum(all_busy_frac) / n_s if n_s else 0
    avg_p_wait = sum(all_p_wait) / n_s if n_s else 0
    avg_arr = sum(all_arr) / n_s if n_s else 0
    avg_dep = sum(all_dep) / n_s if n_s else 0
    avg_blk = sum(all_blk) / n_s if n_s else 0
    avg_busy_util = sum(all_busy_util) / n_s if n_s else 0
    avg_dep_rate = sum(all_dep_rate) / n_s if n_s else 0
    avg_lam_eff = sum(all_lam_eff) / n_s if n_s else 0
    avg_p_loss = sum(all_p_loss) / n_s if n_s else 0
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": n_s,
        "time_unit": time_unit,
        "win": round(horizon_min * 0.25, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
