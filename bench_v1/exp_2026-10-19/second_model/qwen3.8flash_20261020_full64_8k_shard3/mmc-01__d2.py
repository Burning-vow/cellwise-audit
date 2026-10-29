import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0
    mu_base = 5.0
    c = 2
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif a.pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
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
    seed_list = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        service_times = {}
        dep_events = []
        
        area_n = 0.0
        area_min_nc = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        total_time_sum = 0.0
        
        while t < horizon:
            # Determine next event
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if dep_events:
                events.append(('dep', min(dep_events)))
            
            if not events:
                break
            
            etype, etime = min(events, key=lambda x: x[1])
            
            # Integrate before state change
            dt = etime - t
            if t >= win_start:
                area_n += n * dt
                busy_now = min(n, c)
                area_min_nc += busy_now * dt
            
            t = etime
            
            if etype == 'arr':
                arr_count += 1
                if n < c:
                    st = rng.expovariate(mu)
                    service_times[n] = (t, st)
                    dep_events.append(t + st)
                    n += 1
                else:
                    # Queue or block? FCFS with infinite queue assumed unless specified otherwise
                    # But problem says "bank branch with 2 counters", typically finite capacity not mentioned -> assume infinite queue
                    # However, we need to track waiting customers. Let's use a list for queue.
                    pass
                
                # Actually, let's restructure: maintain queue explicitly
                # Reset approach: use a proper DES loop with explicit queue
                break  # Will rewrite below
            
        # Rewrite with cleaner structure
        rng = random.Random(seed)
        t = 0.0
        queue = []  # list of arrival times
        serving = []  # list of (start_time, end_time)
        next_arr = rng.expovariate(lam)
        
        area_n = 0.0
        area_min_nc = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        total_time_sum = 0.0
        num_in_system_at_arrival = 0
        waited_flag = False
        
        while t < horizon:
            # Find next departure
            next_dep = float('inf')
            dep_idx = -1
            for idx, (st, et) in enumerate(serving):
                if et < next_dep:
                    next_dep = et
                    dep_idx = idx
            
            # Next event time
            next_event = min(next_arr, next_dep)
            if next_event > horizon:
                # Advance to horizon and integrate
                dt = horizon - t
                if t >= win_start:
                    n_cur = len(queue) + len(serving)
                    area_n += n_cur * dt
                    area_min_nc += min(n_cur, c) * dt
                t = horizon
                break
            
            dt = next_event - t
            n_cur = len(queue) + len(serving)
            if t >= win_start:
                area_n += n_cur * dt
                area_min_nc += min(n_cur, c) * dt
            t = next_event
            
            if t == next_arr:
                arr_count += 1
                # Check if any server free
                if len(serving) < c:
                    st = rng.expovariate(mu)
                    serving.append((t, t + st))
                    # No wait
                    if t >= win_start:
                        total_time_sum += st
                else:
                    queue.append(t)
                    # Will compute wait later on departure
                next_arr = t + rng.expovariate(lam)
            
            elif t == next_dep:
                dep_count += 1
                # Remove the departing customer
                serving.pop(dep_idx)
                # If queue non-empty, start next service
                if queue:
                    arr_t = queue.pop(0)
                    st = rng.expovariate(mu)
                    serving.append((t, t + st))
                    if t >= win_start:
                        w = t - arr_t
                        total_time_sum += w + st
                else:
                    # A customer left without replacement from queue
                    # This customer was already accounted for when they started service
                    pass
        
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = total_time_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = area_min_nc / (win_len * c) if win_len > 0 and c > 0 else 0
        p_wait_est = 0.0  # Need to track arrivals that had to queue
        
        # Recompute p_wait properly during simulation
        # Let's redo with p_wait tracking
        rng = random.Random(seed)
        t = 0.0
        queue = []
        serving = []
        next_arr = rng.expovariate(lam)
        area_n = 0.0
        area_min_nc = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        total_time_sum = 0.0
        p_wait_count = 0
        
        while t < horizon:
            next_dep = float('inf')
            dep_idx = -1
            for idx, (st, et) in enumerate(serving):
                if et < next_dep:
                    next_dep = et
                    dep_idx = idx
            
            next_event = min(next_arr, next_dep)
            if next_event > horizon:
                dt = horizon - t
                if t >= win_start:
                    n_cur = len(queue) + len(serving)
                    area_n += n_cur * dt
                    area_min_nc += min(n_cur, c) * dt
                t = horizon
                break
            
            dt = next_event - t
            n_cur = len(queue) + len(serving)
            if t >= win_start:
                area_n += n_cur * dt
                area_min_nc += min(n_cur, c) * dt
            t = next_event
            
            if abs(t - next_arr) < 1e-9:
                arr_count += 1
                if len(serving) < c:
                    st = rng.expovariate(mu)
                    serving.append((t, t + st))
                    if t >= win_start:
                        total_time_sum += st
                else:
                    queue.append(t)
                    if t >= win_start:
                        p_wait_count += 1
                next_arr = t + rng.expovariate(lam)
            
            elif abs(t - next_dep) < 1e-9:
                dep_count += 1
                serving.pop(dep_idx)
                if queue:
                    arr_t = queue.pop(0)
                    st = rng.expovariate(mu)
                    serving.append((t, t + st))
                    if t >= win_start:
                        w = t - arr_t
                        total_time_sum += w + st
        
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = total_time_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = area_min_nc / (win_len * c) if win_len > 0 and c > 0 else 0
        p_wait_est = p_wait_count / arr_count if arr_count > 0 else 0
        busy_util_est = busy_frac_est
        dep_rate_est = dep_count / win_len if win_len > 0 else 0
        lam_eff_est = arr_count / win_len if win_len > 0 else 0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        seed_list.append(seed)
    
    seeds_used = len(per_seed_L)
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used > 0 else 0
    avg_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0
    avg_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0
    avg_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0
    avg_busy_util = sum(all_busy_util) / seeds_used if seeds_used > 0 else 0
    avg_dep_rate = sum(all_dep_rate) / seeds_used if seeds_used > 0 else 0
    avg_lam_eff = sum(all_lam_eff) / seeds_used if seeds_used > 0 else 0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used > 0 else 0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
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
    print(json.dumps(result))

if __name__ == "__main__":
    main()
