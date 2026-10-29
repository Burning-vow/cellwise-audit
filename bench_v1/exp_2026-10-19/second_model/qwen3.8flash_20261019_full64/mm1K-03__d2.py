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
    elif pert == 'c_up': pass # c is fixed by problem statement structure usually, but "pert only changes params". If c_up meant changing capacity? Problem says "only 1 doctor", "capacity 4". Usually perturbations are on rates. Let's assume c_up does nothing or maybe increases capacity? The prompt says "pert NAME... none/lam_up/mu_up/c_up". In MM1K context, c is servers. But here c=1 fixed. Maybe c_up means increasing capacity K? Or maybe it's a distractor. Given "MM1K-03", K is buffer size. Let's assume c_up increases K to 5? Or maybe it's just not applicable. I will treat c_up as no change for safety unless standard convention implies otherwise. Actually, looking at typical DES tasks, c_up might mean increasing the number of servers, but the problem says "only 1 doctor". So c_up likely refers to Capacity K. Let's increase K to 5 for c_up.
    if pert == 'c_up': K += 1
    
    lam = lam_base
    mu = mu_base
    
    time_unit = 'hour'
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_blk = []
    per_seed_dep = []
    
    seed_list = []
    
    total_L_area = 0.0
    total_time_window = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_blocks = 0
    total_departures = 0
    total_wait_time_sum = 0.0 # Sum of waiting times for all served customers in window
    
    warmup_ratio = 0.25
    warmup_end = H * (1 - warmup_ratio)
    window_len = H - warmup_end
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        n_in_system = 0 # Includes those in service and queue
        busy = False
        
        # Accumulators for this seed (raw, before filtering)
        # We need to integrate L over time and count events in the window [warmup_end, H]
        
        # To handle area integration correctly with discrete events:
        # We track last_event_time and current_n.
        # Area += current_n * (t_current - t_last)
        
        t_last = 0.0
        curr_n = 0
        
        # For W calculation: we need sum of (departure_time - arrival_time) for customers 
        # who ARRIVED in the window? Or DEPARTED in the window?
        # Standard definition: W is average time spent in system.
        # Usually, we accumulate wait times for customers that complete service within the window.
        # However, Little's Law L = lambda_eff * W holds for steady state.
        # Let's use the area method for L and event-based for W.
        # For W, we sum (t_dep - t_arr) for each customer whose departure occurs in the window.
        # Note: Customers arriving before window but departing inside contribute their full sojourn time?
        # Or do we truncate? Usually, we take customers who depart in the window.
        # Let's stick to: Sum of sojourn times for customers departing in [warmup_end, H].
        # And Count of such customers.
        
        seed_L_area = 0.0
        seed_busy_time = 0.0
        seed_arr_count = 0
        seed_blk_count = 0
        seed_dep_count = 0
        seed_sojourn_sum = 0.0
        
        # Queue to store arrival times of patients currently in system
        # Since FIFO, we can just store arrival times.
        # When someone departs, pop from front.
        # But we need to know if they arrived in the window? No, W is property of the patient.
        # If we count patients departing in window, we add their full sojourn time.
        
        arrivals_queue = [] # List of arrival times
        
        while t < H:
            # Determine next event time
            t_next = min(next_arrival, next_departure)
            
            if t_next > H:
                t_next = H
            
            dt = t_next - t_last
            
            # Integrate L and Busy Time
            if t_last >= warmup_end:
                seed_L_area += curr_n * dt
                if curr_n > 0:
                    seed_busy_time += dt
            
            # Update global accumulators if we were doing so, but we'll aggregate later
            
            t = t_next
            t_last = t
            
            if t >= H:
                break
                
            # Process Event
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                if curr_n < K:
                    # Accept
                    curr_n += 1
                    arrivals_queue.append(t)
                    seed_arr_count += 1
                    
                    # If server was idle, start service immediately
                    if not busy:
                        busy = True
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                else:
                    # Block
                    seed_blk_count += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - next_departure) < 1e-9:
                # Departure
                if curr_n > 0:
                    # Pop first arrival
                    arr_t = arrivals_queue.pop(0)
                    sojourn = t - arr_t
                    
                    # Check if this departure is in the window
                    if t >= warmup_end:
                        seed_dep_count += 1
                        seed_sojourn_sum += sojourn
                        
                    curr_n -= 1
                    
                    if curr_n > 0:
                        # Start next service
                        service_time = rng.expovariate(mu)
                        next_departure = t + service_time
                    else:
                        busy = False
                        next_departure = float('inf')
                else:
                    # Should not happen if logic correct
                    next_departure = float('inf')
                    
        # End of simulation for this seed
        
        # Calculate metrics for this seed based on window
        # L = Average number in system during window
        if window_len > 0:
            l_val = seed_L_area / window_len
        else:
            l_val = 0.0
            
        # W = Average sojourn time for customers departing in window
        if seed_dep_count > 0:
            w_val = seed_sojourn_sum / seed_dep_count
        else:
            w_val = 0.0
            
        # Convert W to minutes
        w_val_min = w_val * 60.0
        
        # Busy Fraction = Proportion of time system is non-empty (N>0)
        # Note: Prompt defines busy_frac as 1-pi_0, which is P(N>0).
        # This is exactly seed_busy_time / window_len.
        bf_val = seed_busy_time / window_len if window_len > 0 else 0.0
        
        # Loss Probability
        pl_val = seed_blk_count / seed_arr_count if seed_arr_count > 0 else 0.0
        
        # Wait Probability (P(Wait > 0))
        # Approximation: Fraction of accepted customers who had to wait.
        # A customer waits if upon arrival, there was already someone in service (or queue).
        # i.e., if arrival found N >= 1.
        # We didn't track this explicitly. 
        # Alternative: P_wait = 1 - P(Arrival finds empty).
        # Or calculate from data: We know total arrivals accepted.
        # How many found N=0? Those that started service immediately.
        # We can infer: Number of immediate starts = Number of times an arrival occurred when busy=False.
        # Let's re-run loop logic mentally or add counter.
        # Better: Add counter `immediate_starts` in the loop.
        
        # Re-calculating P_wait requires tracking how many arrivals found the system empty.
        # Let's modify the loop slightly in thought process, but since I must output code now, 
        # I will implement the counter in the actual code block below.
        
        # For now, placeholder logic in code will include `seed_immediate_starts`.
        # P_wait = 1 - (immediate_starts / accepted_arrivals) ? 
        # No, P_wait is probability that a customer has to wait.
        # Customer waits if N >= 1 upon arrival.
        # So P_wait = (Accepted Arrivals - Immediate Starts) / Accepted Arrivals.
        
        # Let's ensure the code includes this.
        
        per_seed_L.append(l_val)
        per_seed_W.append(w_val_min)
        per_seed_busy_frac.append(bf_val)
        per_seed_p_loss.append(pl_val)
        # Will compute p_wait properly in code
        per_seed_p_wait.append(0.0) 
        per_seed_arr.append(seed_arr_count)
        per_seed_blk.append(seed_blk_count)
        per_seed_dep.append(seed_dep_count)
        
        # Accumulate for global stats
        total_L_area += seed_L_area
        total_busy_time += seed_busy_time
        total_arrivals += seed_arr_count
        total_blocks += seed_blk_count
        total_departures += seed_dep_count
        # Need total_sojourn_sum for global W? 
        # Global W should be weighted average or simple average of seeds?
        # Usually "W" reported is the overall estimate. 
        # If we pool all seeds, W_total = Total_Sojourn_Sum / Total_Departures.
        # Let's keep a global sum.
        # I'll add `total_sojourn_sum` variable.

