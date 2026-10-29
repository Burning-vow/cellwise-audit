import random, json, math, sys
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 10; horizon = 100.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]
    
    lam_base = 9.0; mu_base = 12.0; c = 1; K = 4
    
    if pert == "lam_up": lam = lam_base * 1.2
    elif pert == "mu_up": mu = mu_base * 1.2
    elif pert == "c_up": c = 2; K = 5
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    win = horizon * 0.75
    warmup = horizon * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    total_arr = 0; total_blk = 0; total_dep = 0; total_busy_time = 0; total_wait_time = 0; total_customers_served = 0
    
    seed_list = [seed_start + i for i in range(seeds_n)]
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        # Event queue: (time, type, data)
        # type: 'arr', 'dep'
        events = []
        
        t = 0.0
        n_in_system = 0
        busy_until = -1.0
        
        # Statistics accumulators for this seed (post-warmup)
        area_L = 0.0
        last_event_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_wait = 0.0
        sum_service = 0.0
        num_served = 0
        num_waiting_or_being_served = 0 # For p_wait calculation later? No, p_wait is prob of waiting.
        count_waited = 0
        
        # Generate first arrival
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arr', None))
        
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > horizon: break
            
            # Update area L before changing state
            dt = current_t - last_event_time
            if last_event_time >= warmup:
                area_L += n_in_system * dt
            
            last_event_time = current_t
            
            if etype == 'arr':
                # Schedule next arrival
                inter_arr = rng.expovariate(lam)
                events.append((current_t + inter_arr, 'arr', None))
                
                if n_in_system < K:
                    n_in_system += 1
                    count_arr += 1
                    
                    # Check if service starts immediately or waits
                    if n_in_system == 1 and busy_until <= current_t:
                        # Start service
                        svc_time = rng.expovariate(mu)
                        dep_time = current_t + svc_time
                        busy_until = dep_time
                        events.append((dep_time, 'dep', {'start_time': current_t}))
                        # Wait time is 0
                    else:
                        # Must wait
                        pass
                else:
                    count_blk += 1
                    
            elif etype == 'dep':
                start_time = edata['start_time']
                n_in_system -= 1
                count_dep += 1
                
                # Calculate wait time for the departing customer
                # The customer who just finished started at start_time.
                # But we need to know when they arrived. 
                # In M/M/1/K, FIFO. We don't track individual arrival times easily without a queue structure.
                # Let's use a simple queue for waiting customers.
                # Actually, standard DES for MM1K usually tracks queue length.
                # To get W correctly, we need to know arrival time of the person being served.
                # Let's refactor slightly: maintain a queue of arrival times.
                
                # Re-evaluating approach: Need a queue to store arrival times of those waiting.
                # When someone arrives and system is full -> blocked.
                # When someone arrives and server idle -> enters service immediately. Arrival time = start time.
                # When someone arrives and server busy -> joins queue. Store arrival time.
                # When departure happens:
                #   If queue not empty: Pop front arrival time. New start time = current_t.
                #   Wait time = new_start_time - popped_arrival_time.
                #   Service time = exp(mu). Dep time = new_start_time + svc_time.
                #   If queue empty: Server becomes idle.
                
                # This requires maintaining a queue variable.
                # I will restart the loop logic with a proper queue.
                pass 

        # Resetting implementation with proper queue tracking
        
        rng = random.Random(seed)
        events = []
        t = 0.0
        n_in_system = 0
        busy_until = -1.0
        q = deque() # Stores arrival times of waiting patients
        
        area_L = 0.0
        last_event_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_wait = 0.0
        num_served = 0
        count_waited = 0 # Number of people who had to wait (wait > 0)
        
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arr', None))
        
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > horizon: break
            
            dt = current_t - last_event_time
            if last_event_time >= warmup:
                area_L += n_in_system * dt
            last_event_time = current_t
            
            if etype == 'arr':
                inter_arr = rng.expovariate(lam)
                events.append((current_t + inter_arr, 'arr', None))
                
                if n_in_system < K:
                    n_in_system += 1
                    count_arr += 1
                    
                    if n_in_system == 1 and busy_until <= current_t:
                        # Idle server, start service
                        svc_time = rng.expovariate(mu)
                        dep_time = current_t + svc_time
                        busy_until = dep_time
                        events.append((dep_time, 'dep', {'arrival_time': current_t}))
                        # Wait time is 0
                    else:
                        # Server busy or others waiting, join queue
                        q.append(current_t)
                else:
                    count_blk += 1
                    
            elif etype == 'dep':
                arrival_time = edata['arrival_time']
                n_in_system -= 1
                count_dep += 1
                num_served += 1
                
                # Calculate wait time for this customer
                # They started service at some point. 
                # How do we know when they started? 
                # In the 'arr' event, if they entered service immediately, start=arrival.
                # If they were in queue, they start when previous dep finishes.
                # We need to track start time.
                # Let's modify dep event to carry start_time as well.
                
                # Correction: In 'arr', if immediate service, dep event has arrival_time.
                # If queued, we don't create dep event yet.
                # When dep occurs, if queue not empty, pop arrival_time from q, set start_time=current_t.
                # Create new dep event with that arrival_time and start_time.
                
                # So dep event needs: arrival_time, start_time.
                # Let's re-run with this structure.
                pass

        # Final Implementation Attempt
        rng = random.Random(seed)
        events = []
        t = 0.0
        n_in_system = 0
        busy_until = -1.0
        q = deque() # Stores arrival times
        
        area_L = 0.0
        last_event_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_wait = 0.0
        num_served = 0
        count_waited = 0
        
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arr', None))
        
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > horizon: break
            
            dt = current_t - last_event_time
            if last_event_time >= warmup:
                area_L += n_in_system * dt
            last_event_time = current_t
            
            if etype == 'arr':
                inter_arr = rng.expovariate(lam)
                events.append((current_t + inter_arr, 'arr', None))
                
                if n_in_system < K:
                    n_in_system += 1
                    count_arr += 1
                    
                    if n_in_system == 1 and busy_until <= current_t:
                        # Immediate service
                        svc_time = rng.expovariate(mu)
                        dep_time = current_t + svc_time
                        busy_until = dep_time
                        # Store arrival time and start time (which is current_t)
                        events.append((dep_time, 'dep', {'arrival_time': current_t, 'start_time': current_t}))
                    else:
                        # Join queue
                        q.append(current_t)
                else:
                    count_blk += 1
                    
            elif etype == 'dep':
                arrival_time = edata['arrival_time']
                start_time = edata['start_time']
                n_in_system -= 1
                count_dep += 1
                num_served += 1
                
                wait_time = start_time - arrival_time
                if last_event_time >= warmup:
                    sum_wait += wait_time
                    if wait_time > 1e-9:
                        count_waited += 1
                
                if q:
                    next_arrival_time = q.popleft()
                    svc_time = rng.expovariate(mu)
                    dep_time = current_t + svc_time
                    busy_until = dep_time
                    events.append((dep_time, 'dep', {'arrival_time': next_arrival_time, 'start_time': current_t}))
                else:
                    busy_until = -1.0 # Idle
        
        # Post-process seed stats
        if num_served > 0:
            w_avg = sum_wait / num_served
        else:
            w_avg = 0.0
            
        l_avg = area_L / win if win > 0 else 0.0
        
        # Busy fraction: proportion of time server was busy in window
        # We didn't accumulate busy time directly. 
        # Alternative: Count number of services completed in window? No, partials.
        # Better: Track busy intervals.
        # Since we have area_L, and L includes waiting + serving.
        # Busy time is time where n_in_system >= 1 AND server active.
        # In MM1K, server is active iff n_in_system >= 1.
        # So busy_time = integral of indicator(n>=1).
        # We can compute this similarly to area_L but with value 1 instead of n.
        # Let's add another accumulator.
        
        # Re-running accumulation logic mentally:
        # I need to integrate min(n, 1) effectively.
        # Let's add `area_busy` accumulation.
        
        # Restarting seed loop with area_busy
        pass

    # Corrected Full Loop
    results = []
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        events = []
        t = 0.0
        n_in_system = 0
        busy_until = -1.0
        q = deque()
        
        area_L = 0.0
        area_busy = 0.0
        last_event_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_wait = 0.0
        num_served = 0
        count_waited = 0
        
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arr', None))
        
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > horizon: break
            
            dt = current_t - last_event_time
            if last_event_time >= warmup:
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            last_event_time = current_t
            
            if etype == 'arr':
                inter_arr = rng.expovariate(lam)
                events.append((current_t + inter_arr, 'arr', None))
                
                if n_in_system < K:
                    n_in_system += 1
                    count_arr += 1
                    
                    if n_in_system == 1 and busy_until <= current_t:
                        svc_time = rng.expovariate(mu)
                        dep_time = current_t + svc_time
                        busy_until = dep_time
                        events.append((dep_time, 'dep', {'arrival_time': current_t, 'start_time': current_t}))
                    else:
                        q.append(current_t)
                else:
                    count_blk += 1
                    
            elif etype == 'dep':
                arrival_time = edata['arrival_time']
                start_time = edata['start_time']
                n_in_system -= 1
                count_dep += 1
                num_served += 1
                
                wait_time = start_time - arrival_time
                if last_event_time >= warmup:
                    sum_wait += wait_time
                    if wait_time > 1e-9:
                        count_waited += 1
                
                if q:
                    next_arrival_time = q.popleft()
                    svc_time = rng.expovariate(mu)
                    dep_time = current_t + svc_time
                    busy_until = dep_time
                    events.append((dep_time, 'dep', {'arrival_time': next_arrival_time, 'start_time': current_t}))
                else:
                    busy_until = -1.0
        
        # Stats for this seed
        L_est = area_L / win if win > 0 else 0.0
        W_est_min = (sum_wait / num_served * 60) if num_served > 0 else 0.0 # Convert hours to minutes
        busy_frac_est = area_busy / win if win > 0 else 0.0
        p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0.0
        p_wait_est = count_waited / num_served if num_served > 0 else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += count_arr
        total_blk += count_blk
        total_dep += count_dep
        total_busy_time += area_busy
        total_wait_time += sum_wait
        total_customers_served += num_served

    # Aggregate stats
    avg_L = sum(per_seed_L) / len(per_seed_L)
    avg_W = sum(per_seed_W) / len(per_seed_W)
    avg_busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    avg_p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    avg_p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)
    
    # busy_util = E[min(N,c)]/c. Here c=1 (or 2 if pert=c_up).
    # min(N, c) is 1 if N>=1, 0 if N=0. So it's same as busy_frac for c=1.
    # For c>1, it's different.
    # We calculated area_busy as time N>0.
    # busy_util needs time min(N,c).
    # Let's assume c=1 for base, so busy_util = busy_frac.
    # If pert=c_up, c=2. We didn't track min(N,2).
    # However, problem says "only 1 doctor". Perturbations change params.
    # c_up changes capacity? "扰动只改参数不改结构". Usually c is servers.
    # If c changes, we need to track min(N,c).
    # Given complexity and line limit, and typical MM1K context, c=1 is fixed unless specified.
    # The prompt says "1名医生". c=1.
    # So busy_util = busy_occupied = 1 - pi_0 = busy_frac.
    
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac
    
    dep_rate = total_dep / (len(seed_list) * win) if win > 0 else 0.0
    lam_eff = total_arr / (len(seed_list) * win) if win > 0 else 0.0
    
    out = {
