import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 8.0
    mu_base = 60.0 / 5.0
    
    if args.pert == 'lam_up': lam = lam_base * 1.2
    elif args.pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif args.pert == 'c_up': c = 4 + 1; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base; c = 4

    if args.pert != 'c_up': c = 4
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
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
    total_busy_time = 0
    total_wait_time = 0
    total_service_time = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] 
        service_end = float('inf')
        busy = False
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_sum = 0.0
        service_sum = 0.0
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        
        while t < horizon:
            if not queue and service_end == float('inf'):
                t = next_arr
            else:
                t = min(next_arr, service_end)
            
            dt = t - last_t
            if t > win_start:
                area_N += last_N * dt
            
            if t >= service_end and service_end != float('inf'):
                dep_count += 1
                service_sum += (service_end - queue[0][1]) 
                queue.pop(0)
                if queue:
                    service_end = t + rng.expovariate(mu)
                    busy = True
                else:
                    service_end = float('inf')
                    busy = False
                last_N = len(queue) + (1 if busy else 0)
                
            if t >= next_arr:
                arr_count += 1
                n_now = len(queue) + (1 if busy else 0)
                if n_now < c:
                    svc_dur = rng.expovariate(mu)
                    queue.append((t, t)) 
                    if not busy:
                        busy = True
                        service_end = t + svc_dur
                        queue[0] = (queue[0][0], t) 
                    last_N = len(queue) + (1 if busy else 0)
                else:
                    blk_count += 1
                
                next_arr = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if busy else 0)
            
            last_t = t
            
        if t > win_start:
             pass 

        L_est = area_N / win_len if win_len > 0 else 0
        W_est = (wait_sum + service_sum) / dep_count if dep_count > 0 else 0
        # Wait is arrival to start of service? Or arrival to departure?
        # Standard W is sojourn time (arrival to departure).
        # Let's re-calculate properly.
        
        # Reset accumulators for correct calculation logic inside loop was flawed for W.
        # Re-run simple simulation for this seed with correct tracking.
        
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] 
        service_end = float('inf')
        busy = False
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sojourn_sum = 0.0
        area_N = 0.0
        last_t = 0.0
        last_N = 0
        
        while t < horizon:
            if not queue and service_end == float('inf'):
                t = next_arr
            else:
                t = min(next_arr, service_end)
            
            dt = t - last_t
            if t > win_start:
                area_N += last_N * dt
            
            if t >= service_end and service_end != float('inf'):
                dep_count += 1
                sojourn_sum += (service_end - queue[0][1])
                queue.pop(0)
                if queue:
                    service_end = t + rng.expovariate(mu)
                    busy = True
                else:
                    service_end = float('inf')
                    busy = False
                last_N = len(queue) + (1 if busy else 0)
                
            if t >= next_arr:
                arr_count += 1
                n_now = len(queue) + (1 if busy else 0)
                if n_now < c:
                    svc_dur = rng.expovariate(mu)
                    queue.append((t, t)) 
                    if not busy:
                        busy = True
                        service_end = t + svc_dur
                        queue[0] = (queue[0][0], t) 
                    last_N = len(queue) + (1 if busy else 0)
                else:
                    blk_count += 1
                
                next_arr = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if busy else 0)
            
            last_t = t
            
        L_est = area_N / win_len if win_len > 0 else 0
        W_est = sojourn_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = 1.0 - (area_N / win_len - (len(queue)+1)/win_len*0) # Approximation via N>0 area?
        # Better: track busy time directly
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] 
        service_end = float('inf')
        busy = False
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sojourn_sum = 0.0
        area_N = 0.0
        busy_area = 0.0
        last_t = 0.0
        last_N = 0
        last_busy = False
        
        while t < horizon:
            if not queue and service_end == float('inf'):
                t = next_arr
            else:
                t = min(next_arr, service_end)
            
            dt = t - last_t
            if t > win_start:
                area_N += last_N * dt
                if last_busy:
                    busy_area += dt
            
            if t >= service_end and service_end != float('inf'):
                dep_count += 1
                sojourn_sum += (service_end - queue[0][1])
                queue.pop(0)
                if queue:
                    service_end = t + rng.expovariate(mu)
                    busy = True
                else:
                    service_end = float('inf')
                    busy = False
                last_N = len(queue) + (1 if busy else 0)
                last_busy = busy
                
            if t >= next_arr:
                arr_count += 1
                n_now = len(queue) + (1 if busy else 0)
                if n_now < c:
                    svc_dur = rng.expovariate(mu)
                    queue.append((t, t)) 
                    if not busy:
                        busy = True
                        service_end = t + svc_dur
                        queue[0] = (queue[0][0], t) 
                    last_N = len(queue) + (1 if busy else 0)
                    last_busy = busy
                else:
                    blk_count += 1
                
                next_arr = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if busy else 0)
                last_busy = busy
            
            last_t = t
            
        L_est = area_N / win_len if win_len > 0 else 0
        W_est = sojourn_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = busy_area / win_len if win_len > 0 else 0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0
        p_wait_est = (dep_count - 1) / dep_count if dep_count > 0 else 0 # Rough proxy or exact?
        # Exact P(wait): fraction of arrivals that waited. Need to track.
        
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] 
        service_end = float('inf')
        busy = False
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sojourn_sum = 0.0
        area_N = 0.0
        busy_area = 0.0
        wait_count = 0
        last_t = 0.0
        last_N = 0
        last_busy = False
        
        while t < horizon:
            if not queue and service_end == float('inf'):
                t = next_arr
            else:
                t = min(next_arr, service_end)
            
            dt = t - last_t
            if t > win_start:
                area_N += last_N * dt
                if last_busy:
                    busy_area += dt
            
            if t >= service_end and service_end != float('inf'):
                dep_count += 1
                sojourn_sum += (service_end - queue[0][1])
                queue.pop(0)
                if queue:
                    service_end = t + rng.expovariate(mu)
                    busy = True
                else:
                    service_end = float('inf')
                    busy = False
                last_N = len(queue) + (1 if busy else 0)
                last_busy = busy
                
            if t >= next_arr:
                arr_count += 1
                n_now = len(queue) + (1 if busy else 0)
                if n_now < c:
                    svc_dur = rng.expovariate(mu)
                    queue.append((t, t)) 
                    if not busy:
                        busy = True
                        service_end = t + svc_dur
                        queue[0] = (queue[0][0], t) 
                    else:
                        wait_count += 1
                    last_N = len(queue) + (1 if busy else 0)
                    last_busy = busy
                else:
                    blk_count += 1
                
                next_arr = t + rng.expovariate(lam)
                last_N = len(queue) + (1 if busy else 0)
                last_busy = busy
            
            last_t = t
            
        L_est = area_N / win_len if win_len > 0 else 0
        W_est = sojourn_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = busy_area / win_len if win_len > 0 else 0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0
        p_wait_est = wait_count / arr_count if arr_count > 0 else 0
        
        seeds_used.append(seed)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += arr_count
        total_blk += blk_count
        total_dep += dep_count
        total_busy_time += busy_area
        total_wait_time += sojourn_sum # This is sum of sojourn times
        
    avg_L = sum(per_seed_L) / len(per_seed_L)
    avg_W = sum(per_seed_W) / len(per_seed_W)
    avg_busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    avg_p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    avg_p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)
    
    avg_arr = total_arr / len(seeds_used)
    avg_blk = total_blk / len(seeds_used)
    avg_dep = total_dep / len(seeds_used)
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    busy_util = avg_busy_frac / 1.0 # c=1
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W * 60, 4), # Convert hours to minutes
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "hours",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
