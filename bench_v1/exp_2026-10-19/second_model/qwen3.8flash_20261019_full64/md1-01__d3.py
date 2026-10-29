import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 4.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0    # per minute (service rate)
    c = 1
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.5
    elif a.pert == 'mu_up':
        mu = mu_base * 1.5
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = a.horizon * 60.0 if a.time_unit == 'hour' else a.horizon
    time_unit = 'minute'
    horizon = a.horizon * 60.0 if a.pert != 'none' and False else a.horizon
    # Re-evaluate based on prompt: H is in same unit as time_unit. Let's assume minute for internal consistency with W in minutes.
    # But prompt says "H ... unit with self-reported time_unit". If I report minute, H is minutes.
    # Default H=100 might be too short if it's minutes? No, let's stick to standard DES practice. 
    # Actually, the prompt implies I choose time_unit. Let's choose 'minute'.
    # So horizon is just a.horizon if time_unit is minute.
    
    time_unit = 'minute'
    horizon = float(a.horizon)
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_win = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        random.seed(seed)
        seeds_used.append(seed)
        
        t = 0.0
        next_arr = random.expovariate(lam)
        next_dep = float('inf')
        
        queue = [] # list of arrival times
        service_times = [] # pre-drawn service durations for customers in system (waiting or serving)
        # Since M/M/1/1 (c=1), no waiting allowed? "先到先洗" usually implies queue. 
        # But "自动洗车机每次洗车固定 6 分钟... 平均每小时 4 辆". 
        # If it's a single server with infinite capacity, it's M/D/1.
        # If it's loss system, it's M/D/1/1.
        # "场内平均车辆数 L" suggests there can be more than 1 car inside (waiting).
        # So it's M/D/1 with FCFS.
        
        # State:
        # busy: bool
        # current_service_end_time: float
        # queue: list of (arrival_time, service_duration)
        
        busy = False
        curr_serv_end = -1.0
        q = [] # list of (arr_t, serv_dur)
        
        # Statistics accumulators (for area integration)
        # We need to integrate N(t) over time window [warmup, horizon]
        warmup = 0.25 * horizon
        start_stat = warmup
        
        # To do area integration correctly, we track events.
        # Events: Arrival, Departure.
        # Between events, N is constant.
        
        n_count_integral = 0.0
        wait_time_sum = 0.0 # sum of (dep - arr) for completed services in window? 
        # W is average stay time. Usually calculated as Total Stay Time / Number of Customers Completed.
        # Or via Little's Law L = lambda_eff * W.
        # The prompt asks for W directly. Standard estimator: Sum of sojourn times of customers who departed in window / count of such departures.
        # However, "area-type quantities must be integrated before state change". This refers to L (time-average number).
        # For W, it's often customer-average.
        
        # Let's use the standard approach:
        # L = (1/T_window) * integral(N(t) dt)
        # W = (Sum of sojourn times of customers departing in window) / (Number of customers departing in window)
        # Note: Customers arriving before warmup but departing after are included in departure stats?
        # Usually, we discard data from first 25% of simulation time.
        # So we only count departures that happen AFTER warmup.
        # And we only integrate N(t) AFTER warmup.
        
        last_event_time = 0.0
        current_n = 0
        
        # Initialize first event
        # We need to simulate until horizon.
        
        # Pre-generate arrivals? No, Poisson process is memoryless, generate on fly.
        # But service time is fixed 6 min.
        
        # Event loop
        while t < horizon:
            # Determine next event time
            next_arr_t = next_arr
            next_dep_t = curr_serv_end if busy else float('inf')
            
            next_t = min(next_arr_t, next_dep_t)
            
            if next_t > horizon:
                break
                
            # Integrate N(t) from last_event_time to next_t, but only if interval overlaps with stat window
            # Stat window is [start_stat, horizon]
            int_start = max(last_event_time, start_stat)
            int_end = min(next_t, horizon)
            
            if int_start < int_end:
                duration = int_end - int_start
                n_count_integral += current_n * duration
            
            # Process event at next_t
            t = next_t
            
            if abs(t - next_arr_t) < 1e-9:
                # Arrival
                # Check if server is free
                if not busy:
                    # Start service immediately
                    busy = True
                    serv_dur = 6.0
                    curr_serv_end = t + serv_dur
                    # Customer enters system, stays until dep
                    # Record arrival time for this customer to calculate sojourn later
                    # Since we don't have a queue, this customer is the one being served.
                    # We need to store their arrival time to compute W when they leave.
                    # Let's keep a variable `current_cust_arr`
                    current_cust_arr = t
                    current_n += 1
                else:
                    # Server busy, join queue
                    serv_dur = 6.0
                    q.append((t, serv_dur))
                    current_n += 1
                
                # Generate next arrival
                next_arr = t + random.expovariate(lam)
                
            elif abs(t - next_dep_t) < 1e-9:
                # Departure
                # Calculate sojourn time for the departing customer
                # Who is departing? The one currently being served.
                # Its arrival time was stored in `current_cust_arr`
                sojourn = t - current_cust_arr
                
                # Only record statistics if departure happens within stat window
                if t >= start_stat:
                    wait_time_sum += sojourn
                    dep_count_in_window += 1 # Need to initialize this
                
                # Remove departing customer from system
                current_n -= 1
                
                # Next customer from queue?
                if q:
                    next_cust_arr, next_cust_serv = q.pop(0)
                    busy = True
                    curr_serv_end = t + next_cust_serv
                    current_cust_arr = next_cust_arr
                else:
                    busy = False
                    curr_serv_end = float('inf')
                    current_cust_arr = None
            
            last_event_time = t
            
        # End of simulation for this seed
        
        # Calculate metrics for this seed
        win_len = horizon - start_stat
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0 # Assuming no losses in M/D/1 infinite buffer? 
            # Wait, "blk" is rejected/lost. In M/D/1 with infinite buffer, blk=0.
            # Does the problem imply finite capacity? "自动洗车机... 场内平均车辆数". 
            # Usually "car wash" has limited space. But without explicit capacity C, assume infinite?
            # If infinite, p_loss = 0.
            # Let's check constraints. "M/M/1" vs "M/D/1". Fixed service time -> D.
            # If no capacity given, assume infinite buffer. Thus blk=0, p_loss=0.
            # p_wait: fraction of time customers spend waiting? Or probability an arriving customer waits?
            # "p_wait" usually means P(waiting > 0) for an arrival.
            # We didn't track arrivals in window separately for p_wait.
            # Let's re-run logic or adjust tracking.
            
            # Actually, I need to track:
            # 1. Arrivals in window (to compute p_wait = arrivals_that_waited / total_arrivals_in_window)
            # 2. Departures in window (for W)
            # 3. Losses (if any)
            
            # My previous loop didn't count arrivals in window explicitly for p_wait denominator.
            # Let's refine the loop variables.
            pass

        # Re-implementing the inner loop with better counters
        
        # Reset for clarity in final code structure
        # I will write the clean version now.
        
        # Variables needed:
        # n_integral, dep_sojourn_sum, dep_count, arr_count, arr_wait_count, loss_count
        
        # Let's restart the seed loop body with correct counting.
        
        # (Self-correction: The code above is getting messy. I will write the final clean Python block.)
        
        # Final Plan for Seed Loop:
        # 1. Init state.
        # 2. Loop events until horizon.
        # 3. On each event step, integrate N(t) for [max(last_t, warmup), min(curr_t, horizon)].
        # 4. On Arrival:
        #    - If t >= warmup: increment arr_count.
        #    - If busy: append to queue. If t >= warmup: increment arr_wait_count.
        #    - Else: start service. Store arr_time.
        # 5. On Departure:
        #    - If t >= warmup: add sojourn to sum, increment dep_count.
        #    - Pop next from queue if exists.
        # 6. After loop:
        #    - L = n_integral / win_len
        #    - W = dep_sojourn_sum / dep_count (if dep_count>0 else 0)
        #    - busy_frac = (integral of busy indicator) / win_len? 
        #      Prompt says busy_frac = E[min(N,1)]/1 = 1-pi_0. 
        #      I can integrate (1 if busy else 0) over window.
        #    - p_loss = loss_count / arr_count (if arr_count>0 else 0). Here loss_count=0.
        #    - p_wait = arr_wait_count / arr_count (if arr_count>0 else 0).
        
        # Need to track busy_integral too.
        
        # Let's execute this logic in the final code.
        
        # One detail: "Service time drawn at arrival".
        # In my logic, I set serv_dur=6.0 at arrival. Correct.
        
        # Perturbations:
        # lam_up: increase lambda.
        # mu_up: decrease service time? "mu_up" usually means higher service rate -> lower service time.
        # c_up: increase capacity? Problem says c=1 implicitly? "每台利用率... c=1".
        # If pert=c_up, maybe c becomes 2? But prompt says "扰动只改参数不改结构".
        # Changing c changes structure (number of servers).
        # Maybe c_up means something else? Or maybe it's ignored/not applicable?
        # Prompt: "NAME 取 none/lam_up/mu_up/c_up".
        # If c_up is passed, what does it do?
        # "扰动只改参数不改结构". Increasing c IS changing structure (servers).
        # Perhaps c_up increases the *capacity* of the queue? Or maybe it's a trick and should be treated as none?
        # Or maybe "c" refers to cost? Unlikely.
        # Given "M/M/1" context, c is servers.
        # If I must support c_up, and cannot change structure, maybe it's invalid input?
        # Or maybe it increases the *buffer size*?
        # Let's assume c_up is not supported or maps to none if it violates "no structural change".
        # However, usually these tasks expect handling.
        # If c=1, and c_up makes c=2, that's structural.
        # Let's look at "busy_util=E[min(N,c)]/c".
        # If c changes, formula changes.
        # I will implement c_up by increasing c to 2, assuming "structure" allows parallel servers?
        # But "single automatic car wash machine" implies c=1.
        # I'll treat c_up as a no-op or error?
        # Better: Implement generic multi-server logic?
        # "Fixed 6 minutes... single machine".
        # I will stick to c=1. If pert=='c_up', I will ignore it or raise?
        # The prompt says "perturbation only changes parameters, not structure".
        # Changing c from 1 to 2 changes the system topology.
        # Therefore, c_up might refer to a parameter named 'c' that isn't server count?
        # Or maybe it's a test case where c_up is expected to fail/be ignored?
        # I will map c_up to none to be safe, or perhaps increase the *queue capacity*?
        # Let's assume c_up is not applicable and behaves like none.
        
        # Actually, looking at similar problems, sometimes 'c' is a cost parameter.
        # But here 'c' is clearly server count in the formula.
        # I will implement c=1 always. If pert=='c_up', I'll just print warning or ignore.
        # To be robust, I'll just ignore c_up.

        # Recalculating for the specific seed iteration inside the loop.
        
        # Code generation starts now.
        
        # Initialize counters for this seed
        n_integral = 0.0
        busy_integral = 0.0
        dep_sojourn_sum = 0.0
        dep_count = 0
        arr_count = 0
        arr_wait_count = 0
        loss_count = 0
        
        # State
        t = 0.0
        next_arr = random.expovariate(lam)
        busy = False
        curr_serv_end = float('inf')
        current_cust_arr = None
        q = [] # list of (arr_t, serv_dur)
        
        last_event_time = 0.0
        current_n = 0
        
        # Warmup
        start_stat = 0.25 * horizon
        end_stat = horizon
        win_len = end_stat - start_stat
        
        while t < horizon:
            next_arr_t = next_arr
            next_dep_t = curr_serv_end if busy else float('inf')
            next_t = min(next_arr_t, next_dep_t)
            
            if next_t > horizon:
                # Integrate up to horizon
                int_start = max(last_event_time, start_stat)
                int_end = horizon
                if int_start < int_end:
                    dur = int_end - int_start
                    n_integral += current_n * dur
                    if busy:
                        busy_integral += dur
                break
            
            # Integrate from last_event_time to next_t
            int_start = max(last_event_time, start_stat)
            int_end = min(next_t, horizon)
            if int_start < int_end:
                dur = int_end - int_start
                n_integral += current_n * dur
                if busy:
                    busy_integral += dur
            
            t = next_t
            
            if abs(t - next_arr_t) < 1e-9:
                # Arrival
                if t >= start_stat:
                    arr_count += 1
                
                if not busy:
                    busy = True
                    serv_dur = 6.0
                    curr_serv_end = t + serv_dur
                    current_cust_arr = t
                    current_n += 1
                else:
                    serv_dur = 6.0
                    q.append((t, serv_dur))
                    current_n += 1
                    if t >= start_stat:
                        arr_wait_count += 1
                
                next_arr = t + random.expovariate(lam)
                
            elif abs(t - next_dep_t) < 1e-9:
                # Departure
                sojourn = t - current_cust_arr
                if t >= start_stat:
                    dep_sojourn_sum += sojourn
                    dep_count += 1
                
                current_n -= 1
                
                if q:
                    next_cust_arr, next_cust_serv = q.pop(0)
                    busy = True
                    curr_serv_end = t + next_cust_serv
                    current_cust_arr = next_cust_arr
                else:
                    busy = False
                    curr_serv_end = float('inf')
                    current_cust_arr = None
            
            last_event_time = t
        
        # Compute estimates
        L_est = n_integral / win_len if win_len > 0 else 0.0
        W_est = dep_s
