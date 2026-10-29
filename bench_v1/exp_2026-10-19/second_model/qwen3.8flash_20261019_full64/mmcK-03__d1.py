import sys, json, random, math
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            val = sys.argv[i+1] if i+1 < len(sys.argv) and not sys.argv[i+1].startswith('--') else None
            if val is not None:
                try:
                    if '.' in val or 'e' in val.lower():
                        args[key] = float(val)
                    else:
                        args[key] = int(val)
                except:
                    args[key] = val
            i += 2
        else:
            i += 1
    
    seeds_n = args.get('seeds', 5)
    horizon = float(args.get('horizon', 100.0))
    seed_start = args.get('seed-start', 1)
    pert = args.get('pert', 'none')
    
    time_unit = "hour"
    lam_base = 8.0
    mu_base = 60.0 / 12.0
    c = 2
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    if pert != 'mu_up':
        mu = mu_base
    if pert == 'mu_up':
        pass # already set
        
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    results_busy_util = []
    
    total_time = horizon
    warmup_end = 0.75 * total_time
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = deque()
        n_in_system = 0
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        count_wait = 0
        
        last_event_time = 0.0
        
        while True:
            min_server_free = min(servers_free_at)
            next_departure = min_server_free if n_in_system > 0 else float('inf')
            
            if next_arrival <= next_departure:
                event_time = next_arrival
            else:
                event_time = next_departure
                
            if event_time >= total_time:
                break
            
            dt = event_time - last_event_time
            if last_event_time >= warmup_end:
                area_L += n_in_system * dt
                busy_count = sum(1 for st in servers_free_at if st <= last_event_time)
                area_busy += (busy_count / c) * dt
            
            if next_arrival <= next_departure:
                if n_in_system < K:
                    n_in_system += 1
                    count_arr += 1
                    if last_event_time >= warmup_end:
                        pass 
                    start_service = max(event_time, min(servers_free_at))
                    idx_min = servers_free_at.index(min(servers_free_at))
                    service_dur = rng.expovariate(mu)
                    servers_free_at[idx_min] = start_service + service_dur
                    queue.append((event_time, start_service, servers_free_at[idx_min]))
                else:
                    count_blk += 1
                next_arrival = event_time + rng.expovariate(lam)
            else:
                if n_in_system > 0:
                    n_in_system -= 1
                    count_dep += 1
                    if queue:
                        arr_t, serv_start, serv_end = queue.popleft()
                        if serv_end <= event_time:
                            w = serv_end - arr_t
                            if last_event_time >= warmup_end:
                                sum_W += w
                                count_wait += 1
                        else:
                             queue.appendleft((arr_t, serv_start, serv_end))
                    else:
                        pass
                    
                    found = False
                    for i in range(c):
                        if servers_free_at[i] <= event_time:
                            servers_free_at[i] = float('inf')
                            found = True
                            break
                    if not found:
                         min_val = min(servers_free_at)
                         idx = servers_free_at.index(min_val)
                         servers_free_at[idx] = float('inf')
                         
                    if queue:
                        arr_t, serv_start, serv_end = queue[0]
                        if serv_start <= event_time:
                            queue.popleft()
                            new_serv_start = event_time
                            new_serv_end = new_serv_start + (serv_end - serv_start)
                            servers_free_at[min(range(c), key=lambda x: servers_free_at[x])] = new_serv_end
                            queue.appendleft((arr_t, new_serv_start, new_serv_end))
                
            last_event_time = event_time
            
        if last_event_time < total_time:
             dt = total_time - last_event_time
             if last_event_time >= warmup_end:
                 area_L += n_in_system * dt
                 busy_count = sum(1 for st in servers_free_at if st <= last_event_time)
                 area_busy += (busy_count / c) * dt

        win_len = total_time - warmup_end
        if win_len > 0:
            L_est = area_L / win_len
            W_est = sum_W / count_wait if count_wait > 0 else 0.0
            busy_frac_est = area_busy / win_len
            p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0.0
            p_wait_est = count_wait / count_arr if count_arr > 0 else 0.0
            busy_util_est = (area_busy * c) / win_len if win_len > 0 else 0.0
            
            results_L.append(L_est)
            results_W.append(W_est)
            results_busy_frac.append(busy_frac_est)
            results_p_loss.append(p_loss_est)
            results_p_wait.append(p_wait_est)
            results_arr.append(count_arr)
            results_blk.append(count_blk)
            results_dep.append(count_dep)
            results_busy_util.append(busy_util_est)
        else:
            results_L.append(0.0)
            results_W.append(0.0)
            results_busy_frac.append(0.0)
            results_p_loss.append(0.0)
            results_p_wait.append(0.0)
            results_arr.append(0)
            results_blk.append(0)
            results_dep.append(0)
            results_busy_util.append(0.0)

    avg_L = sum(results_L) / seeds_n
    avg_W = sum(results_W) / seeds_n
    avg_busy_frac = sum(results_busy_frac) / seeds_n
    avg_p_loss = sum(results_p_loss) / seeds_n
    avg_p_wait = sum(results_p_wait) / seeds_n
    avg_arr = sum(results_arr) / seeds_n
    avg_blk = sum(results_blk) / seeds_n
    avg_dep = sum(results_dep) / seeds_n
    avg_busy_util = sum(results_busy_util) / seeds_n
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0.0
    lam_eff = avg_arr / win_len if win_len > 0 else 0.0
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hours",
        "seed_list": list(range(seed_start, seed_start + seeds_n)),
        "seeds_used": seeds_n,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in results_L],
        "per_seed_W": [round(x, 6) for x in results_W],
        "per_seed_busy_frac": [round(x, 6) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in results_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
