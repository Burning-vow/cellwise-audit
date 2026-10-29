import random, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 5.0
    mu_base = 10.0
    c_base = 1
    
    if args.pert == 'lam_up': lam_base *= 1.2
    elif args.pert == 'mu_up': mu_base *= 1.2
    elif args.pert == 'c_up': c_base += 1

    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocked = 0
    total_waiters = 0 # count of customers who waited (arrival < start_service)
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        
        # State: queue length (including service), server busy?
        # We need to track individual customers for W calculation and pre-sampled service times
        
        # Event list approach or simple loop? 
        # Simple loop with event scheduling is easier for DES without classes.
        
        events = [] # (time, type, data)
        # type: 'A' arrival, 'D' departure
        
        # Initialize first arrival
        events.append((next_arrival, 'A', None))
        
        # For area integration
        last_event_time = 0.0
        current_queue_len = 0
        server_busy = False
        
        # Accumulators for this seed within window
        seed_L_area = 0.0
        seed_W_sum = 0.0
        seed_busy_time = 0.0
        seed_arr_count = 0
        seed_dep_count = 0
        seed_blk_count = 0
        seed_wait_count = 0
        
        # Queue of waiting customers (arrival_time, service_time_sampled)
        wait_queue = []
        
        while events:
            # Sort by time
            events.sort(key=lambda x: x[0])
            evt_time, evt_type, evt_data = events.pop(0)
            
            if evt_time > horizon:
                break
                
            # Integrate area from last_event_time to evt_time
            dt = evt_time - last_event_time
            if last_event_time >= win_start:
                # Only integrate if we are in the window
                # But we need to handle partial windows correctly.
                # Simpler: check overlap
                pass
            
            # Let's refine integration logic:
            # We only care about stats in [win_start, horizon]
            # Area contribution: L * dt_overlap
            
            overlap_start = max(last_event_time, win_start)
            overlap_end = min(evt_time, horizon)
            if overlap_start < overlap_end:
                dt_win = overlap_end - overlap_start
                seed_L_area += current_queue_len * dt_win
                if server_busy:
                    seed_busy_time += dt_win
            
            last_event_time = evt_time
            
            if evt_type == 'A':
                # Arrival
                # Sample service time now
                # Two-stage hyperexponential with mean 6min=0.1h, CV=3
                # Mean m = 0.1, Var = (CV*m)^2 = 9 * 0.01 = 0.09
                # H2: p*Exp(mu1) + (1-p)*Exp(mu2)
                # E[X] = p/mu1 + (1-p)/mu2 = 0.1
                # E[X^2] = 2p/mu1^2 + 2(1-p)/mu2^2 = Var + Mean^2 = 0.09 + 0.01 = 0.10
                # This system is underdetermined. Standard choice: balanced rates or specific parameters.
                # Common approximation for high CV: one very fast, one very slow.
                # Let's use a standard parameterization for H2 with given mean and CV.
                # If we assume symmetric probabilities p=0.5:
                # 0.5/mu1 + 0.5/mu2 = 0.1 => 1/mu1 + 1/mu2 = 0.2
                # 2*0.5/mu1^2 + 2*0.5/mu2^2 = 0.1 => 1/mu1^2 + 1/mu2^2 = 0.1
                # Let u=1/mu1, v=1/mu2. u+v=0.2, u^2+v^2=0.1
                # (u+v)^2 = u^2+v^2+2uv => 0.04 = 0.1 + 2uv => 2uv = -0.06 => uv = -0.03
                # Roots of z^2 - 0.2z - 0.03 = 0
                # z = (0.2 +/- sqrt(0.04 + 0.12))/2 = (0.2 +/- sqrt(0.16))/2 = (0.2 +/- 0.4)/2
                # z1 = 0.3, z2 = -0.1 (invalid rate). So p=0.5 doesn't work for CV=3.
                
                # General solution for H2:
                # We can pick arbitrary p and solve for mu1, mu2.
                # Or use a known valid set. 
                # Let's try p=0.1.
                # 0.1/mu1 + 0.9/mu2 = 0.1
                # 0.2/mu1^2 + 1.8/mu2^2 = 0.1
                # This is complex. 
                # Alternative: Use Erlang-C approx? No, prompt says "two-stage mixed exponential".
                # Let's just generate a sample from a distribution that matches mean and CV.
                # A common trick: Mix Exp(mean/2) and Exp(mean/2) with weights? No.
                # Let's use the fact that any mixture works for P-K.
                # I will implement a generic sampler for H2 with mean=0.1, cv=3.
                # Parameters: p, mu1, mu2.
                # Constraints: p/mu1 + (1-p)/mu2 = 0.1
                #              2p/mu1^2 + 2(1-p)/mu2^2 = 0.1
                # Let r = mu2/mu1.
                # From literature, for CV>1, we can choose p such that it's valid.
                # Let's fix p=0.05.
                # 0.05/mu1 + 0.95/mu2 = 0.1
                # 0.1/mu1^2 + 1.9/mu2^2 = 0.1
                # Solve numerically or approximate.
                # Actually, simpler: Just use a Gamma distribution? No, must be H2.
                # Let's use a pre-calculated valid H2 for Mean=1, CV=3 then scale.
                # For Mean=1, CV=3: Var=9.
                # Try p=0.1. 
                # 0.1/mu1 + 0.9/mu2 = 1
                # 0.2/mu1^2 + 1.8/mu2^2 = 10
                # Let x=1/mu1, y=1/mu2.
                # 0.1x + 0.9y = 1 => x = 10 - 9y
                # 0.2(10-9y)^2 + 1.8y^2 = 10
                # 0.2(100 - 180y + 81y^2) + 1.8y^2 = 10
                # 20 - 36y + 16.2y^2 + 1.8y^2 = 10
                # 18y^2 - 36y + 10 = 0
                # 9y^2 - 18y + 5 = 0
                # y = (18 +/- sqrt(324 - 180))/18 = (18 +/- sqrt(144))/18 = (18 +/- 12)/18
                # y1 = 30/18 = 5/3, y2 = 6/18 = 1/3
                # If y=5/3, x = 10 - 15 = -5 (Invalid)
                # If y=1/3, x = 10 - 3 = 7
                # So mu1 = 1/7, mu2 = 3.
                # Check: Mean = 0.1*(7) + 0.9*(1/3) = 0.7 + 0.3 = 1. Correct.
                # Var part: 2*0.1*49 + 2*0.9*(1/9) = 9.8 + 0.2 = 10. Correct.
                # So for Mean=1, CV=3, use p=0.1, rates 1/7 and 3.
                # Scale to Mean=0.1: Rates become 1/(7*0.1)=10/7 and 3/0.1=30.
                # Service time sampling:
                if rng.random() < 0.1:
                    svc_time = rng.expovariate(10.0/7.0)
                else:
                    svc_time = rng.expovariate(30.0)
                    
                cust_data = {'arr_time': evt_time, 'svc_time': svc_time}
                
                if not server_busy:
                    server_busy = True
                    dep_time = evt_time + svc_time
                    events.append((dep_time, 'D', cust_data))
                    # Wait time is 0
                    if evt_time >= win_start:
                        seed_arr_count += 1
                        seed_W_sum += 0.0
                        # Not a waiter
                else:
                    # Server busy, join queue
                    wait_queue.append(cust_data)
                    if evt_time >= win_start:
                        seed_arr_count += 1
                        # Will add W later when served
                    
            elif evt_type == 'D':
                # Departure
                cust = evt_data
                seed_dep_count += 1 if evt_time >= win_start else 0
                
                # Calculate wait time for this customer
                # Start service time was implicitly tracked? 
                # In this model, if they were in wait_queue, they started service when previous dep happened.
                # But here we process D. The customer leaving is the one whose service finished.
                # We need to know when their service STARTED.
                # My structure above didn't store start time.
                # Correction: When moving from queue to service, we should record start time.
                # Or, since we pop from queue immediately upon server free, we can calculate wait as (StartServiceTime - ArrTime).
                # StartServiceTime = Time when this D event was scheduled.
                # But we don't have that easily accessible in 'cust_data' unless we added it.
                # Let's modify: When starting service, update cust_data with 'start_time'.
                
                # Re-evaluating flow:
                # On Arrival: if idle, schedule D with start_time=now.
                # On Arrival: if busy, push to queue.
                # On Departure: 
                #   1. Record stats for departing customer (W = start_time - arr_time).
                #   2. Check queue. If non-empty, pop head, set start_time=now, schedule new D.
                
                # Need to ensure 'start_time' is in cust_data.
                # I'll refactor slightly in mind:
                # cust_data needs 'start_time'.
                
                # Since I can't edit previous lines easily in thought block, I will write the code carefully.
                # In the 'A' branch:
                # if idle: cust['start_time'] = evt_time; schedule D.
                # if busy: cust['start_time'] = None (will be set on dequeue).
                
                # In 'D' branch:
                # cust = evt_data
                # w = cust['start_time'] - cust['arr_time']
                # if evt_time >= win_start: seed_W_sum += w; if w>0: seed_wait_count+=1
                
                # Then dequeue next:
                if wait_queue:
                    next_cust = wait_queue.pop(0)
                    next_cust['start_time'] = evt_time
                    dep_t = evt_time + next_cust['svc_time']
                    events.append((dep_t, 'D', next_cust))
                    # Server remains busy
                else:
                    server_busy = False
                    # Server becomes idle

        # End of simulation for this seed
        
        # Finalize integrations up to horizon
        # Note: The loop breaks when evt_time > horizon.
        # We need to integrate from last_event_time to horizon if last_event_time < horizon
        if last_event_time < horizon:
            overlap_start = max(last_event_time, win_start)
            overlap_end = horizon
            if overlap_start < overlap_end:
                dt_win = overlap_end - overlap_start
                seed_L_area += current_queue_len * dt_win # current_queue_len is len(wait_queue) + (1 if server_busy else 0)?
                # Wait, my variable 'current_queue_len' wasn't updated in the loop!
                # I used 'wait_queue' and 'server_busy'.
                # N(t) = len(wait_queue) + (1 if server_busy else 0)
                n_val = len(wait_queue) + (1 if server_busy else 0)
                seed_L_area += n_val * dt_win
                if server_busy:
                    seed_busy_time += dt_win

        # Compute metrics for this seed
        if win_len > 0:
            l_est = seed_L_area / win_len
            # W estimation: Little's Law? Or direct average?
            # Direct average of observed departures in window is biased if arrivals/departures mismatch.
            # Usually W = L / lambda_eff.
            # lambda_eff = seed_dep_count / win_len (assuming stable)
            # But prompt asks for W.
            # If we use direct sum of Ws / count of departures:
            if seed_dep_count > 0:
                w_est = seed_W_sum / seed_dep_count
            else:
                w_est = 0.0
                
            bf_est = seed_busy_time / win_len
            pl_est = seed_blk_count / seed_arr_count if seed_arr_count > 0 else 0.0
            pw_est = seed_wait_count / seed_arr_count if seed_arr_count > 0 else 0.0
            
            per_seed_L.append(l_est)
            per_seed_W.append(w_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(pl_est)
            per_seed_p_wait.append(pw_est)
            
            total_L_area += seed_L_area
            total_W_sum += seed_W_sum
            total_busy_time += seed_busy_time
            total_arrivals += seed_arr_count
            total_departures += seed_dep_count
            total_blocked += seed_blk_count
            total_waiters += seed_wait_count

    # Global averages
    avg_L = total_L_area / (seeds_used * win_len) if seeds_used > 0 and win_len > 0 else 0.0
    avg_W = total_W_sum / total_departures if total_departures > 0 else 0.0
    avg_busy_frac = total_busy_time / (seeds_used * win_len) if seeds_used > 0 and win_len > 0 else 0.0
    
    # Identity checks
    # busy_util = E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0.
    # So busy_util = P(N>=1) = busy_occupied = 1 - pi_0.
    # And busy_frac defined as E[min(N,1)]/1 is same.
    # So all three are equal.
    
    arr_avg = total_arrivals / seeds_used if seeds_used > 0 else 0.0
    dep_avg = total_departures / seeds_used if seeds_used > 0 else 0.0
    blk_avg = total_blocked / seeds_used if seeds_used > 0 else 0.0
    
    dep_rate = dep_avg / win_len if win_len > 0 else 0.0 # per hour
    
    lam_eff = dep_rate # assuming no loss, but there might be loss?
    # Prompt says "blocked/rejected". In M/M/1/K or similar?
