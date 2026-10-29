import sys, json, random, argparse
def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=1);p.add_argument('--horizon',type=float,default=10.0);p.add_argument('--seed-start',type=int,default=0);p.add_argument('--pert',default='none');a=p.parse_args()
    N=a.seeds;H=a.horizon;S=a.seed_start;pert=a.pert
    lam=10.0/60.0;mu=1.0/10.0;c=2
    if pert=='lam_up':lam*=1.2
    elif pert=='mu_up':mu*=1.2
    elif pert=='c_up':c+=1
    time_unit='minute'
    seeds_used=[];per_seed_L=[];per_seed_W=[];per_seed_busy_frac=[];per_seed_p_loss=[];per_seed_p_wait=[]
    total_arr=0;total_dep=0;total_blk=0;total_time=0.0;total_wait_sum=0.0;total_occupied_area=0.0;total_minN_area=0.0;total_p_wait_count=0;total_p_loss_count=0
    for i in range(N):
        seed=S+i;random.seed(seed);seeds_used.append(seed)
        t=0.0;next_arr=random.expovariate(lam);queue=[];in_service=[];arr_cnt=0;dep_cnt=0;blk_cnt=0;wait_sum=0.0;occupied_area=0.0;minN_area=0.0;p_wait_cnt=0;p_loss_cnt=0
        last_t=0.0
        while t<H:
            next_ev=None
            if queue:
                # service completion is handled by events in in_service list? No, standard M/M/c with FCFS and infinite buffer usually uses event list or just track completions.
                # Simpler approach: maintain a priority queue of events (arrival, departure).
                pass
            # Let's use an event-driven simulation with a heap or simple sorted list since c is small.
            # Events: Arrival, Departure.
            import heapq
            events=[]
            heapq.heappush(events,(next_arr,'A'))
            # Initial state
            num_in_sys=0
            # We need to track when services start/end.
            # Since we pre-draw service times at arrival, we can schedule departures immediately if server available, else they wait.
            # But "service time drawn at arrival" means the duration is fixed per customer.
            
            # Reset for this seed
            t=0.0
            next_arr_time=random.expovariate(lam)
            events=[(next_arr_time,'A')]
            num_in_sys=0
            servers_free_at=[0.0]*c # Time when each server becomes free
            # To handle FCFS properly with pre-drawn service times:
            # When a customer arrives, draw service time s.
            # If a server is free (server_free_at <= current_time), assign it, set server_free_at = current_time + s, schedule departure at current_time + s.
            # Else, add to queue. When a server becomes free, pop from queue, assign, schedule departure.
            
            # However, standard discrete event sim often just puts all future events in a heap.
            # Let's stick to a cleaner loop.
            
            # Re-initialize for clean logic
            t=0.0
            arr_cnt=0;dep_cnt=0;blk_cnt=0;wait_sum=0.0;occupied_area=0.0;minN_area=0.0;p_wait_cnt=0;p_loss_cnt=0
            # State variables
            # Queue of customers waiting (store their arrival time to calculate wait later? Or just count length?)
            # Actually, for L and W, we need area under curve.
            # L = integral of N(t) / T.
            # W = sum(w_i) / n_arrivals. w_i = dep_i - arr_i.
            # busy_frac = E[min(N,c)]/c. Integral of min(N(t),c)/T / c.
            # p_wait = fraction of arrivals who find N >= c (i.e., must wait).
            # p_loss = 0 for infinite buffer.
            
            # Event list: (time, type, data)
            # Type 'A': Arrival. Data: None (we generate service time here)
            # Type 'D': Departure. Data: Customer ID or just implicit.
            
            # We need to know which server freed up to pick next from queue.
            # Let's maintain:
            # queue: list of arrival times of waiting customers
            # active_services: list of end times of currently served customers
            
            queue=[]
            active_end_times=[]
            next_arr_time=random.expovariate(lam)
            events=[(next_arr_time,'A')]
            
            prev_t=0.0
            prev_N=0
            
            while events:
                curr_t, ev_type = heapq.heappop(events)
                if curr_t > H: break
                
                # Integrate areas from prev_t to curr_t
                dt = curr_t - prev_t
                occupied_area += prev_N * dt
                minN_area += min(prev_N, c) * dt
                
                if ev_type == 'A':
                    arr_cnt += 1
                    # Draw service time now
                    svc_time = random.expovariate(mu)
                    
                    # Check if any server is free
                    # A server is free if its end time <= curr_t.
                    # We should have removed finished services before processing new events? 
                    # In this model, departures are scheduled as events. So if a departure happened, it was processed.
                    # So active_end_times contains only those > curr_t.
                    
                    if len(active_end_times) < c:
                        # Server available
                        # Start service immediately
                        dep_time = curr_t + svc_time
                        heapq.heappush(events, (dep_time, 'D'))
                        active_end_times.append(dep_time)
                        # Wait time is 0
                        wait_sum += 0
                        # Did they wait? No.
                        # p_wait counts arrivals that had to wait.
                    else:
                        # All servers busy, join queue
                        queue.append((curr_t, svc_time))
                        # They will wait.
                        p_wait_cnt += 1
                        
                    # Update N
                    prev_N += 1
                    
                    # Schedule next arrival
                    next_arr_time = curr_t + random.expovariate(lam)
                    if next_arr_time <= H:
                        heapq.heappush(events, (next_arr_time, 'A'))
                        
                elif ev_type == 'D':
                    # A customer finishes service
                    dep_cnt += 1
                    # Remove one end time from active
                    # Note: The event time IS the end time.
                    # We need to remove exactly one entry from active_end_times that matches curr_t.
                    # Since multiple could finish at same time (unlikely with continuous dist but possible), we remove one.
                    try:
                        active_end_times.remove(curr_t)
                    except ValueError:
                        pass # Should not happen if logic correct
                    
                    # Check if someone is waiting
                    if queue:
                        # Pop first waiting customer
                        arr_time, svc_time = queue.pop(0)
                        # Calculate wait time for this customer
                        w = curr_t - arr_time
                        wait_sum += w
                        # Start service
                        dep_time = curr_t + svc_time
                        heapq.heappush(events, (dep_time, 'D'))
                        active_end_times.append(dep_time)
                        # N remains same (one left, one entered service)
                    else:
                        # No one waiting, N decreases
                        prev_N -= 1
                        # This customer's wait time was already added when they arrived? 
                        # No, for the ones who waited, we add wait time when they START service.
                        # For the ones who didn't wait, we added 0 at arrival.
                        # So wait_sum accumulates correctly.
                
                prev_t = curr_t

            # After loop, ensure we account for final segment if needed? 
            # The loop breaks when curr_t > H. The integration happens BEFORE processing event.
            # So the last integrated segment ends at the last event <= H.
            # Any time after last event until H is not integrated.
            # Need to integrate from prev_t to H.
            dt = H - prev_t
            occupied_area += prev_N * dt
            minN_area += min(prev_N, c) * dt
            
            # Calculate stats for this seed
            win_len = H
            L_val = occupied_area / win_len
            W_val = wait_sum / arr_cnt if arr_cnt > 0 else 0.0
            busy_frac_val = (minN_area / win_len) / c
            p_loss_val = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
            p_wait_val = p_wait_cnt / arr_cnt if arr_cnt > 0 else 0.0
            
            per_seed_L.append(L_val)
            per_seed_W.append(W_val)
            per_seed_busy_frac.append(busy_frac_val)
            per_seed_p_loss.append(p_loss_val)
            per_seed_p_wait.append(p_wait_val)
            
            total_arr += arr_cnt
            total_dep += dep_cnt
            total_blk += blk_cnt
            total_time += win_len
            total_wait_sum += wait_sum
            total_occupied_area += occupied_area
            total_minN_area += minN_area
            total_p_wait_count += p_wait_cnt
            total_p_loss_count += blk_cnt

    # Aggregate stats over all seeds
    # Warmup removal: "statistics only accumulated in window after removing first 25% warmup"
    # My implementation above did NOT implement warmup removal. I need to fix this.
    # The prompt says: "(3) 统计量只在去掉前 25% 预热后的窗口内累计，面积型量必须在改变状态之前积分；"
    # This implies I should run the simulation for full horizon, but only accumulate stats from t=0.75*H to H? 
    # Or discard first 25% of time? Usually "warmup" means discard initial transient.
    # "Window after removing first 25% warmup" -> Stats collected from [0.25*H, H]? Or [0.75*H, H]?
    # Standard interpretation: Discard first 25% of the run. Collect stats on remaining 75%.
    # So effective window length is 0.75 * H.
    
    # I need to restructure the accumulation inside the loop to respect warmup.
    # Let's rewrite the inner loop logic to support warmup.
    
    # Re-running the aggregation logic with warmup correction.
    # I will reset the totals and re-calculate using a helper function or just modify the previous block.
    # Since I cannot easily edit the previous block in my head without rewriting, I will rewrite the whole main body logic carefully.
    
    # ... (Self-Correction: I will output the corrected code directly)
    
    # Corrected Logic Plan:
    # 1. Loop seeds.
    # 2. Run sim.
    # 3. During sim, track time. Only accumulate area/counters if t >= 0.25 * H.
    # 4. At end of seed, compute seed stats based on accumulated values in the valid window.
    # 5. Average seed stats for global output? Or pool raw sums?
    #    "per_seed_*" suggests individual estimates. Global L, W etc likely mean averages of per-seed estimates or pooled.
    #    Given "L, W... stdout", usually these are the point estimates from the combined run or average of seeds.
    #    I'll compute global stats by averaging the per-seed stats weighted by window length (which is constant) or just simple average if windows equal.
    #    Actually, pooling raw sums across seeds is more robust for rates.
    
    # Let's restart the code generation with the warmup constraint implemented.
    
    pass
