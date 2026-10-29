import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0
    mu_base = 12.0
    c = 1
    K = 4
    time_unit = 'hour'
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base
    
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time_in_system = 0.0
    total_busy_time = 0.0
    total_window_time = 0.0
    total_wait_count = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        random.seed(seed)
        seed_list.append(seed)
        
        t = 0.0
        next_arr = random.expovariate(lam)
        next_dep = float('inf')
        queue = []
        service_times = {}
        arrival_times = {}
        
        n_customers = 0
        busy_periods = 0
        last_event_time = 0.0
        current_n = 0
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_w = 0.0
        count_wait = 0
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_event_time
                if last_event_time >= warmup_end or (last_event_time < warmup_end and t > warmup_end):
                    overlap_start = max(last_event_time, warmup_end)
                    overlap_len = t - overlap_start
                    if overlap_len > 0:
                        area_L += current_n * overlap_len
                        if current_n > 0:
                            area_busy += overlap_len
                
                if len(queue) + (1 if next_dep != float('inf') else 0) < K:
                    queue.append(t)
                    st = random.expovariate(mu)
                    service_times[t] = st
                    arrival_times[t] = t
                    count_arr += 1
                    if next_dep == float('inf'):
                        next_dep = t + st
                        busy_periods += 1
                else:
                    count_blk += 1
                
                next_arr = t + random.expovariate(lam)
                last_event_time = t
                current_n = len(queue)
                
            else:
                t = next_dep
                dt = t - last_event_time
                if last_event_time >= warmup_end or (last_event_time < warmup_end and t > warmup_end):
                    overlap_start = max(last_event_time, warmup_end)
                    overlap_len = t - overlap_start
                    if overlap_len > 0:
                        area_L += current_n * overlap_len
                        if current_n > 0:
                            area_busy += overlap_len
                
                if queue:
                    arr_t = queue.pop(0)
                    w = t - arr_t
                    sum_w += w
                    count_dep += 1
                    if w > 0:
                        count_wait += 1
                    
                    if queue:
                        next_arr_t = queue[0]
                        remaining_service = service_times[next_arr_t] - (t - next_arr_t)
                        if remaining_service <= 0:
                             # This logic is flawed for simple FIFO with pre-drawn times if we don't track remaining carefully
                             # Let's restart the simulation loop with a cleaner state machine approach
                             pass 
                        else:
                            next_dep = t + remaining_service
                    else:
                        next_dep = float('inf')
                
                last_event_time = t
                current_n = len(queue)
        
        # The above loop has issues with tracking remaining service time correctly when popping from front.
        # Let's rewrite the inner simulation loop properly.
        
        # Reset variables for this seed to redo cleanly
        t = 0.0
        next_arr = random.expovariate(lam)
        next_dep = float('inf')
        queue = [] # List of tuples (arrival_time, service_duration)
        current_n = 0
        last_event_time = 0.0
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_w = 0.0
        count_wait = 0
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_event_time
                if last_event_time < warmup_end and t > warmup_end:
                    overlap_len = t - warmup_end
                    area_L += current_n * overlap_len
                    if current_n > 0:
                        area_busy += overlap_len
                elif last_event_time >= warmup_end:
                    area_L += current_n * dt
                    if current_n > 0:
                        area_busy += dt
                
                if len(queue) < K:
                    st = random.expovariate(mu)
                    queue.append((t, st))
                    count_arr += 1
                    if len(queue) == 1:
                        next_dep = t + st
                else:
                    count_blk += 1
                
                next_arr = t + random.expovariate(lam)
                last_event_time = t
                current_n = len(queue)
                
            else:
                t = next_dep
                dt = t - last_event_time
                if last_event_time < warmup_end and t > warmup_end:
                    overlap_len = t - warmup_end
                    area_L += current_n * overlap_len
                    if current_n > 0:
                        area_busy += overlap_len
                elif last_event_time >= warmup_end:
                    area_L += current_n * dt
                    if current_n > 0:
                        area_busy += dt
                
                if queue:
                    arr_t, st = queue.pop(0)
                    w = t - arr_t
                    sum_w += w
                    count_dep += 1
                    if w > 0:
                        count_wait += 1
                    
                    if queue:
                        next_arr_t, next_st = queue[0]
                        # Service starts immediately after previous one ends
                        # But wait, the service duration was drawn at arrival.
                        # If the server was busy, the customer waited.
                        # When we pop, we are finishing service.
                        # The next customer in line starts service NOW.
                        # Their service time is already known.
                        next_dep = t + queue[0][1]
                    else:
                        next_dep = float('inf')
                
                last_event_time = t
                current_n = len(queue)

        win_len = horizon - warmup_end
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = sum_w / count_dep if count_dep > 0 else 0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0
        p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0
        p_wait_est = count_wait / count_dep if count_dep > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += count_arr
        total_blk += count_blk
        total_dep += count_dep
        total_time_in_system += sum_w
        total_busy_time += area_busy
        total_window_time += win_len
        total_wait_count += count_wait

    seeds_used = len(per_seed_L)
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0
    avg_p_loss = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0
    avg_p_wait = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0
    
    avg_arr = total_arr / seeds_used if seeds_used > 0 else 0
    avg_blk = total_blk / seeds_used if seeds_used > 0 else 0
    avg_dep = total_dep / seeds_used if seeds_used > 0 else 0
    
    dep_rate = avg_dep / (total_window_time / seeds_used) if seeds_used > 0 and total_window_time > 0 else 0
    lam_eff = dep_rate
    
    busy_util = avg_busy_frac / c if c > 0 else 0
    busy_occupied = avg_busy_frac
    
    result = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "p_loss": avg_p_loss,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": total_window_time / seeds_used if seeds_used > 0 else 0,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": busy_util,
        "dep": avg_dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_wait": avg_p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": busy_occupied
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
