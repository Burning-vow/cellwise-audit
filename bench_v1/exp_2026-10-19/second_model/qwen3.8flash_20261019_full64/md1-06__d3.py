import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 60.0 / 5.0
    c = 1
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_time = 1.0 / mu
        queue = []
        busy_until = -1.0
        n_in_system = 0
        
        warmup_end = horizon_hours * 0.25
        stats_window_len = horizon_hours - warmup_end
        
        area_n = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        wait_count = 0
        loss_count = 0
        
        last_event_time = 0.0
        
        while t < horizon_hours:
            # Determine next event
            arr_t = next_arrival if next_arrival is not None else float('inf')
            dep_t = busy_until if busy_until >= t else float('inf')
            
            if arr_t <= dep_t and arr_t < horizon_hours:
                dt = arr_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(arr_t, horizon_hours)
                    if overlap_end > overlap_start:
                        area_n += n_in_system * (overlap_end - overlap_start)
                
                t = arr_t
                last_event_time = t
                
                if n_in_system < c:
                    n_in_system += 1
                    start_service = t
                    end_service = t + service_time
                    if end_service < busy_until or busy_until < t:
                         busy_until = end_service
                    else:
                         busy_until = max(busy_until, end_service)
                    queue.append((start_service, end_service))
                    count_arr += 1
                else:
                    count_blk += 1
                    loss_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif dep_t < arr_t and dep_t < horizon_hours:
                dt = dep_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(dep_t, horizon_hours)
                    if overlap_end > overlap_start:
                        area_n += n_in_system * (overlap_end - overlap_start)
                
                t = dep_t
                last_event_time = t
                
                if queue:
                    s_start, s_end = queue.pop(0)
                    if s_end == t:
                        n_in_system -= 1
                        count_dep += 1
                        w = t - s_start
                        if t >= warmup_end:
                            sum_w += w
                            wait_count += 1
                        if n_in_system > 0 and queue:
                             pass # Next departure handled by loop logic implicitly via busy_until check? 
                             # Actually we need to set busy_until for the next car if any
                             if queue:
                                 next_s_start, next_s_end = queue[0]
                                 busy_until = next_s_end
                             else:
                                 busy_until = -1.0
                        else:
                             busy_until = -1.0
                    else:
                        # This shouldn't happen in strict FIFO single server with pre-assigned times if we manage queue correctly
                        # But let's ensure consistency. If multiple cars, only one leaves at a time.
                        # The queue stores (arrival_time, completion_time).
                        # We pop the head. Its completion time should be current t.
                        pass
                else:
                    busy_until = -1.0
            
            else:
                break

        # Final integration up to horizon
        if t < horizon_hours:
             dt = horizon_hours - last_event_time
             if t >= warmup_end or (t + dt > warmup_end):
                 overlap_start = max(t, warmup_end)
                 overlap_end = horizon_hours
                 if overlap_end > overlap_start:
                     area_n += n_in_system * (overlap_end - overlap_start)

        L_est = area_n / stats_window_len if stats_window_len > 0 else 0
        W_est = sum_w / wait_count if wait_count > 0 else 0
        busy_frac_est = area_n / stats_window_len / c if stats_window_len > 0 and c > 0 else 0 # E[min(N,c)]/c approx by avg N/c for c=1
        # For c>1, this simple area_n/c is wrong. It should be integral of min(n,c)/c.
        # Let's re-calculate properly for general c.
        
        # Re-run simulation logic to get correct integrals for c>1 case? 
        # Or fix the loop above. The loop above integrates n_in_system.
        # For busy_util = E[min(N,c)]/c, we need integral of min(n,c).
        # Since I can't easily refactor without rewriting, I will assume c=1 for the main task description but handle c_up carefully.
        # Wait, the prompt says "busy_frac ... = E[min(N,1)]/1". So for c=1 it's fine.
        # For c_up, c=2. The definition of busy_frac in output keys is specific to c=1 context usually, but here pert changes c.
        # Let's stick to the calculation inside the loop being accurate for min(n,c).
        
        # Correction: The previous loop integrated n_in_system. 
        # To support c>1 correctly for busy_util, I need to integrate min(n_in_system, c).
        # And for L, it is average number in system (n_in_system).
        
        # Let's restart the inner simulation block with corrected integration.
        
        # Reset variables for this seed to redo cleanly
        t = 0.0
        rng = random.Random(seed)
        next_arrival = rng.expovariate(lam)
        service_time = 1.0 / mu
        queue = []
        busy_until = -1.0
        n_in_system = 0
        warmup_end = horizon_hours * 0.25
        stats_window_len = horizon_hours - warmup_end
        
        area_n = 0.0
        area_min_nc = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        wait_count = 0
        loss_count = 0
        last_event_time = 0.0
        
        while t < horizon_hours:
            arr_t = next_arrival if next_arrival is not None else float('inf')
            dep_t = busy_until if busy_until >= t else float('inf')
            
            if arr_t <= dep_t and arr_t < horizon_hours:
                dt = arr_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(arr_t, horizon_hours)
                    if overlap_end > overlap_start:
                        dur = overlap_end - overlap_start
                        area_n += n_in_system * dur
                        area_min_nc += min(n_in_system, c) * dur
                
                t = arr_t
                last_event_time = t
                
                if n_in_system < c:
                    n_in_system += 1
                    start_service = t
                    end_service = t + service_time
                    queue.append((start_service, end_service))
                    if len(queue) == 1:
                        busy_until = end_service
                    count_arr += 1
                else:
                    count_blk += 1
                    loss_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif dep_t < arr_t and dep_t < horizon_hours:
                dt = dep_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(dep_t, horizon_hours)
                    if overlap_end > overlap_start:
                        dur = overlap_end - overlap_start
                        area_n += n_in_system * dur
                        area_min_nc += min(n_in_system, c) * dur
                
                t = dep_t
                last_event_time = t
                
                if queue:
                    s_start, s_end = queue.pop(0)
                    if s_end == t:
                        n_in_system -= 1
                        count_dep += 1
                        w = t - s_start
                        if t >= warmup_end:
                            sum_w += w
                            wait_count += 1
                        
                        if queue:
                            next_s_start, next_s_end = queue[0]
                            busy_until = next_s_end
                        else:
                            busy_until = -1.0
                    else:
                        # Should not happen in consistent model
                        pass
                else:
                    busy_until = -1.0
            else:
                break

        if t < horizon_hours:
             dt = horizon_hours - last_event_time
             if t >= warmup_end or (t + dt > warmup_end):
                 overlap_start = max(t, warmup_end)
                 overlap_end = horizon_hours
                 if overlap_end > overlap_start:
                     dur = overlap_end - overlap_start
                     area_n += n_in_system * dur
                     area_min_nc += min(n_in_system, c) * dur

        L_est = area_n / stats_window_len if stats_window_len > 0 else 0
        W_est = sum_w / wait_count if wait_count > 0 else 0
        busy_util_est = area_min_nc / stats_window_len / c if stats_window_len > 0 and c > 0 else 0
        p_loss_est = loss_count / count_arr if count_arr > 0 else 0
        p_wait_est = (count_arr - count_dep - loss_count) / count_arr if count_arr > 0 else 0 # Approximation of waiting prob? 
        # Usually P(wait) is fraction of arrivals that wait. In M/M/1, P(W>0) = rho.
        # Here, if n_in_system >= c upon arrival, they are blocked (loss). If n_in_system < c, they enter immediately.
        # So no one waits in queue in this model? "先到先洗" implies queue.
        # My model above: if n_in_system < c, enter. Else block. This is M/M/c/c (Erlang Loss).
        # BUT the problem says "自动洗车机... 车辆按泊松流到达... 先到先洗". This implies a Queue (M/M/1), not Loss System.
        # "固定 5 分钟" -> Deterministic Service Time. M/D/1.
        # If it's a queue, n_in_system can exceed c.
        # Let's re-read: "场内平均车辆数 L". If it's a loss system, L is small. If queue, L can be large.
        # Standard interpretation of "car wash" with "first come first served" is a Queue.
        # However, "busy_frac ... = 1-pi_0" suggests standard utilization.
        # If it's a queue, capacity is infinite.
        # Let's adjust model to Infinite Capacity Queue.
        
        # Restarting simulation for Infinite Capacity Queue
        t = 0.0
        rng = random.Random(seed)
        next_arrival = rng.expovariate(lam)
        service_time = 1.0 / mu
        queue = [] # List of (arrival_time, completion_time)
        busy_until = -1.0
        n_in_system = 0
        warmup_end = horizon_hours * 0.25
        stats_window_len = horizon_hours - warmup_end
        
        area_n = 0.0
        area_min_nc = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0 # Always 0 for infinite queue
        sum_w = 0.0
        wait_count = 0
        loss_count = 0
        last_event_time = 0.0
        
        while t < horizon_hours:
            arr_t = next_arrival if next_arrival is not None else float('inf')
            dep_t = busy_until if busy_until >= t else float('inf')
            
            if arr_t <= dep_t and arr_t < horizon_hours:
                dt = arr_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(arr_t, horizon_hours)
                    if overlap_end > overlap_start:
                        dur = overlap_end - overlap_start
                        area_n += n_in_system * dur
                        area_min_nc += min(n_in_system, c) * dur
                
                t = arr_t
                last_event_time = t
                
                n_in_system += 1
                start_service = t
                # Calculate completion time based on when server becomes free
                if t >= busy_until:
                    end_service = t + service_time
                    busy_until = end_service
                else:
                    end_service = busy_until + service_time
                    busy_until = end_service
                
                queue.append((start_service, end_service))
                count_arr += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif dep_t < arr_t and dep_t < horizon_hours:
                dt = dep_t - last_event_time
                if t >= warmup_end or (t + dt > warmup_end):
                    overlap_start = max(t, warmup_end)
                    overlap_end = min(dep_t, horizon_hours)
                    if overlap_end > overlap_start:
                        dur = overlap_end - overlap_start
                        area_n += n_in_system * dur
                        area_min_nc += min(n_in_system, c) * dur
                
                t = dep_t
                last_event_time = t
                
                if queue:
                    s_start, s_end = queue.pop(0)
                    if s_end == t:
                        n_in_system -= 1
                        count_dep += 1
                        w = t - s_start
                        if t >= warmup_end:
                            sum_w += w
                            wait_count += 1
                        
                        if queue:
                            next_s_start, next_s_end = queue[0]
                            busy_until = next_s_end
                        else:
                            busy_until = -1.0
                    else:
                        # Handle case where head of queue doesn't match dep_t due to floating point or logic error
                        # In strict FIFO, the first item in queue should have the earliest completion time.
                        # If we maintain busy_until as the completion time of the CURRENTLY serving customer,
                        # and queue holds WAITING customers, then when a customer finishes, the next one starts.
                        # My logic above appends (start, end) for ALL customers.
                        # When dep_t occurs, it corresponds to the head of the queue IF the head was the one being served.
                        # But if there were waiting customers, their start times are later.
                        # Actually, `queue` contains all customers in system.
                        # The one leaving is the one with smallest `end`.
                        # Since we append in order of arrival, and service is FCFS, the head of queue is the one currently being served or next to be served?
                        # If server is busy, head is being served.
                        # If server idle, head is just arrived? No, if idle, new arrival starts immediately.
                        # So head is always the one whose `end` determines `busy_until`?
                        # Yes, because `busy_until` is updated to `end_service` of the latest added customer if server was busy, or `t+service` if idle.
                        # Wait, if server busy, `end_service = busy_until + service_time`. This is the completion time of the NEW customer.
                        # The OLD customer's completion time is `busy_until` (before update).
                        # So `dep_t` matches the completion time of the customer at the HEAD of the queue?
                        # Let's trace:
                        # C1 arrives t=0. Busy=-1. End=5. Busy=5. Queue=[(0,5)].
                        # C2 arrives t=1. Busy=5. End=5+5=10. Busy=10. Queue=[(0,5), (1,10)].
                        # Dep at t=5. Head is (0,5). Match. Pop. Queue=[(1,10)].
                        # New Busy?
