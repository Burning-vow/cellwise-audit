import sys, json, random, math
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 10; horizon = 100.0; seed_start = 1; pert = "none"
    for i in range(0, len(args), 2):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]
    
    lam_base = 6.0; mu_base = 5.0; c = 3; K = 4
    time_unit = "hour"
    
    if pert == "lam_up": lam = lam_base * 1.2
    elif pert == "mu_up": mu = mu_base * 1.2
    elif pert == "c_up": c = 4
    else: lam = lam_base; mu = mu_base
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    total_arr = 0; total_blk = 0; total_dep = 0; total_time_active = 0.0; total_time_total = 0.0
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers = [0.0] * c 
        queue = deque() 
        n_in_system = 0 
        
        warmup_end = horizon * 0.25
        
        area_L = 0.0
        area_W_num = 0.0 
        count_W_den = 0  
        time_busy = 0.0 
        last_event_t = 0.0
        prev_n = 0
        
        arr_count = 0; blk_count = 0; dep_count = 0
        
        while t < horizon:
            events = []
            if next_arrival <= horizon:
                events.append((next_arrival, 'A'))
            for i in range(c):
                if servers[i] > t and servers[i] <= horizon:
                    events.append((servers[i], 'D', i))
            
            if not events: break
            
            events.sort(key=lambda x: (x[0], x[1]))
            ev_t, ev_type = events[0][0], events[0][1]
            srv_idx = events[0][2] if ev_type == 'D' else -1
            
            dt = ev_t - last_event_t
            if last_event_t >= warmup_end:
                area_L += prev_n * dt
                if prev_n > 0:
                    time_busy += dt
            
            last_event_t = ev_t
            
            if ev_type == 'A':
                arr_count += 1
                if n_in_system < K:
                    free_srv = -1
                    for i in range(c):
                        if servers[i] <= t:
                            free_srv = i; break
                    
                    service_time = rng.expovariate(mu)
                    
                    if free_srv != -1:
                        servers[free_srv] = t + service_time
                        start_t = t
                    else:
                        queue.append((t, service_time))
                        start_t = None 
                    
                    n_in_system += 1
                    prev_n = n_in_system
                    if start_t is not None:
                        pass 
                else:
                    blk_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif ev_type == 'D':
                dep_count += 1
                servers[srv_idx] = 0.0 
                
                if queue:
                    arrival_t, svc_dur = queue.popleft()
                    servers[srv_idx] = t + svc_dur
                    wait_time = t - arrival_t
                    area_W_num += wait_time
                    count_W_den += 1
                else:
                    n_in_system -= 1
                    prev_n = n_in_system
                
                t = ev_t 

        if last_event_t < horizon:
             dt = horizon - last_event_t
             if last_event_t >= warmup_end:
                 area_L += prev_n * dt
                 if prev_n > 0:
                     time_busy += dt
             last_event_t = horizon

        win_len = horizon - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_L / win_len
        W_est = area_W_num / count_W_den if count_W_den > 0 else 0.0
        busy_frac_est = time_busy / win_len
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_est = count_W_den / arr_count if arr_count > 0 else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += arr_count
        total_blk += blk_count
        total_dep += dep_count
        total_time_active += time_busy
        total_time_total += win_len

    avg_L = sum(per_seed_L)/len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W)/len(per_seed_W) if per_seed_W else 0
    avg_busy_frac = sum(per_seed_busy_frac)/len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_p_loss = sum(per_seed_p_loss)/len(per_seed_p_loss) if per_seed_p_loss else 0
    avg_p_wait = sum(per_seed_p_wait)/len(per_seed_p_wait) if per_seed_p_wait else 0
    
    avg_arr = total_arr / seeds_n
    avg_blk = total_blk / seeds_n
    avg_dep = total_dep / seeds_n
    
    dep_rate = avg_dep / (horizon - horizon*0.25) if (horizon - horizon*0.25) > 0 else 0
    lam_eff = dep_rate 
    
    busy_util = min(avg_L, c) / c if c > 0 else 0
    busy_occupied = avg_busy_frac
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": horizon,
        "seed_list": list(range(seed_start, seed_start + seeds_n)),
        "seeds_used": seeds_n,
        "time_unit": time_unit,
        "win": round(horizon * 0.75, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_p_wait, 6),
        "busy_util": round(busy_util, 6),
        "busy_occupied": round(busy_occupied, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
