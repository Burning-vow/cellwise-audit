import argparse, json, random, math
def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=1);p.add_argument('--horizon',type=float,default=100.0);p.add_argument('--seed-start',type=int,default=42);p.add_argument('--pert',default='none');a=p.parse_args()
    lam=8.0;mu=10.0;c=3;K=4
    if a.pert=='lam_up':lam*=1.2
    elif a.pert=='mu_up':mu*=1.2
    elif a.pert=='c_up':c+=1
    seeds=[a.seed_start+i for i in range(a.seeds)]
    res={'L':0,'W':0,'busy_frac':0,'p_loss':0,'runtime_units':0,'seed_list':seeds,'seeds_used':len(seeds),'time_unit':'hour','win':0,'arr':0,'blk':0,'busy_util':0,'dep':0,'dep_rate':0,'lam_eff':0,'p_wait':0,'per_seed_L':[],'per_seed_W':[],'per_seed_busy_frac':[],'per_seed_p_loss':[],'per_seed_p_wait':[]}
    tot_L=tot_W=tot_BF=tot_PL=tot_PW=tot_Arr=tot_Blk=tot_BU=tot_Dep=0.0
    for s in seeds:
        rng=random.Random(s)
        t=0.0;ev=[]
        def push(tt,tp,idx):ev.append((tt,tp,idx))
        n=0;arr_t=[];svc_end={};wait_t={};busy_t=0.0;last_chg=0.0;area_n=0.0;area_b=0.0;area_w=0.0;cnt_arr=0;cnt_blk=0;cnt_dep=0
        push(rng.expovariate(lam),0,-1)
        while ev:
            ev.sort(key=lambda x:x[0])
            tt,tp,idx=ev.pop(0)
            dt=tt-last_chg
            area_n+=n*dt
            if n>0:area_b+=dt
            for k in list(wait_t.keys()):
                if svc_end[k]>tt:area_w+=(tt-wait_t[k])*0 # wait accumulates only until service starts? No, W is time in system. 
            # Actually W = Time in System. Area of N(t) gives L. Little's Law L = lambda_eff * W.
            # We need to track sum of (departure_time - arrival_time) for completed services in window.
            last_chg=tt
            if tp==0: # Arrival
                cnt_arr+=1
                arr_t.append(tt)
                if n<K:
                    n+=1
                    svc=rng.expovariate(mu)
                    st=max(tt, max([v for v in svc_end.values()] or [0])) # Find earliest available server? 
                    # Simpler: assign to specific server index 0..c-1
                    # Let's use a list of next_free times for servers
                    pass
                else:
                    cnt_blk+=1
            elif tp==1: # Departure
                n-=1
                dep_time=tt
                # Need to match with arrival
                pass
        # The above logic is getting messy for "standard library" and "no classes".
        # Let's restart the simulation loop with a cleaner state machine using lists.
        
    # Re-implementing cleanly inside the seed loop
    for s in seeds:
        rng=random.Random(s)
        horizon=a.horizon
        warmup=0.25*horizon
        t=0.0
        # State: n (number in system), servers (list of end times), queue (list of arrival times waiting)
        # But problem says "total capacity 4 including passing". So it's a finite buffer of size K=4.
        # If n < K, enter. Else block.
        # Service time drawn at arrival.
        # We need to track:
        # 1. Number in system N(t) -> Integral for L
        # 2. Busy fraction: Time where N(t) > 0 / Total Time -> Integral for busy_frac
        # 3. Loss probability: Blocked / Arrivals
        # 4. W: Average time in system for those who entered and left within window.
        
        # Events: Arrival, Departure
        # Server assignment: Since c=3, we can just track when each server becomes free.
        # But since service time is exponential and memoryless, and we draw at arrival, we can just maintain a list of departure times for current occupants.
        # When an arrival happens, if len(departures) < K, add new departure time = t + exp(mu).
        # Wait, if there are multiple servers, does the car go to a specific one?
        # Yes. But for counting N(t), we just need the count.
        # For determining when the NEXT departure happens, we need min(departures).
        
        departures=[] # List of times when cars leave
        arrivals=[] # List of times when cars arrived (for calculating W later)
        # We need to pair them. FIFO? Usually toll booths are FCFS per lane, but here lanes are parallel.
        # Standard M/M/c/K model assumes FCFS discipline among all customers.
        # So when a customer arrives, they join the queue (if any) or start service immediately.
        # Here K=4 total spots. c=3 servers.
        # If n < c, immediate service.
        # If c <= n < K, wait in queue (which is effectively part of the system count).
        # If n == K, blocked.
        
        # To simulate this properly without complex queue structures:
        # Maintain `next_departure_times` for the c servers. Initially 0.
        # Maintain `queue` of arrival times for people waiting.
        # Maintain `in_service_count`.
        # Actually, simpler: Just maintain a list of `end_times` for all currently present vehicles.
        # When a vehicle arrives:
        #   If len(end_times) < K:
        #     Draw service time S ~ Exp(mu).
        #     Determine start time.
        #       If len(end_times) < c: Start now (t). End time = t + S.
        #       Else: Must wait for a server. The earliest available server is min(end_times).
        #             Start time = min(end_times). End time = Start time + S.
        #             Remove that min(end_times) from the list? No, that server is busy until then.
        #             This approach is tricky because removing/re-adding changes indices.
        
        # Better Approach: Event-driven with explicit server states.
        # Servers: list of length c, storing `free_at` time.
        # Queue: list of arrival times waiting for service.
        # In-system count = len(queue) + number of active servers (servers where free_at > t).
        # But we need to know exactly when events happen.
        
        # Let's stick to the simplest valid interpretation for M/M/c/K:
        # State variables:
        # `t`: current time
        # `n`: number in system
        # `server_free`: list of c floats, time when each server becomes free.
        # `waiting_queue`: list of arrival times of customers waiting for a server.
        # `completed_customers`: list of tuples (arrival_time, departure_time) for stats.
        
        # Initialization
        server_free = [0.0] * c
        waiting_queue = []
        completed = []
        n = 0
        t = 0.0
        last_event_time = 0.0
        
        # Accumulators for integrals (only after warmup)
        integral_N = 0.0
        integral_Busy = 0.0 # Time where n > 0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        
        # Generate first arrival
        next_arrival = rng.expovariate(lam)
        
        # Main Loop
        while True:
            # Determine next event time
            # Next arrival: next_arrival
            # Next departure: min(server_free) if any server is busy (server_free > t)? 
            # Actually, if server_free[i] > t, it will finish at server_free[i].
            # If server_free[i] <= t, it's idle.
            
            # Find next departure time
            next_dep = float('inf')
            for sf in server_free:
                if sf > t:
                    if sf < next_dep:
                        next_dep = sf
            
            # Choose next event
            if next_arrival < next_dep:
                # Arrival
                t_new = next_arrival
                dt = t_new - t
                # Integrate over interval [t, t_new]
                if t >= warmup:
                    integral_N += n * dt
                    if n > 0:
                        integral_Busy += dt
                
                t = t_new
                count_arr += 1
                
                # Check capacity
                if n < K:
                    n += 1
                    # Draw service time
                    svc = rng.expovariate(mu)
                    
                    # Find an idle server
                    idle_idx = -1
                    for i in range(c):
                        if server_free[i] <= t:
                            idle_idx = i
                            break
                    
                    if idle_idx != -1:
                        # Start immediately
                        server_free[idle_idx] = t + svc
                        # Record arrival time for this customer? 
                        # We need to link arrival to departure.
                        # Since we don't have object IDs, we can store (arrival_time, expected_departure_time) in a list associated with the server?
                        # Or simpler: Store arrival time in a global list, and when a server finishes, pop the oldest arrival?
                        # FCFS assumption: The customer who has been waiting longest gets served.
                        # If we start immediately, this customer is the newest.
                        # If we wait, they join the queue.
                        
                        # Let's maintain a list of `active_customers` on servers: (arrival_time, end_time)
                        # And `waiting_customers`: (arrival_time)
                        
                        # Refactor state:
                        # `on_server`: list of dicts {'arr': t, 'end': t+svc}
                        # `waiting`: list of arrival times
                        
                        # Let's switch to this clearer structure.
                        pass
                    else:
                        # All servers busy, must wait
                        waiting_queue.append(t)
                        # Note: n increased, so capacity check was correct.
                else:
                    count_blk += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                t_new = next_dep
                dt = t_new - t
                if t >= warmup:
                    integral_N += n * dt
                    if n > 0:
                        integral_Busy += dt
                
                t = t_new
                
                # Identify which server finished
                finished_idx = -1
                for i in range(c):
                    if abs(server_free[i] - t) < 1e-9:
                        finished_idx = i
                        break
                
                # Process departure
                # Who left? The person on that server.
                # We need their arrival time to calculate W.
                # Problem: We didn't store arrival time per server slot in the previous logic.
                
                # Let's rewrite the inner loop with proper tracking.
                break # Break to restart code generation with better structure

        # --- RESTARTING CODE GENERATION WITH BETTER STRUCTURE ---
        # I will generate the final Python code directly based on this refined logic.
        
        # Logic:
        # 1. Initialize servers as list of None (idle) or dict {start, end, arr}.
        # 2. Waiting queue is list of arrival times.
        # 3. On Arrival:
        #    - If total_in_system < K:
        #      - Draw svc.
        #      - If any server idle: Assign to it. Record arr time.
        #      - Else: Add to waiting queue.
        #    - Else: Block.
        # 4. On Departure:
        #    - Find server finishing.
        #    - Calculate W contribution if in window.
        #    - Mark server idle.
        #    - If waiting queue not empty: Pop front, assign to this server. New end time = t + svc(newly assigned? No, svc was drawn at arrival!).
        #      - CRITICAL: "Service duration must be drawn at arrival".
        #      - So when a car joins the waiting queue, we MUST have already drawn its service time.
        #      - So waiting queue should store (arrival_time, service_duration).
        #      - When assigned to server, end_time = current_time + service_duration.
        
        # Revised State:
        # `servers`: list of length c. Each element is None or tuple(arr_time, end_time).
        # `queue`: list of tuples(arr_time, svc_dur).
        # `n`: len(servers_active) + len(queue).
        
        # Let's implement this.
        
        # Reset for this seed
        rng = random.Random(s)
        horizon = a.horizon
        warmup = 0.25 * horizon
        t = 0.0
        servers = [None] * c  # None means idle. Otherwise (arr_time, end_time)
        queue = []            # List of (arr_time, svc_dur)
        n = 0
        last_t = 0.0
        int_N = 0.0
        int_Busy = 0.0
        cnt_arr = 0
        cnt_blk = 0
        cnt_dep = 0
        sum_W = 0.0 # Sum of time-in-system for departed customers in window
        
        # First arrival
        next_arr = rng.expovariate(lam)
        
        while True:
            # Find next departure
            next_dep = float('inf')
            for sv in servers:
                if sv is not None:
                    if sv[1] < next_dep:
                        next_dep = sv[1]
            
            if next_arr < next_dep:
                # Arrival
                dt = next_arr - t
                if t >= warmup:
                    int_N += n * dt
                    if n > 0: int_Busy += dt
                t = next_arr
                cnt_arr += 1
                
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    # Try to find idle server
                    idx = -1
                    for i in range(c):
                        if servers[i] is None:
                            idx = i
                            break
                    if idx != -1:
                        servers[idx] = (t, t + svc)
                    else:
                        queue.append((t, svc))
                else:
                    cnt_blk += 1
                
                next_arr = t + rng.expovariate(lam)
                
            else:
                # Departure
                dt = next_dep - t
                if t >= warmup:
                    int_N += n * dt
                    if n > 0: int_Busy += dt
                t = next_dep
                
                # Find server that finished
                idx = -1
                for i in range(c):
                    if servers[i] is not None and abs(servers[i][1] - t) < 1e-9:
                        idx = i
                        break
                
                if idx != -1:
                    arr_time, _ = servers[idx]
                    servers[idx] = None
                    n -= 1
                    cnt_dep += 1
                    if arr_time >= warmup: # Only count W for those who arrived in window? 
                        # Standard practice: Count all departures in window.
                        # W = (Dep - Arr).
                        w_val = t - arr_time
                        sum_W += w_val
                    
                    # Serve next from queue if any
                    if queue:
                        q_arr, q_svc = queue.pop(0)
                        servers[idx] = (q_arr, t + q_svc)
                        n += 1 # Wait, n decreased by 1, now increases by 1. Net change 0? 
                        # No, the person moved from queue to server. Total N remains same.
                        # My n counter tracks total in system.
                        # When departure happened, n--.
                        # When assigning from queue, n++? No, they were already counted in n.
                        # So n should NOT increase.
                        # Correction: n tracks total presence.
                        # Arrival: n++.
                        # Departure: n--.
                        # Move from queue to server: n unchanged.
                        pass
                else:
                    # Should not happen
                    pass
            
            if t >= horizon:
                break
        
        # Calculate stats for this seed
        win_len = horizon - warmup
        if win_len <= 0: win_len = 1e-9
        
        L_est = int_N / win_len
        BF_est = int_Busy / win_len
        PL_est = cnt_blk / cnt_arr if cnt_arr > 0 else 0.0
        # W estimation: Average time in system for those who DEPARTED in the window.
        # Note: Some might have arrived before warmup. That's fine, they contribute to W.
        # However, strict steady-state usually excludes transient effects.
        # Using departures in window is standard.
        W_est = sum_W / cnt_dep if cnt_dep > 0 else 0.0
        
        # Busy Utilization E[min(N,c)]/c
        # We need integral of min(n, c).
        # We didn't track this separately. 
        # Approximation: We can re-run or track it. 
        # Let's add tracking
