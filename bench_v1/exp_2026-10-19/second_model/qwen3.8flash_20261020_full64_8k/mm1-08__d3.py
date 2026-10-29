import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    lam_base = 8.0
    mu_base = 12.0
    c = 1

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 2
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    horizon_hours = H if time_unit == 'hour' else (H / 60.0 if time_unit == 'minute' else H / 3600.0)
    
    warmup_frac = 0.25
    win_start = warmup_frac * horizon_hours
    win_len = horizon_hours - win_start

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []

    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n_in_sys = 0
        busy_time = 0.0
        last_event_t = 0.0
        
        arrivals_win = 0
        departures_win = 0
        blocked_win = 0
        wait_count = 0
        
        area_n = 0.0
        total_wait_time = 0.0
        total_service_time = 0.0
        num_completed = 0
        
        customer_queue = [] 
        
        while t < horizon_hours:
            if next_arr <= next_dep:
                dt = next_arr - t
                if t >= win_start or (t < win_start and next_arr > win_start):
                    pass 
                
                if t < win_start:
                    overlap = max(0.0, min(next_arr, win_start) - t)
                    area_n += n_in_sys * overlap
                    busy_time += min(n_in_sys, c) * overlap
                else:
                    area_n += n_in_sys * dt
                    busy_time += min(n_in_sys, c) * dt
                
                t = next_arr
                
                if n_in_sys < c:
                    service_time = rng.expovariate(mu)
                    dep_time = t + service_time
                    if dep_time < next_dep:
                        next_dep = dep_time
                    n_in_sys += 1
                    if t >= win_start:
                        arrivals_win += 1
                        total_service_time += service_time
                        num_completed += 1
                        if len(customer_queue) > 0:
                            wait_count += 1
                            total_wait_time += (dep_time - t)
                        else:
                            total_wait_time += 0
                else:
                    if t >= win_start:
                        blocked_win += 1
                    n_in_sys += 1 
                    customer_queue.append(t)
                    if t >= win_start:
                        arrivals_win += 1
                
                next_arr = t + rng.expovariate(lam)
            else:
                dt = next_dep - t
                if t < win_start:
                    overlap = max(0.0, min(next_dep, win_start) - t)
                    area_n += n_in_sys * overlap
                    busy_time += min(n_in_sys, c) * overlap
                else:
                    area_n += n_in_sys * dt
                    busy_time += min(n_in_sys, c) * dt
                
                t = next_dep
                
                if n_in_sys > 0:
                    n_in_sys -= 1
                    if t >= win_start:
                        departures_win += 1
                    
                    if customer_queue:
                        arr_time = customer_queue.pop(0)
                        service_time = rng.expovariate(mu)
                        dep_time = t + service_time
                        if dep_time < next_dep:
                            next_dep = dep_time
                        n_in_sys += 1
                        if t >= win_start:
                            total_service_time += service_time
                            num_completed += 1
                            wait_time = t - arr_time
                            total_wait_time += wait_time
                            if wait_time > 0:
                                wait_count += 1
                    else:
                        next_dep = float('inf')
                else:
                    next_dep = float('inf')

        if win_len > 0:
            L_est = area_n / win_len
            W_est = total_wait_time / num_completed if num_completed > 0 else 0.0
            busy_frac_est = busy_time / win_len
            p_loss_est = blocked_win / arrivals_win if arrivals_win > 0 else 0.0
            p_wait_est = wait_count / arrivals_win if arrivals_win > 0 else 0.0
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            per_seed_arr.append(arrivals_win)
            per_seed_dep.append(departures_win)
            per_seed_blk.append(blocked_win)
        else:
            per_seed_L.append(0.0)
            per_seed_W.append(0.0)
            per_seed_busy_frac.append(0.0)
            per_seed_p_loss.append(0.0)
            per_seed_p_wait.append(0.0)
            per_seed_arr.append(0)
            per_seed_dep.append(0)
            per_seed_blk.append(0)

    seeds_used = N_seeds
    seed_list = [seed_start + i for i in range(N_seeds)]
    
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_p_loss = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_p_wait = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0.0
    
    avg_arr = sum(per_seed_arr) / seeds_used if seeds_used > 0 else 0.0
    avg_dep = sum(per_seed_dep) / seeds_used if seeds_used > 0 else 0.0
    avg_blk = sum(per_seed_blk) / seeds_used if seeds_used > 0 else 0.0
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate
    
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
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
