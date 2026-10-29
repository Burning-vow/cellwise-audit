import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0 / 60.0
    mu_base = 1.0 / 5.0
    c = 1
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    elif a.pert == 'c_up':
        c = 2
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
    
    horizon_min = a.horizon
    warmup_frac = 0.25
    win_start = horizon_min * warmup_frac
    win_len = horizon_min - win_start
    
    all_L = []
    all_W = []
    all_busy = []
    all_ploss = []
    all_pwait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seeds_used = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        busy_until = [0.0] * c
        
        area_N = 0.0
        last_event_t = 0.0
        N = 0
        
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        wait_count = 0
        total_wait_time = 0.0
        total_service_time = 0.0
        customers_served = 0
        
        while t < horizon_min:
            arr_t = next_arr
            dep_t = min(busy_until) if any(b > t for b in busy_until) else float('inf')
            
            if arr_t <= dep_t and arr_t < horizon_min:
                dt = arr_t - t
                if t >= win_start:
                    area_N += N * dt
                t = arr_t
                
                st = rng.expovariate(mu)
                service_times[t] = st
                
                free_idx = -1
                for j in range(c):
                    if busy_until[j] <= t:
                        free_idx = j
                        break
                
                if free_idx != -1:
                    busy_until[free_idx] = t + st
                    N += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                        if len(queue) > 0 or (N > 1 and c == 1):
                            pass
                        # check if waited: if there was someone ahead or server busy at arrival
                        # Actually simpler: if N before increment was >0 and server was busy? 
                        # Let's track waiting properly.
                        # If upon arrival, no server is free immediately, they wait.
                        # We already found free_idx. If free_idx was found because busy_until[j] <= t, then no wait.
                        # But we need to know if they had to wait in queue.
                        # In this simulation, if free_idx != -1, they start service immediately -> no wait.
                        # If free_idx == -1, they go to queue -> wait.
                        # So here free_idx != -1 means no wait.
                        pass
                    else:
                        queue.append((t, st))
                        N += 1
                        if t >= win_start:
                            arrivals_in_win += 1
                            wait_count += 1
                else:
                    # Should not happen if logic above is correct, but safety
                    queue.append((t, st))
                    N += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                        wait_count += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif dep_t < horizon_min and dep_t < arr_t:
                dt = dep_t - t
                if t >= win_start:
                    area_N += N * dt
                t = dep_t
                
                # Find which server finished
                finished_server = -1
                for j in range(c):
                    if abs(busy_until[j] - t) < 1e-9:
                        finished_server = j
                        break
                
                if finished_server != -1:
                    # A customer leaves
                    N -= 1
                    if t >= win_start:
                        departures_in_win += 1
                    
                    # Check if queue has someone
                    if queue:
                        arr_time, svc_time = queue.pop(0)
                        busy_until[finished_server] = t + svc_time
                        # This customer started service now
                        # Their total time in system = t - arr_time
                        sys_time = t - arr_time
                        if t >= win_start:
                            total_wait_time += sys_time
                            customers_served += 1
                    else:
                        busy_until[finished_server] = t  # idle
                
            else:
                break
        
        # Final integration up to horizon
        if t < horizon_min:
            dt = horizon_min - t
            if t >= win_start:
                area_N += N * dt
        
        L_est = area_N / win_len if win_len > 0 else 0.0
        
        # W estimation: average system time of those who departed within window?
        # Or use Little's Law? The prompt asks for empirical stats.
        # "统计量只在去掉前 25% 预热后的窗口内累计"
        # For W, usually it's avg time in system for customers served in the window.
        # But careful with boundary effects. Standard approach: sum of times for completions in window / count.
        
        W_est = total_wait_time / customers_served if customers_served > 0 else 0.0
        
        busy_frac_est = 0.0
        # Calculate busy fraction via area of busy servers
        # We didn't track busy area explicitly. Let's re-calculate or approximate.
        # Better: track busy_area during loop.
        
        # Re-run tracking busy area? No, let's just compute from final state approximations or fix loop.
        # Fixing loop mentally: I should have tracked busy_area.
        # Since I can't edit easily without rewriting, I'll estimate busy_frac as 1 - P(idle).
        # Idle time = time when N==0.
        # I didn't track idle area either.
        
        # Let's assume standard M/M/1/c results for validation but output simulated.
        # To be safe, I will rewrite the loop slightly in my head to ensure correctness.
        # Actually, I can compute busy_frac from utilization formula if needed, but must be simulated.
        # Let's add busy_area tracking.
        
        # Since I am generating code, I will include proper tracking.
        
        # Resetting variables for clean implementation below...
        pass

    # Clean Implementation
    all_L = []
    all_W = []
    all_busy = []
    all_ploss = []
    all_pwait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seeds_used = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # list of (arrival_time, service_duration)
        busy_until = [0.0] * c
        
        area_N = 0.0
        area_busy = 0.0 # Sum of min(N, c) over time? No, E[min(N,c)]/c.
        # Busy fraction defined as E[min(N,1)]/1 for c=1. Generally E[min(N,c)]/c.
        # Let's track number of busy servers.
        
        last_t = 0.0
        N = 0
        num_busy = 0
        
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        wait_count = 0
        total_sys_time = 0.0
        customers_completed = 0
        
        while t < horizon_min:
            arr_t = next_arr
            dep_t = min([b for b in busy_until if b > t], default=float('inf'))
            
            if arr_t <= dep_t and arr_t < horizon_min:
                dt = arr_t - t
                if t >= win_start:
                    area_N += N * dt
                    area_busy += num_busy * dt
                t = arr_t
                
                st = rng.expovariate(mu)
                
                # Determine if blocked
                if N >= c + len(queue): # Capacity is c servers + infinite queue? 
                    # Problem says "打印店", usually finite capacity? 
                    # "系统稳定" implies infinite queue or high enough capacity.
                    # Standard MM1 assumes infinite queue.
                    # Perturbation c_up changes servers.
                    # Blocking only happens if system is full. With infinite queue, never blocked.
                    # However, prompt mentions blk/p_loss. 
                    # If queue is infinite, blk=0.
                    # Let's assume infinite queue unless specified otherwise.
                    # But "blk" key exists. Maybe finite capacity?
                    # Task mm1-04 doesn't specify capacity K. Default is infinite.
                    # So blk should be 0.
                    pass
                
                # Add to system
                N += 1
                
                # Try to assign to server
                assigned = False
                for j in range(c):
                    if busy_until[j] <= t:
                        busy_until[j] = t + st
                        num_busy += 1
                        assigned = True
                        break
                
                if not assigned:
                    queue.append((t, st))
                    # Waited
                    if t >= win_start:
                        wait_count += 1
                
                if t >= win_start:
                    arrivals_in_win += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif dep_t < horizon_min and dep_t < arr_t:
                dt = dep_t - t
                if t >= win_start:
                    area_N += N * dt
                    area_busy += num_busy * dt
                t = dep_t
                
                # Find server that became free
                freed_idx = -1
                for j in range(c):
                    if abs(busy_until[j] - t) < 1e-9:
                        freed_idx = j
                        break
                
                if freed_idx != -1:
                    num_busy -= 1
                    N -= 1
                    
                    if t >= win_start:
                        departures_in_win += 1
                    
                    # Serve next from queue
                    if queue:
                        arr_time, svc_dur = queue.pop(0)
                        busy_until[freed_idx] = t + svc_dur
                        num_busy += 1
                        # Customer completed service
                        sys_time = t - arr_time
                        if t >= win_start:
                            total_sys_time += sys_time
                            customers_completed += 1
                    else:
                        busy_until[freed_idx] = t # Idle
            
            else:
                break
        
        if t < horizon_min:
            dt = horizon_min - t
            if t >= win_start:
                area_N += N * dt
                area_busy += num_busy * dt
        
        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = total_sys_time / customers_completed if customers_completed > 0 else 0.0
        busy_est = area_busy / (win_len * c) if win_len > 0 else 0.0
        
        p_loss_est = blocked_in_win / arrivals_in_win if arrivals_in_win > 0 else 0.0
        p_wait_est = wait_count / arrivals_in_win if arrivals_in_win > 0 else 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy.append(busy_est)
        all_ploss.append(p_loss_est)
        all_pwait.append(p_wait_est)
        all_arr.append(arrivals_in_win)
        all_dep.append(departures_in_win)
        all_blk.append(blocked_in_win)
        seeds_used.append(seed)
    
    n_seeds = len(seeds_used)
    avg_L = sum(all_L) / n_seeds
    avg_W = sum(all_W) / n_seeds
    avg_busy = sum(all_busy) / n_seeds
    avg_ploss = sum(all_ploss) / n_seeds
    avg_pwait = sum(all_pwait) / n_seeds
    avg_arr = sum(all_arr) / n_seeds
    avg_dep = sum(all_dep) / n_seeds
    avg_blk = sum(all_blk) / n_seeds
    
    dep_rate = avg_dep / (win_len / 60.0) if win_len > 0 else 0.0
    lam_eff = dep_rate
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_pwait, 6),
        "runtime_units": "minute",
        "seed_list": seeds_used,
        "seeds_used": n_seeds,
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_ploss, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy],
        "per_seed_p_loss": [round(x, 6) for x in all_ploss],
        "per_seed_p_wait": [round(x, 6) for x in all_pwait]
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
