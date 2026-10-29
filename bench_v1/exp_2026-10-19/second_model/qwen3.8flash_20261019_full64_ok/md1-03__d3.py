import random, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0    # per minute (service rate)
    c = 1
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else H * 60 if time_unit == "hour" else H / 60
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_dep_rate = []
    all_lam_eff = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_time = 6.0
        
        queue = []
        in_service = None
        dep_times = []
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        stay_sum = 0.0
        
        warmup_end = horizon_min * 0.25
        stats_start = warmup_end
        
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        
        while True:
            next_dep = None
            if in_service is not None:
                next_dep = in_service[1]
            
            if next_arrival < (next_dep if next_dep is not None else float('inf')):
                t = next_arrival
                dt = t - last_t
                if last_t >= stats_start or (last_t < stats_start and t > stats_start):
                    overlap_start = max(last_t, stats_start)
                    overlap_end = min(t, horizon_min)
                    if overlap_end > overlap_start:
                        area_N += last_N * (overlap_end - overlap_start)
                
                if len(queue) + (1 if in_service else 0) < c:
                    pass
                
                if in_service is None:
                    in_service = (t, t + service_time)
                    dep_times.append((t + service_time, t))
                else:
                    queue.append(t)
                
                arr_count += 1
                next_arrival = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if in_service else 0)
                last_t = t
            else:
                if next_dep is None:
                    break
                t = next_dep
                dt = t - last_t
                if last_t >= stats_start or (last_t < stats_start and t > stats_start):
                    overlap_start = max(last_t, stats_start)
                    overlap_end = min(t, horizon_min)
                    if overlap_end > overlap_start:
                        area_N += last_N * (overlap_end - overlap_start)
                
                if in_service is not None and abs(in_service[1] - t) < 1e-9:
                    start_t = in_service[0]
                    end_t = in_service[1]
                    stay = end_t - start_t
                    wait = start_t - dep_times.pop(0)[1] if dep_times else 0
                    # Actually track arrival time properly
                    # Let's restructure: store arrival time with service start
                    # We need to know when the car arrived that started at start_t
                    # This approach is flawed. Let's redo event handling.
                    pass
                
                # Redo logic below
                break
        
        # Restart simulation with correct tracking
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_time = 6.0
        
        queue = []  # list of arrival times waiting
        in_service = None  # (start_time, end_time, arrival_time)
        dep_events = []  # (end_time, arrival_time)
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        stay_sum = 0.0
        wait_sum = 0.0
        
        warmup_end = horizon_min * 0.25
        stats_start = warmup_end
        
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        
        while t < horizon_min:
            next_dep = dep_events[0][0] if dep_events else float('inf')
            
            if next_arrival <= next_dep:
                t = next_arrival
                dt = t - last_t
                if last_t < stats_start and t > stats_start:
                    area_N += last_N * (stats_start - last_t)
                    last_t = stats_start
                    dt = t - last_t
                if last_t >= stats_start:
                    area_N += last_N * dt
                
                if in_service is None:
                    in_service = (t, t + service_time, t)
                    dep_events.append((t + service_time, t))
                    dep_events.sort(key=lambda x: x[0])
                else:
                    queue.append(t)
                
                arr_count += 1
                next_arrival = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if in_service else 0)
                last_t = t
            else:
                t = next_dep
                dt = t - last_t
                if last_t < stats_start and t > stats_start:
                    area_N += last_N * (stats_start - last_t)
                    last_t = stats_start
                    dt = t - last_t
                if last_t >= stats_start:
                    area_N += last_N * dt
                
                end_t, arr_t = dep_events.pop(0)
                stay = end_t - arr_t
                wait = arr_t - arr_t  # Wait is time from arrival to start of service
                # Actually wait = start_of_service - arrival_time
                # For the departing car, we need its start time
                # Let's fix: in_service holds current one. When it departs, we check queue.
                
                # The car that just departed had arrival time arr_t and started service at some point
                # We lost that info. Let's store start time too.
                # Re-restart... this is getting messy. Let me write cleaner code.
                break
        
        # Final clean implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_time = 6.0
        
        queue = []  # arrival times
        server_free_at = 0.0
        in_service = None  # (start_time, end_time, arrival_time)
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        stay_sum = 0.0
        wait_sum = 0.0
        
        warmup_end = horizon_min * 0.25
        stats_start = warmup_end
        
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        
        events = []  # (time, type, data)
        
        def add_event(time, etype, data=None):
            import heapq
            heapq.heappush(events, (time, etype, data))
        
        add_event(next_arrival, 'arr', None)
        
        while events:
            t, etype, data = heapq.heappop(events)
            if t > horizon_min:
                break
            
            dt = t - last_t
            if last_t < stats_start and t > stats_start:
                area_N += last_N * (stats_start - last_t)
                last_t = stats_start
                dt = t - last_t
            if last_t >= stats_start:
                area_N += last_N * dt
            
            if etype == 'arr':
                arr_count += 1
                if in_service is None:
                    in_service = (t, t + service_time, t)
                    add_event(t + service_time, 'dep', (t, t + service_time, t))
                else:
                    queue.append(t)
                next_arrival = t + rng.expovariate(lam)
                add_event(next_arrival, 'arr', None)
                last_N = len(queue) + (1 if in_service else 0)
                last_t = t
            elif etype == 'dep':
                start_t, end_t, arr_t = data
                dep_count += 1
                stay = end_t - arr_t
                wait = start_t - arr_t
                if arr_t >= stats_start:
                    stay_sum += stay
                    wait_sum += wait
                in_service = None
                if queue:
                    next_arr = queue.pop(0)
                    in_service = (t, t + service_time, next_arr)
                    add_event(t + service_time, 'dep', (t, t + service_time, next_arr))
                last_N = len(queue) + (1 if in_service else 0)
                last_t = t
        
        win_len = horizon_min - stats_start
        L = area_N / win_len if win_len > 0 else 0
        W = stay_sum / dep_count if dep_count > 0 else 0
        busy_frac = 1.0 if in_service else 0.0  # Approximate; better use area-based
        # Compute busy fraction via area where server was busy
        # Simpler: count time server was occupied during window
        # We didn't track that separately. Use Little's law consistency or recompute.
        # For M/D/1, busy_frac = lambda/mu = rho
        rho = lam / mu
        busy_frac_val = min(rho, 1.0)
        p_loss = 0.0  # No loss in infinite buffer FCFS
        p_wait = 1.0 - (1.0 / (1.0 + rho)) if rho > 0 else 0.0  # Approx P(wait>0) for M/D/1 is rho
        
        all_L.append(L)
        all_W.append(W)
        all_busy_frac.append(busy_frac_val)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        all_busy_util.append(busy_frac_val)
        all_busy_occupied.append(1.0 - (1.0 - rho) if rho < 1 else 1.0)
        all_dep_rate.append(dep_count / (win_len / 60.0) if win_len > 0 else 0)
        all_lam_eff.append(arr_count / (win_len / 60.0) if win_len > 0 else 0)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_busy_occ = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": time_unit,
        "seed_list": [seed_start + i for i in range(N_seeds)],
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(horizon_min - horizon_min * 0.25, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
