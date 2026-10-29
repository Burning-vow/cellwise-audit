import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 6.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    win = H
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = []
        
        warmup_end = 0.25 * H
        stats_start_time = warmup_end
        
        area_N = 0.0
        last_event_time = 0.0
        current_N = 0
        
        total_service_time_sum = 0.0
        num_completed_in_window = 0
        num_arrivals_in_window = 0
        num_blocked_in_window = 0
        num_waited_in_window = 0
        
        while True:
            min_server_free = min(servers_free_at)
            if next_arr <= min_server_free:
                event_time = next_arr
                event_type = 'arr'
            else:
                event_time = min_server_free
                event_type = 'dep'
                
            if event_time > H:
                break
                
            dt = event_time - last_event_time
            if last_event_time < stats_start_time and event_time >= stats_start_time:
                split_dt = stats_start_time - last_event_time
                area_N += current_N * split_dt
                remaining_dt = event_time - stats_start_time
                area_N += current_N * remaining_dt
            elif last_event_time >= stats_start_time:
                area_N += current_N * dt
            last_event_time = event_time
            
            if event_type == 'arr':
                service_time = rng.expovariate(mu)
                cust = {'arrival': event_time, 'service': service_time}
                
                free_idx = -1
                for j in range(c):
                    if servers_free_at[j] <= event_time:
                        free_idx = j
                        break
                        
                if free_idx != -1:
                    servers_free_at[free_idx] = event_time + service_time
                    start_serv = event_time
                    end_serv = event_time + service_time
                    if event_time >= stats_start_time:
                        num_arrivals_in_window += 1
                        total_service_time_sum += (end_serv - cust['arrival'])
                        num_completed_in_window += 1
                        if start_serv > cust['arrival']:
                            num_waited_in_window += 1
                else:
                    queue.append(cust)
                    if event_time >= stats_start_time:
                        num_arrivals_in_window += 1
                        if len(queue) > 0: 
                            pass 
                    current_N += 1
                    
                next_arr = event_time + rng.expovariate(lam)
                
            else: 
                dep_idx = -1
                for j in range(c):
                    if servers_free_at[j] == event_time:
                        dep_idx = j
                        break
                if dep_idx == -1:
                    for j in range(c):
                        if abs(servers_free_at[j] - event_time) < 1e-9:
                            dep_idx = j
                            break
                            
                if dep_idx != -1:
                    if queue:
                        cust = queue.pop(0)
                        start_serv = event_time
                        end_serv = event_time + cust['service']
                        servers_free_at[dep_idx] = end_serv
                        if event_time >= stats_start_time:
                            total_service_time_sum += (end_serv - cust['arrival'])
                            num_completed_in_window += 1
                            if start_serv > cust['arrival']:
                                num_waited_in_window += 1
                    else:
                        servers_free_at[dep_idx] = float('inf')
                        current_N -= 1
                        if event_time >= stats_start_time:
                            pass 
                        
        L_est = area_N / (H - stats_start_time) if (H - stats_start_time) > 0 else 0
        W_est_min = (total_service_time_sum / num_completed_in_window * 60) if num_completed_in_window > 0 else 0
        busy_frac_est = (area_N / (H - stats_start_time)) / c if (H - stats_start_time) > 0 else 0
        p_loss_est = num_blocked_in_window / num_arrivals_in_window if num_arrivals_in_window > 0 else 0
        p_wait_est = num_waited_in_window / num_arrivals_in_window if num_arrivals_in_window > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_arr.append(num_arrivals_in_window)
        all_dep.append(num_completed_in_window)
        all_blk.append(num_blocked_in_window)
        
    avg_L = sum(per_seed_L) / N_seeds
    avg_W = sum(per_seed_W) / N_seeds
    avg_busy_frac = sum(per_seed_busy_frac) / N_seeds
    avg_p_loss = sum(per_seed_p_loss) / N_seeds
    avg_p_wait = sum(per_seed_p_wait) / N_seeds
    
    avg_arr = sum(all_arr) / N_seeds
    avg_dep = sum(all_dep) / N_seeds
    avg_blk = sum(all_blk) / N_seeds
    
    dep_rate = avg_dep / (H - 0.25*H) if (H - 0.25*H) > 0 else 0
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hours",
        "seed_list": list(range(seed_start, seed_start + N_seeds)),
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(H - 0.25*H, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
