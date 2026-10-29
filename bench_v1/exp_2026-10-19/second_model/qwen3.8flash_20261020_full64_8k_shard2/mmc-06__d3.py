import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 14.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0     # service rate per minute (mean 6 min)
    c = 2                   # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = H if args.horizon > 0 else 100.0
    warmup_frac = 0.25
    win_len = horizon_min * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] # (time, type, data) type: 0=arrival, 1=departure
        
        # State
        n_in_system = 0
        busy_servers = 0
        queue = [] # list of arrival times or customer objects? Need to track wait time.
        # Let's store customers as dicts with arrival_time and service_time
        active_services = [] # list of end_times
        
        # Statistics accumulators (for area integration)
        area_L = 0.0
        last_event_time = 0.0
        
        # Counters within window
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0 # sum of waiting+service times for completed customers in window
        p_wait_hits = 0 # number of arrivals that had to wait (queue length > 0 at arrival)
        
        # We need to handle the warmup period. 
        # Strategy: Simulate until horizon. 
        # For L (area), integrate only from warmup_end to horizon.
        # For W, p_wait, etc., count only events occurring after warmup_end.
        
        warmup_end = horizon_min * warmup_frac
        
        # Initialize first event
        heapq = None # not using heapq module to keep stdlib simple, use sorted insertion or just process sequentially?
        # Discrete Event Simulation usually uses a priority queue. 
        # Since we can't import heapq? "standard library" includes heapq. But prompt says "only output runnable python... no third party". heapq is standard.
        # However, to be safe and minimal, I'll implement a simple list-based PQ since N is likely small enough or I can use heapq.
        import heapq
        
        heap = []
        heapq.heappush(heap, (next_arrival, 0, None)) # 0=arrival
        
        while heap:
            current_t, etype, edata = heapq.heappop(heap)
            
            if current_t > horizon_min:
                break
                
            # Update Area for L before processing event
            if current_t > warmup_end:
                dt = current_t - max(last_event_time, warmup_end)
                if dt > 0:
                    area_L += n_in_system * dt
            
            last_event_time = current_t
            
            if etype == 0: # Arrival
                # Generate service time now
                svc_time = rng.expovariate(mu)
                
                # Check if server available
                if busy_servers < c:
                    # Start service immediately
                    busy_servers += 1
                    end_t = current_t + svc_time
                    heapq.heappush(heap, (end_t, 1, svc_time)) # 1=departure, data=svc_time (not strictly needed but good practice)
                    n_in_system += 1
                    if current_t >= warmup_end:
                        arr_count += 1
                        # Wait time is 0
                        wait_sum += svc_time # Total time in system = wait + service. Here wait=0.
                        p_wait_hits += 0 # Did not wait
                else:
                    # Queue
                    n_in_system += 1
                    queue.append((current_t, svc_time))
                    if current_t >= warmup_end:
                        arr_count += 1
                        p_wait_hits += 1 # Had to wait
                        
            elif etype == 1: # Departure
                # Find who leaves. FCFS.
                # If queue is empty, this departure corresponds to one of the active services.
                # But we don't track individual active services easily without IDs.
                # Alternative approach: Track completion times of all started services.
                # When a service starts, push its end time.
                # When an end time pops, it means a customer leaves.
                # But which customer? The one who started earliest among those still in system?
                # Actually, simpler: Just decrement busy_servers.
                # And check if queue has people. If yes, start next service.
                
                busy_servers -= 1
                n_in_system -= 1
                
                if current_t >= warmup_end:
                    dep_count += 1
                    
                # If there are people in queue, start service for the head of queue
                if queue:
                    arr_t, svc_t = queue.pop(0)
                    # This customer was waiting. Now starts service.
                    busy_servers += 1
                    end_t = current_t + svc_t
                    heapq.heappush(heap, (end_t, 1, svc_t))
                    
                    # Calculate total time in system for this customer
                    total_time = current_t + svc_t - arr_t
                    if current_t >= warmup_end:
                        # Note: The arrival happened earlier. 
                        # The problem asks for average W over the window.
                        # Usually, we attribute the metric to the completion time or arrival time?
                        # Standard regenerative method or batch means often attributes to completion.
                        # Prompt: "statistics ... accumulated in window after removing warmup".
                        # If we attribute to completion time, we add to wait_sum here.
                        wait_sum += total_time
                        # p_wait was already counted at arrival.
                else:
                    # No one in queue, nothing to do.
                    pass

        # Final area update up to horizon
        if horizon_min > warmup_end:
            dt = horizon_min - max(last_event_time, warmup_end)
            if dt > 0:
                area_L += n_in_system * dt
        
        # Calculate metrics for this seed
        if win_len > 0:
            L_est = area_L / win_len
            # W estimation: Average total time in system for customers completing in window?
            # Or average for all customers arriving in window?
            # Common definition: Little's Law consistency. 
            # Let's use: Sum of total times for completions in window / Number of completions in window.
            # But some arrivals in window might complete after window.
            # To be robust, let's assume steady state approximation or just use the counts we have.
            # If dep_count > 0:
            if dep_count > 0:
                W_est = wait_sum / dep_count
            else:
                W_est = 0.0
                
            # Busy fraction: E[min(N,c)]/c. 
            # We integrated n_in_system. But we need integral of min(n_in_system, c).
            # My previous area_L calculation used n_in_system. 
            # I need to re-calculate area for busy_util correctly.
            # Let's restart the loop logic slightly or fix the accumulation.
            # Actually, I didn't accumulate min(N,c) area. I only accumulated N.
            # I need to go back and fix the simulation loop to accumulate both.
            
            # Re-running simulation for correct busy_util area? 
            # No, I should have done it in the first place. 
            # Let's refactor the inner loop to track area_busy = integral(min(n,c)).
            
            # Since I cannot easily edit the past code in my head without rewriting, 
            # I will rewrite the simulation block inside the seed loop properly.
            pass 

    # Because I realized the area calculation for busy_util was missing in the draft above,
    # I must ensure the final code calculates it correctly.
    # I will write the full corrected code below.

    # Resetting variables for final clean implementation
    results = {}
    
    # Helper to run one seed
    def run_seed(seed_val):
        rng = random.Random(seed_val)
        t = 0.0
        horizon = horizon_min
        warmup = horizon * warmup_frac
        win = horizon - warmup
        
        # Events: (time, type, data)
        # Type 0: Arrival, Type 1: Departure
        heap = []
        next_arr = rng.expovariate(lam)
        heapq.heappush(heap, (next_arr, 0, None))
        
        n_sys = 0
        busy_cnt = 0
        queue = [] # stores (arrival_time, service_duration)
        
        area_n = 0.0
        area_busy = 0.0 # integral of min(n_sys, c)
        last_t = 0.0
        
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        sum_w = 0.0
        cnt_wait = 0 # arrivals that waited
        
        while heap:
            ct, et, ed = heapq.heappop(heap)
            if ct > horizon:
                break
            
            # Integrate areas
            if ct > warmup:
                dt = ct - max(last_t, warmup)
                if dt > 0:
                    area_n += n_sys * dt
                    area_busy += min(n_sys, c) * dt
            
            last_t = ct
            
            if et == 0: # Arrival
                svc_dur = rng.expovariate(mu)
                
                if busy_cnt < c:
                    busy_cnt += 1
                    n_sys += 1
                    end_t = ct + svc_dur
                    heapq.heappush(heap, (end_t, 1, svc_dur))
                    if ct >= warmup:
                        cnt_arr += 1
                        sum_w += svc_dur # total time = 0 wait + svc
                        # did not wait
                else:
                    n_sys += 1
                    queue.append((ct, svc_dur))
                    if ct >= warmup:
                        cnt_arr += 1
                        cnt_wait += 1
                        
            elif et == 1: # Departure
                busy_cnt -= 1
                n_sys -= 1
                
                if ct >= warmup:
                    cnt_dep += 1
                
                if queue:
                    arr_t, dur = queue.pop(0)
                    busy_cnt += 1
                    n_sys += 1 # Still in system, just moved from queue to service
                    end_t = ct + dur
                    heapq.heappush(heap, (end_t, 1, dur))
                    
                    total_time = ct + dur - arr_t
                    if ct >= warmup:
                        sum_w += total_time
                else:
                    pass
        
        # Final integration
        if horizon > warmup:
            dt = horizon - max(last_t, warmup)
            if dt > 0:
                area_n += n_sys * dt
                area_busy += min(n_sys, c) * dt
        
        L = area_n / win if win > 0 else 0
        busy_util = area_busy / win if win > 0 else 0
        busy_frac = busy_util / c
        
        W = sum_w / cnt_dep if cnt_dep > 0 else 0
        p_wait = cnt_wait / cnt_arr if cnt_arr > 0 else 0
        p_loss = 0 # Infinite buffer assumed, so loss is 0 unless specified otherwise. 
                   # Problem doesn't mention blocking capacity limit, just "bank branch". 
                   # Usually infinite queue. So blk=0, p_loss=0.
        
        return {
            'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
            'arr': cnt_arr, 'dep': cnt_dep, 'blk': 0,
            'busy_util': busy_util, 'dep_rate': (cnt_dep / win) * 60 if win > 0 else 0,
            'lam_eff': (cnt_arr / win) * 60 if win > 0 else 0,
            'p_loss': 0.0
        }

    seeds_used = 0
    agg_L = 0; agg_W = 0; agg_bf = 0; agg_pw = 0
    agg_arr = 0; agg_dep = 0; agg_blk = 0; agg_bu = 0; agg_dr = 0; agg_le = 0; agg_pl = 0
    
    ps_L = []; ps_W = []; ps_bf = []; ps_pl = []; ps_pw = []
    
    for i in range(N_seeds):
        s = S_start + i
        res = run_seed(s)
        seeds_used += 1
        seed_list.append(s)
        
        agg_L += res['L']
        agg_W += res['W']
        agg_bf += res['busy_frac']
        agg_pw += res['p_wait']
        agg_arr += res['arr']
        agg_dep += res['dep']
        agg_blk += res['blk']
        agg_bu += res['busy_util']
        agg_dr += res['dep_rate']
        agg_le += res['lam_eff']
        agg_pl += res['p_loss']
        
        ps_L.append(res['L'])
        ps_W.append(res['W'])
        ps_bf.append(res['busy_frac'])
        ps_pl.append(res['p_loss'])
        ps_pw.append(res['p_wait'])
        
    if seeds_used > 0:
        out = {
            "L": agg_L / seeds_used,
            "W": agg_W / seeds_used,
            "busy_frac": agg_bf / seeds_used,
            "p_wait": agg_pw / seeds_used,
            "runtime_units": "minute",
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": "minute",
            "win": win_len,
            "arr": agg_arr / seeds_used,
            "blk": agg_blk / seeds_used,
            "busy_util": agg_bu / seeds_used,
            "dep": agg_dep / seeds_used,
            "dep_rate": agg_dr / seeds_used,
            "lam_eff": agg_le / seeds_used,
            "p_loss": agg_pl / seeds_used,
            "per_seed_L": ps_L,
            "per_seed_W": ps_W,
            "per_seed_busy_frac": ps_bf,
            "per_seed_p_loss": ps_pl,
            "per_seed_p_wait": ps_pw
        }
    else:
        out = {"error": "no seeds"}

    print(json.dumps(out))

if __name__ == "__main__":
    main()
