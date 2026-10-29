import sys, json, random, argparse
from collections import deque

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

    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr
    c = 1
    K = 6 # capacity including service

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Capacity perturbation not explicitly defined for M/M/1/K in prompt context usually, 
        # but "pert only changes parameters". If c_up means capacity up? 
        # Prompt says "NAME takes none/lam_up/mu_up/c_up". 
        # Usually c is servers. Here c=1 fixed by problem statement "only 1 doctor".
        # Maybe c_up refers to something else or is a distractor? 
        # Given "M/M/1", c is likely 1. Let's assume c_up does nothing or increases capacity K?
        # The prompt says "disturbance only changes parameters not structure".
        # If it changes K, that's structural? No, K is a parameter.
        # Let's assume c_up increases K slightly or does nothing if ambiguous.
        # However, standard queueing perturbations are lambda and mu.
        # Let's stick to base params if pert is unknown or c_up doesn't map clearly to 1 server.
        # Actually, let's look at the keys: busy_util=E[min(N,c)]/c. c is number of servers.
        # Problem says "1 doctor". So c=1.
        # I will treat c_up as no change to lam/mu, maybe increase K? 
        # But K is system capacity. Let's just use base params for c_up to be safe unless specified.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Queue: list of (arrival_time, service_duration)
        # We need to store service duration at arrival.
        queue = deque()
        
        # Statistics accumulators (for area integration)
        # We integrate over time.
        # L_area = integral of N(t) dt
        # Busy_area = integral of 1_{N(t)>0} dt
        # Wait_area = integral of 1_{queue length > 0} dt ? 
        # p_wait usually P(wait > 0). In steady state, fraction of customers who wait.
        # Or time-average probability that an arriving customer waits?
        # Standard definition: P(W>0). For Poisson arrivals, this equals fraction of arrivals who find server busy.
        # Let's track count of arrivals who waited vs total accepted arrivals.
        
        L_area = 0.0
        Busy_area = 0.0
        Occupied_area = 0.0 # Same as Busy_area for single server? 
        # busy_frac = 1 - pi_0 = P(server busy).
        # busy_util = E[min(N,c)]/c. For c=1, E[N]/1? No, E[min(N,1)].
        # If N>=1, min(N,1)=1. If N=0, 0. So E[min(N,1)] = P(N>=1) = busy_frac.
        # So busy_util == busy_frac for c=1.
        
        # Counters
        n_arrivals = 0
        n_blocked = 0
        n_departures = 0
        n_waited = 0 # Arrivals who had to wait (server busy upon arrival)
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        
        # Current state variables for integration
        last_event_time = 0.0
        current_N = 0 # Number in system
        
        # Event loop
        while t < H:
            # Determine next event time
            t_arr = next_arrival
            t_dep = next_departure
            
            if t_arr <= t_dep:
                # Arrival
                t = t_arr
                dt = t - last_event_time
                
                # Integrate stats before updating state
                if last_event_time >= warmup_end:
                    L_area += current_N * dt
                    if current_N > 0:
                        Busy_area += dt
                        Occupied_area += dt # For c=1, occupied is same as busy
                
                # Process arrival
                n_arrivals += 1
                if len(queue) + (1 if current_N > 0 else 0) < K:
                    # Accept
                    # Generate service time now
                    svc_time = rng.expovariate(mu)
                    
                    # Check if waiting
                    if current_N > 0:
                        n_waited += 1
                    
                    # Add to queue/system
                    # If server idle, start immediately
                    if current_N == 0:
                        current_N = 1
                        next_departure = t + svc_time
                        # Store departure info implicitly via next_departure
                        # We don't need to store in queue if we manage next_departure directly
                        # But for multiple servers we'd need queue. Here c=1.
                        # Let's keep a simple flag or queue for clarity.
                        # Since c=1, queue holds people waiting.
                        # If current_N==0, person enters service.
                    else:
                        # Server busy, join queue
                        queue.append((t, svc_time))
                        current_N += 1
                        # next_departure remains unchanged
                else:
                    # Blocked
                    n_blocked += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                t = t_dep
                dt = t - last_event_time
                
                # Integrate stats before updating state
                if last_event_time >= warmup_end:
                    L_area += current_N * dt
                    if current_N > 0:
                        Busy_area += dt
                        Occupied_area += dt
                
                # Process departure
                n_departures += 1
                current_N -= 1
                
                if queue:
                    # Next person starts service
                    arr_t, svc_t = queue.popleft()
                    current_N += 1 # Still in system
                    next_departure = t + svc_t
                else:
                    next_departure = float('inf')
            
            last_event_time = t

        # Final integration step if needed? Loop ends when t >= H.
        # The last interval from last_event_time to H was not integrated because no event occurred at H.
        # We should integrate up to H.
        dt_final = H - last_event_time
        if last_event_time >= warmup_end:
            L_area += current_N * dt_final
            if current_N > 0:
                Busy_area += dt_final
                Occupied_area += dt_final
        
        # Calculate metrics for this seed
        win_len = H - warmup_end
        
        if win_len > 0:
            avg_L = L_area / win_len
            avg_busy_frac = Busy_area / win_len
            avg_busy_util = avg_busy_frac # For c=1
            avg_busy_occ = avg_busy_frac
            
            # W calculation: Little's Law L = lam_eff * W
            # lam_eff = (n_arrivals - n_blocked) / win_len ? 
            # No, n_arrivals counted over whole simulation? 
            # We need counts within the window too.
            # My counters n_arrivals etc were global. This is wrong for per-seed window stats.
            # Need to reset counters or track them per window.
            # Refactoring: Track events inside window.
            
            # Re-running logic mentally: 
            # I need to separate global simulation from window statistics.
            # Let's restart the loop logic with proper window tracking.
            pass 

    # Due to complexity of re-implementing correctly in one shot without bugs,
    # I will rewrite the inner loop carefully.

    results = {}
    
    # Reset lists
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_blk = []
    per_seed_dep = []
    per_seed_busy_util = []
    per_seed_busy_occ = []
    
    valid_seeds = 0
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        queue = deque()
        current_N = 0
        
        # Window stats
        L_area = 0.0
        Busy_area = 0.0
        
        # Counts in window
        w_arr = 0
        w_blk = 0
        w_dep = 0
        w_wait = 0
        
        last_event_time = 0.0
        warmup_end = 0.25 * H
        
        while t < H:
            t_arr = next_arrival
            t_dep = next_departure
            
            if t_arr <= t_dep:
                t = t_arr
                dt = t - last_event_time
                
                # Integrate
                if last_event_time >= warmup_end:
                    L_area += current_N * dt
                    if current_N > 0:
                        Busy_area += dt
                
                # Arrival processing
                if t >= warmup_end:
                    w_arr += 1
                
                if len(queue) + (1 if current_N > 0 else 0) < K:
                    svc_time = rng.expovariate(mu)
                    if t >= warmup_end and current_N > 0:
                        w_wait += 1
                        
                    if current_N == 0:
                        current_N = 1
                        next_departure = t + svc_time
                    else:
                        queue.append(svc_time) # Only need svc_time for next dep calc
                        current_N += 1
                else:
                    if t >= warmup_end:
                        w_blk += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                t = t_dep
                dt = t - last_event_time
                
                if last_event_time >= warmup_end:
                    L_area += current_N * dt
                    if current_N > 0:
                        Busy_area += dt
                
                if t >= warmup_end:
                    w_dep += 1
                
                current_N -= 1
                if queue:
                    svc_t = queue.popleft()
                    current_N += 1
                    next_departure = t + svc_t
                else:
                    next_departure = float('inf')
            
            last_event_time = t

        # Final integration
        dt_final = H - last_event_time
        if last_event_time >= warmup_end:
            L_area += current_N * dt_final
            if current_N > 0:
                Busy_area += dt_final
        
        win_len = H - warmup_end
        
        if win_len > 0 and w_arr > 0:
            # Effective arrival rate in window
            lam_eff = (w_arr - w_blk) / win_len
            
            # L
            est_L = L_area / win_len
            
            # W via Little's Law: L = lam_eff * W => W = L / lam_eff
            # Note: W is average time in system.
            if lam_eff > 0:
                est_W = est_L / lam_eff
            else:
                est_W = 0.0
            
            # busy_frac
            est_busy_frac = Busy_area / win_len
            
            # p_loss
            est_p_loss = w_blk / w_arr if w_arr > 0 else 0.0
            
            # p_wait: Fraction of accepted arrivals who waited?
            # Or fraction of all arrivals? Usually conditional on acceptance or overall?
            # Prompt: "p_wait". In MM1K, often P(W>0).
            # If we define p_wait as prob an arriving customer waits (including blocked?), 
            # blocked customers don't enter, so they don't wait in system.
            # Standard: P(wait | admitted) or P(wait)?
            # Let's use w_wait / (w_arr - w_blk) i.e., among those who entered.
            # Or w_wait / w_arr?
            # Given "busy_frac" is time-based, p_wait might be customer-based.
            # Let's calculate p_wait as proportion of admitted customers who waited.
            admitted = w_arr - w_blk
            est_p_wait = w_wait / admitted if admitted > 0 else 0.0
            
            # busy_util = E[min(N,c)]/c. For c=1, this is P(N>=1) = busy_frac.
            est_busy_util = est_busy_frac
            est_busy_occ = est_busy_frac
            
            per_seed_L.append(est_L)
            per_seed_W.append(est_W)
            per_seed_busy_frac.append(est_busy_frac)
            per_seed_p_loss.append(est_p_loss)
            per_seed_p_wait.append(est_p_wait)
            per_seed_arr.append(w_arr)
            per_seed_blk.append(w_blk)
            per_seed_dep.append(w_dep)
            per_seed_busy_util.append(est_busy_util)
            per_seed_busy_occ.append(est_busy_occ)
            
            valid_seeds += 1
            seed_list.append(seed)

    if valid_seeds == 0:
        # Fallback empty results
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":0,"seed_list":[],"seeds_used":0,"time_unit":"hour","win":0}))
        return

    # Aggregate averages
    avg_L = sum(per_seed_L) / valid_seeds
    avg_W = sum(per_seed_W) / valid_seeds
    avg_busy_frac = sum(per_seed_busy_frac) / valid_seeds
    avg_p_loss = sum(per_seed_p_loss) / valid_seeds
    avg_p_wait = sum(per_seed_p_wait) / valid_seeds
    avg_arr = sum(per_seed_arr) / valid_seeds
    avg_blk = sum(per_seed_blk) / valid_seeds
    avg_dep = sum(per_seed_dep) / valid_seeds
    avg_busy_util = sum(per_seed_busy_util) / valid_seeds
    avg_busy_occ = sum(per_seed_busy_occ) / valid_seeds
    
    # dep_rate: effective departure rate per hour
    # Total departures in window / total window time across seeds?
    # Or average of per-seed rates?
    # Per-seed rate = w_dep / win_len.
    # Average rate = sum(w_dep)/sum(win_len) = sum(w_dep)/(valid_seeds*win_len)
    total_win_time = valid_seeds * (H - 0.25*H)
    dep_rate = sum(per_seed_dep) / total_win_time if total_win_time > 0 else 0.0
    
    # lam_eff for output key? Not requested as top level, but used in W calc.
    # Output requires: L, W, busy_frac, p_loss, runtime_units, seed_list, seeds_used, time_unit, win
    # And suggested: arr, blk, busy_util, dep, dep_rate, lam_eff, p_wait, per_seed_*...
    
    # lam_eff aggregate: average effective arrival rate
    total_admitted = sum([a-b for a,b in zip(per_seed_arr, per_seed_blk)])
    lam_eff_avg = total_admitted / total_win_time if total_win_time > 0 else 0.0

    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": valid_seeds,
        "time_unit": time_unit,
        "win": round(H - 0.25*H, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff_avg, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