# Refining the code structure to include missing counters and global sums

if __name__ == "__main__":
    # Re-implementing main cleanly with all required fields
    
    import sys, json, random, argparse

    def run_sim():
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
        
        lam_base = 8.0
        mu_base = 10.0 
        c = 1
        K = 4 
        
        if pert == 'lam_up': lam_base *= 1.1
        elif pert == 'mu_up': mu_base *= 1.1
        elif pert == 'c_up': K += 1
        
        lam = lam_base
        mu = mu_base
        time_unit = 'hour'
        
        warmup_ratio = 0.25
        warmup_end = H * (1 - warmup_ratio)
        window_len = H - warmup_end
        
        per_seed_L = []
        per_seed_W = []
        per_seed_busy_frac = []
        per_seed_p_loss = []
        per_seed_p_wait = []
        per_seed_arr = []
        per_seed_blk = []
        per_seed_dep = []
        seed_list = []
        
        # Global accumulators for pooled estimates
        g_L_area = 0.0
        g_busy_time = 0.0
        g_arr = 0
        g_blk = 0
        g_dep = 0
        g_sojourn_sum = 0.0
        g_immediate_starts = 0 # For P_wait
        
        for i in range(N_seeds):
            seed = S_start + i
            seed_list.append(seed)
            rng = random.Random(seed)
            
            t = 0.0
            next_arrival = rng.expovariate(lam)
            next_departure = float('inf')
            
            n_in_system = 0
            busy = False
            t_last = 0.0
            curr_n = 0
            arrivals_queue = []
            
            s_L_area = 0.0
            s_busy_time = 0.0
            s_arr = 0
            s_blk = 0
            s_dep = 0
            s_sojourn_sum = 0.0
            s_immediate = 0
            
            while t < H:
                t_next = min(next_arrival, next_departure)
                if t_next > H: t_next = H
                
                dt = t_next - t_last
                
                if t_last >= warmup_end:
                    s_L_area += curr_n * dt
                    if curr_n > 0:
                        s_busy_time += dt
                
                t = t_next
                t_last = t
                
                if t >= H: break
                
                if abs(t - next_arrival) < 1e-9:
                    if curr_n < K:
                        curr_n += 1
                        arrivals_queue.append(t)
                        s_arr += 1
                        if not busy:
                            busy = True
                            s_immediate += 1
                            service_time = rng.expovariate(mu)
                            next_departure = t + service_time
                    else:
                        s_blk += 1
                    next_arrival = t + rng.expovariate(lam)
                    
                elif abs(t - next_departure) < 1e-9:
                    if curr_n > 0:
                        arr_t = arrivals_queue.pop(0)
                        sojourn = t - arr_t
                        if t >= warmup_end:
                            s_dep += 1
                            s_sojourn_sum += sojourn
                        curr_n -= 1
                        if curr_n > 0:
                            service_time = rng.expovariate(mu)
                            next_departure = t + service_time
                        else:
                            busy = False
                            next_departure = float('inf')
                    else:
                        next_departure = float('inf')
            
            # Per-seed metrics
            l_val = s_L_area / window_len if window_len > 0 else 0.0
            w_val_hr = s_sojourn_sum / s_dep if s_dep > 0 else 0.0
            w_val_min = w_val_hr * 60.0
            bf_val = s_busy_time / window_len if window_len > 0 else 0.0
            pl_val = s_blk / s_arr if s_arr > 0 else 0.0
            pw_val = (s_arr - s_immediate) / s_arr if s_arr > 0 else 0.0
            
            per_seed_L.append(l_val)
            per_seed_W.append(w_val_min)
            per_seed_busy_frac.append(bf_val)
            per_seed_p_loss.append(pl_val)
            per_seed_p_wait.append(pw_val)
            per_seed_arr.append(s_arr)
            per_seed_blk.append(s_blk)
            per_seed_dep.append(s_dep)
            
            g_L_area += s_L_area
            g_busy_time += s_busy_time
            g_arr += s_arr
            g_blk += s_blk
            g_dep += s_dep
            g_sojourn_sum += s_sojourn_sum
            g_immediate_starts += s_immediate
            
        # Global Metrics (Pooled)
        # L: Average over time and seeds? 
        # Usually L is E[N]. Estimate = Total Area / (Window * NumSeeds)? 
        # Or Average of per_seed_L? 
        # The prompt asks for "L". In DES, often the grand mean of the per-seed estimates is used, 
        # or the pooled estimator. Pooled estimator for L is (Sum of Areas) / (Num Seeds * Window).
        # Which is same as Mean(per_seed_L).
        
        avg_L = g_L_area / (N_seeds * window_len) if window_len > 0 else 0.0
        
        # W: Pooled average sojourn time
        avg_W_hr = g_sojourn_sum / g_dep if g_dep > 0 else 0.0
        avg_W_min = avg_W_hr * 60.0
        
        # Busy Frac: Pooled
        avg_bf = g_busy_time / (N_seeds * window_len) if window_len > 0 else 0.0
        
        # Loss Prob: Pooled
        avg_pl = g_blk / g_arr if g_arr > 0 else 0.0
        
        # Wait Prob: Pooled
        avg_pw = (g_arr - g_immediate_starts) / g_arr if g_arr > 0 else 0.0
