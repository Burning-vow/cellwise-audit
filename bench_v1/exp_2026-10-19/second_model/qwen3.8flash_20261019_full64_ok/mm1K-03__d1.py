import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    N_seeds = a.seeds
    H = a.horizon
    S_start = a.seed_start
    pert = a.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 10.0 # 6 min = 0.1 hr -> 1/0.1 = 10/hr
    c = 1
    K = 4 # capacity including service
    
    if pert == 'lam_up': lam_base *= 1.1
    elif pert == 'mu_up': mu_base *= 1.1
    elif pert == 'c_up': pass # structure change not allowed by prompt "only params", but c is param? Prompt says "perturbation only changes parameters not structure". Usually c is structural. I will ignore c_up or treat as no-op to be safe, or maybe increase lambda/mu? The prompt lists c_up. If c is fixed at 1 for this problem, c_up might mean something else or is invalid. Given "MM1K", K is capacity. Let's assume c_up doesn't apply or is ignored as per "not change structure". Actually, standard queueing perturbations often include service rate or arrival rate. I'll stick to lam/mu. If c_up is passed, I'll do nothing special as c=1 is fixed by problem statement "1 doctor".
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    results_busy_util = []
    
    total_time = 0.0
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_wait_area = 0.0
    total_busy_time = 0.0
    total_occ_area = 0.0 # For L
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        end_t = H
        
        # State: number of people in system (waiting + serving)
        n = 0
        # Next event time
        next_arrival = rng.expovariate(lam_base)
        next_departure = float('inf')
        
        # Accumulators for this seed
        s_arr = 0
        s_blk = 0
        s_dep = 0
        s_wait_area = 0.0 # Integral of (n-1) if n>1 else 0? No, W is waiting time. 
                          # Little's Law: L = lambda_eff * W. 
                          # We need average number in system L_sys and average waiting time W_q? 
                          # Problem asks for W. In MM1 context, W usually means waiting time in queue OR total time in system?
                          # Standard notation: Wq = wait in queue, W = total time in system.
                          # However, "W (minutes)" often implies the delay experienced. 
                          # Let's look at "busy_frac" definition: 1-pi0.
                          # Let's calculate L (average number in system) and W (average time in system).
                          # If W meant queue wait, it would likely say Wq.
                          # But let's check typical medical clinic context. Patients care about total time.
                          # I will compute Total Time in System (W_sys) and Number in System (L_sys).
                          
        s_total_time_in_system = 0.0 # Sum of times each patient spent in system
        s_count_completed = 0
        
        # For area integration of L (number in system)
        last_event_time = 0.0
        current_n = 0
        area_n = 0.0
        
        # For busy fraction
        busy_time = 0.0
        last_busy_state = False
        
        while True:
            # Determine next event
            if next_arrival < next_departure:
                evt_type = 'arrival'
                evt_time = next_arrival
            else:
                evt_type = 'departure'
                evt_time = next_departure
                
            if evt_time > end_t:
                break
            
            # Integrate areas up to evt_time
            dt = evt_time - last_event_time
            area_n += current_n * dt
            if current_n > 0:
                busy_time += dt
            
            # Process event
            if evt_type == 'arrival':
                s_arr += 1
                if current_n < K:
                    # Accept
                    current_n += 1
                    # Start service if idle
                    if current_n == 1:
                        # Service time drawn now
                        svc_time = rng.expovariate(mu_base)
                        next_departure = evt_time + svc_time
                        # Store departure time for this customer? 
                        # We need to track individual customers to calculate their sojourn time.
                        # Since we don't have a class, we can use a list of tuples (arrival_time, departure_time)
                        # But we process events sequentially.
                        # When a departure happens, we know who left? 
                        # FIFO assumption.
                        # We need a queue of arrival times.
                        pass
                    else:
                        # Just waiting, no new service start
                        pass
                    
                    # Add arrival time to queue
                    # We need a data structure. List is fine for small K.
                    # But we are inside a loop without classes.
                    # Let's maintain a list `queue` of arrival times.
                    # Wait, I didn't initialize `queue`.
                    # Let's restart logic with explicit queue.
                    
                    # Correction: Need to handle state properly.
                    # Let's restructure slightly within the loop.
                    pass
                else:
                    s_blk += 1
                
                # Generate next arrival
                next_arrival = evt_time + rng.expovariate(lam_base)
                
            else: # Departure
                s_dep += 1
                # Customer leaves
                # Calculate sojourn time
                # Who left? The one at front of queue.
                # We need to pop from queue.
                # But where is the queue?
                # I need to define it before the loop.
                pass
            
            last_event_time = evt_time
            # Update state variables based on event...
            
            # This inline approach is getting messy without proper state management.
            # Let's rewrite the inner simulation loop cleanly.
            
            # Resetting for clean implementation below
            break 

    # Re-implementing the simulation loop correctly
        
    sim_results = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        end_t = H
        
        n = 0 # Number in system
        queue = [] # List of arrival times of patients in system (including one being served)
        
        next_arrival = rng.expovariate(lam_base)
        next_departure = float('inf')
        
        s_arr = 0
        s_blk = 0
        s_dep = 0
        s_sum_sojourn = 0.0
        s_count_sojourn = 0
        
        last_evt_t = 0.0
        area_n = 0.0
        busy_time = 0.0
        
        while True:
            if next_arrival <= next_departure:
                evt_t = next_arrival
                evt_type = 'A'
            else:
                evt_t = next_departure
                evt_type = 'D'
                
            if evt_t > end_t:
                break
                
            dt = evt_t - last_evt_t
            area_n += n * dt
            if n > 0:
                busy_time += dt
                
            if evt_type == 'A':
                s_arr += 1
                if n < K:
                    n += 1
                    queue.append(evt_t)
                    if n == 1:
                        svc_dur = rng.expovariate(mu_base)
                        next_departure = evt_t + svc_dur
                else:
                    s_blk += 1
                next_arrival = evt_t + rng.expovariate(lam_base)
                
            else: # D
                s_dep += 1
                arr_t = queue.pop(0)
                sojourn = evt_t - arr_t
                s_sum_sojourn += sojourn
                s_count_sojourn += 1
                
                n -= 1
                if n > 0:
                    # Next person starts service
                    svc_dur = rng.expovariate(mu_base)
                    next_departure = evt_t + svc_dur
                else:
                    next_departure = float('inf')
                    
            last_evt_t = evt_t
            
        # Finalize stats for this seed
        # Remaining time to horizon
        dt_final = end_t - last_evt_t
        area_n += n * dt_final
        if n > 0:
            busy_time += dt_final
            
        avg_L = area_n / end_t
        avg_W = s_sum_sojourn / s_count_sojourn if s_count_sojourn > 0 else 0.0
        avg_busy_frac = busy_time / end_t
        avg_p_loss = s_blk / s_arr if s_arr > 0 else 0.0
        
        # p_wait: Probability that an arriving customer has to wait?
        # Or probability that a customer spends time waiting?
        # Usually P(wait) = P(n >= c) upon arrival.
        # Here c=1. So P(arrival sees n>=1).
        # We didn't track this explicitly.
        # Alternative: Fraction of customers who waited?
        # Let's estimate P_wait as fraction of accepted customers who had n>0 when they arrived?
        # Hard to get exactly without tracking.
        # Approximation: Busy fraction is related.
        # Let's count arrivals that saw n>0.
        # I need to add a counter for that.
        
        # Re-run loop with p_wait counter? 
        # To save lines, I'll approximate or modify above.
        # Modifying above is better.
        
        # Let's just output what we have and fix p_wait calculation in a second pass or adjust code.
        # Adjusting code now.
        
        # I will replace the previous block with a corrected one including p_wait tracking.
        pass

    # Corrected Simulation Block
    all_seed_stats = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        end_t = H
        
        n = 0
        queue = []
        
        next_arrival = rng.expovariate(lam_base)
        next_departure = float('inf')
        
        s_arr = 0
        s_blk = 0
        s_dep = 0
        s_sum_sojourn = 0.0
        s_count_sojourn = 0
        s_wait_count = 0 # Arrivals that had to wait (n>0 upon arrival)
        
        last_evt_t = 0.0
        area_n = 0.0
        busy_time = 0.0
        
        while True:
            if next_arrival <= next_departure:
                evt_t = next_arrival
                evt_type = 'A'
            else:
                evt_t = next_departure
                evt_type = 'D'
                
            if evt_t > end_t:
                break
                
            dt = evt_t - last_evt_t
            area_n += n * dt
            if n > 0:
                busy_time += dt
                
            if evt_type == 'A':
                s_arr += 1
                if n < K:
                    if n > 0:
                        s_wait_count += 1
                    n += 1
                    queue.append(evt_t)
                    if n == 1:
                        svc_dur = rng.expovariate(mu_base)
                        next_departure = evt_t + svc_dur
                else:
                    s_blk += 1
                next_arrival = evt_t + rng.expovariate(lam_base)
                
            else: # D
                s_dep += 1
                arr_t = queue.pop(0)
                sojourn = evt_t - arr_t
                s_sum_sojourn += sojourn
                s_count_sojourn += 1
                
                n -= 1
                if n > 0:
                    svc_dur = rng.expovariate(mu_base)
                    next_departure = evt_t + svc_dur
                else:
                    next_departure = float('inf')
                    
            last_evt_t = evt_t
            
        dt_final = end_t - last_evt_t
        area_n += n * dt_final
        if n > 0:
            busy_time += dt_final
            
        L_val = area_n / end_t
        W_val = s_sum_sojourn / s_count_sojourn if s_count_sojourn > 0 else 0.0
        BF_val = busy_time / end_t
        PL_val = s_blk / s_arr if s_arr > 0 else 0.0
        PW_val = s_wait_count / s_arr if s_arr > 0 else 0.0
        
        # Busy Util E[min(N,c)]/c. Since c=1, min(N,1) is 1 if N>0 else 0.
        # So E[min(N,1)] = P(N>0) = Busy Fraction.
        # Thus busy_util = BF_val / 1 = BF_val.
        BU_val = BF_val
        
        all_seed_stats.append({
            'L': L_val, 'W': W_val, 'BF': BF_val, 'PL': PL_val, 'PW': PW_val,
            'arr': s_arr, 'blk': s_blk, 'dep': s_dep, 'BU': BU_val
        })
        
    # Aggregate
    num_seeds = len(all_seed_stats)
    sum_L = sum(s['L'] for s in all_seed_stats)
    sum_W = sum(s['W'] for s in all_seed_stats)
    sum_BF = sum(s['BF'] for s in all_seed_stats)
    sum_PL = sum(s['PL'] for s in all_seed_stats)
    sum_PW = sum(s['PW'] for s in all_seed_stats)
    sum_arr = sum(s['arr'] for s in all_seed_stats)
    sum_blk = sum(s['blk'] for s in all_seed_stats)
    sum_dep = sum(s['dep'] for s in all_seed_stats)
    sum_BU = sum(s['BU'] for s in all_seed_stats)
    
    avg_L = sum_L / num_seeds
    avg_W = sum_W / num_seeds
    avg_BF = sum_BF / num_seeds
    avg_PL = sum_PL / num_seeds
    avg_PW = sum_PW / num_seeds
    avg_arr = sum_arr / num_seeds
    avg_blk = sum_blk / num_seeds
    avg_dep = sum_dep / num_seeds
    avg_BU = sum_BU / num_seeds
    
    # Dep rate per hour
    dep_rate = avg_dep / H
    
    # Lam eff
    lam_eff = avg_dep / H # Assuming stability, dep rate ~ effective arrival rate
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W * 60, 4), # Convert hours to minutes
        "busy_frac": round(avg_BF, 4),
        "p_loss": round(avg_PL, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": num_seeds,
        "time_unit": "hour",
        "win": H,
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_BU, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(avg_PW, 4),
        "per_seed_L": [round(s['L'], 4) for s in all_seed_stats],
        "per_seed_W": [round(s['W'] * 60, 4) for s in all_seed_stats],
        "per_seed_busy_frac": [round(s['BF'], 4) for s in all_seed_stats],
        "per_seed_p_loss": [round(s['PL'], 4) for s in all_seed_stats],
        "per_seed_p_wait": [round(s['PW'], 4) for s in all_seed_stats]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
