import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # in hours
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H_horizon = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters
    lam_base = 9.0 # per hour
    mu_base = 10.0 # per hour (6 min mean -> 1/0.1 h)
    c_max = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c_max = 5
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_lam_eff = []
    all_win = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        horizon = H_horizon
        
        # State variables
        queue = deque() # waiting patients
        service_end_time = None # when current service ends
        num_in_system = 0 # including service and queue
        
        # Statistics accumulators (for area integration)
        # We need to track time spent in each state or use event-driven integration
        # Let's track: total_time_busy, total_area_N (integral of N(t)), total_arrivals, total_departures, total_blocked
        # For W, we need sum of sojourn times of completed customers
        
        total_time_busy = 0.0
        last_event_time = 0.0
        prev_num_in_system = 0
        
        total_arrivals = 0
        total_blocked = 0
        total_departures = 0
        total_sojourn_time_sum = 0.0
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * horizon
        stats_start_time = warmup_end
        
        # To handle warmup correctly with area integrals, we can either:
        # 1. Run simulation from 0 to horizon, but only accumulate stats after warmup_end.
        # 2. This requires careful handling of the integral at the boundary.
        
        # Event types: 'arrival', 'departure'
        # Generate next arrival
        next_arrival_t = rng.expovariate(lam)
        next_departure_t = float('inf')
        
        while True:
            # Determine next event time
            if next_arrival_t < next_departure_t:
                event_t = next_arrival_t
                event_type = 'arrival'
            else:
                event_t = next_departure_t
                event_type = 'departure'
            
            if event_t > horizon:
                break
            
            # Integrate area up to event_t
            dt = event_t - last_event_time
            if last_event_time < stats_start_time and event_t > stats_start_time:
                # Split interval
                dt_pre = stats_start_time - last_event_time
                dt_post = event_t - stats_start_time
                if prev_num_in_system > 0:
                    total_time_busy += dt_post # busy if N>0? No, busy if server is occupied.
                    # Server is occupied if there is someone in service.
                    # In M/M/1/K, server is occupied if N >= 1.
                    pass
                
                # Actually, let's define "busy" as server occupied.
                # Server occupied if num_in_system >= 1.
                
                # Recalculate carefully
                # Area of N(t)
                if last_event_time < stats_start_time:
                    # Part before warmup ignored
                    # Part after warmup counted
                    count_dt = event_t - max(last_event_time, stats_start_time)
                    total_area_N += prev_num_in_system * count_dt
                    if prev_num_in_system > 0:
                        total_time_busy += count_dt
                else:
                    total_area_N += prev_num_in_system * dt
                    if prev_num_in_system > 0:
                        total_time_busy += dt
            else:
                if last_event_time >= stats_start_time:
                    total_area_N += prev_num_in_system * dt
                    if prev_num_in_system > 0:
                        total_time_busy += dt
            
            last_event_time = event_t
            
            if event_type == 'arrival':
                # Check capacity
                if num_in_system < c_max:
                    # Enter system
                    num_in_system += 1
                    total_arrivals += 1
                    
                    # If server idle, start service immediately
                    if num_in_system == 1:
                        service_duration = rng.expovariate(mu)
                        next_departure_t = event_t + service_duration
                        # Record arrival time for this customer
                        # We need to store arrival time to calculate sojourn later
                        # Since it's a single server, we can just push to queue if not starting service?
                        # Or simpler: maintain a list of arrival times for those in system.
                        # But we need to match departure with specific arrival.
                        # Let's use a queue of arrival times.
                        # If server was idle, this customer starts service.
                        # We don't strictly need to know who is in service vs waiting for L, 
                        # but for W we need individual sojourn times.
                        
                        # Let's keep a global list of arrival times for all customers currently in system.
                        # When a departure happens, we remove the oldest arrival time (FIFO).
                        # Wait, M/M/1 is FIFO.
                        # So we can just append arrival time to a list `in_system_times`.
                        # But we also have a queue structure conceptually.
                        # Let's simplify: `in_system_times` is a list/deque of arrival times.
                        # Length of `in_system_times` is `num_in_system`.
                        # The one being served is the first one? Yes, FIFO.
                        # So when a new arrival comes and server is idle, it becomes the first one.
                        # If server is busy, it goes to end of queue.
                        
                        # Actually, we already incremented num_in_system.
                        # We need to add arrival time to our tracking structure.
                        # Let's use a deque `customer_queue` storing arrival times.
                        # If we started service, the head of queue is in service.
                        # If we didn't start service (server busy), it joins tail.
                        
                        # Correction: If num_in_system became 1, server was idle.
                        # So this customer enters service.
                        # Add to queue.
                        customer_queue.append(event_t)
                    else:
                        # Server busy, join queue
                        customer_queue.append(event_t)
                    
                    # Update next arrival
                    inter_arrival = rng.expovariate(lam)
                    next_arrival_t = event_t + inter_arrival
                else:
                    # Blocked
                    total_blocked += 1
                    # Update next arrival
                    inter_arrival = rng.expovariate(lam)
                    next_arrival_t = event_t + inter_arrival
                
                prev_num_in_system = num_in_system

            elif event_type == 'departure':
                # A customer leaves
                # Remove oldest arrival time
                if len(customer_queue) > 0:
                    arr_time = customer_queue.popleft()
                    sojourn = event_t - arr_time
                    total_sojourn_time_sum += sojourn
                    total_departures += 1
                    num_in_system -= 1
                    
                    # If there are still customers, start service for next one
                    if num_in_system > 0:
                        service_duration = rng.expovariate(mu)
                        next_departure_t = event_t + service_duration
                    else:
                        next_departure_t = float('inf')
                
                prev_num_in_system = num_in_system

        # End of simulation loop
        
        # Final integration step? 
        # The loop breaks when event_t > horizon.
        # We need to integrate from last_event_time to horizon.
        dt_final = horizon - last_event_time
        if last_event_time < stats_start_time and horizon > stats_start_time:
             count_dt = horizon - max(last_event_time, stats_start_time)
             total_area_N += prev_num_in_system * count_dt
             if prev_num_in_system > 0:
                 total_time_busy += count_dt
        elif last_event_time >= stats_start_time:
             total_area_N += prev_num_in_system * dt_final
             if prev_num_in_system > 0:
                 total_time_busy += dt_final
        
        win_len = horizon - stats_start_time
        
        if win_len <= 0:
            continue
            
        L_est = total_area_N / win_len
        W_est = total_sojourn_time_sum / total_departures if total_departures > 0 else 0.0
        # Convert W to minutes
        W_min = W_est * 60.0
        
        busy_frac_est = total_time_busy / win_len
        
        p_loss_est = total_blocked / (total_arrivals + total_blocked) if (total_arrivals + total_blocked) > 0 else 0.0
        
        # p_wait: probability that an arriving customer has to wait?
        # Or fraction of time queue is non-empty?
        # Usually P(wait) in M/M/1 is rho. Here finite capacity.
        # Let's define p_wait as fraction of arrivals that find server busy (and thus wait, unless blocked).
        # We didn't track this directly. 
        # Alternative: Fraction of time N > 1?
        # Let's approximate p_wait as fraction of successful arrivals that had to wait.
        # We need to track how many arrivals found server busy.
        # I missed tracking that. 
        # Let's re-run logic mentally: 
        # If I want to be precise, I should have tracked `arrivals_finding_server_busy`.
        # Given constraints, I'll estimate p_wait using Little's Law variant or just set to 0 if not tracked properly?
        # No, I must output it.
        # Let's assume p_wait = fraction of time N >= 2? No.
        # Standard definition: Probability an arrival waits.
        # In discrete event sim, we can count:
        # On arrival, if num_in_system_before_arrival >= 1, then wait.
        # I didn't save that counter.
        # I will modify the code to include `count_waited`.
        
        # Since I cannot change the flow easily now without rewriting, I will derive p_wait approximately or fix the code.
        # Fixing code is better.
        
        # Re-initializing counters for clarity in final code generation...
        # I will rewrite the inner loop part in the final string to ensure `count_waited` is captured.
        
        # For now, placeholder calculation based on available data:
        # busy_util = E[min(N,c)]/c. 
        # E[N] = L. 
        # E[min(N,c)] is not simply L. 
        # I need to track integral of min(N, c)? 
        # Actually, busy_util usually means average utilization of servers. 
        # With 1 doctor, c=1 effectively for service? 
        # Problem says "1 doctor", "capacity 4". 
        # "busy_util=E[min(N,c)]/c". Here c likely refers to number of servers? 
        # Text says "1名医生". So servers=1. Capacity=4.
        # If c in formula is number of servers (1), then busy_util = E[min(N,1)]/1 = P(N>=1) = busy_frac.
        # If c in formula is system capacity (4), then busy_util = E[min(N,4)]/4 = L/4.
        # The prompt distinguishes `busy_frac` (1-pi0) and `busy_util`.
        # And asks for `busy_occupied` which is same as busy_frac.
        # Let's assume `busy_util` uses c=number of servers=1. Then it equals busy_frac.
        # But they ask for both. Maybe `busy_util` uses c=capacity?
        # "E[min(N,c)]/c". If c=1, it's utilization. If c=4, it's occupancy rate.
        # Given "1 doctor", standard utilization is against 1.
        # I will calculate `busy_util` as `L / 1.0`? No, that's L.
        # Let's look at `busy_occupied=1-pi0`.
        # I will compute `busy_util` as `total_time_busy / win_len` (same as busy_frac) if c=1.
        # But to distinguish, maybe they want `L/capacity`?
        # Let's stick to `busy_util` = `L / 1.0` is wrong dimensionally?
        # Let's assume `busy_util` is the standard server utilization = `busy_frac`.
        # And `busy_occupied` is also `busy_frac`.
        # Why two keys? Maybe one is `L/c` where c is capacity?
        # Prompt: "busy_util=E[min(N,c)]/c". It doesn't specify what c is in the formula context vs problem context.
        # Problem: "1 doctor". Capacity 4.
        # Usually c denotes number of servers in queueing theory.
        # So c=1. Then busy_util = busy_frac.
        # I will output them as equal.
        
        # p_wait: I will add a counter in the final code.
        
        # lam_eff: effective arrival rate (accepted)
        lam_eff = total_arrivals / win_len
        
        dep_rate = total_departures / win_len
        
        # Store results
        all_L.append(L_est)
        all_W.append(W_min)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        # p_wait needs to be calculated in loop
        all_p_wait.append(0.0) # Placeholder, will fix in code
        all_arr.append(total_arrivals / win_len) # Rate? "arr is ... average per seed person count"? 
        # "arr 是统计窗口内平均每种子的人数计数" -> Count? Or Rate?
        # "dep_rate 是...有效离开率".
        # "arr" key description: "average per seed person count". Sounds like total count averaged over seeds?
        # But per_seed arrays exist.
        # Top level `arr` might be mean of counts? Or mean of rates?
        # "arr 是统计窗口内平均每种子的人数计数" -> Mean count of arrivals per seed.
        # "blk ... 人数计数" -> Mean count of blocks.
        # "dep ... 人数计数" -> Mean count of departures.
        # So these are totals divided by seeds_used.
        
        all_arr_counts = [] # Will collect raw counts
        all_blk_counts = []
        all_dep_counts = []
        
        # Refactoring plan for final code:
        # 1. Initialize lists for raw counts.
        # 2. Inside loop, track `count_waited`.
        # 3. Calculate p_wait = count_waited / total_arrivals.
        # 4. Append raw counts to lists.
        # 5. After loop, compute averages.

        # Since I am generating the code now, I will write the correct version.
        
        # Note: The previous block was analysis. Now writing final code.
        
        # Resetting for actual code generation...
        pass

    # This structure is getting messy in thought. I will write clean code below.
    
    # Clean Code Structure:
    # Parse args
    # Init global accumulators for top-level stats (sums across seeds)
    # Loop seeds:
    #   Init local RNG
    #   Init sim state
    #   Init local counters (area, time, counts, etc.)
    #   Simulate events until horizon
    #   Handle final integration
    #   Compute local metrics
    #   Append local metrics to per_seed lists
    #   Accumulate local raw counts to global sums for top-level averages
    # Compute top-level averages
    # Print JSON

    # One detail: "面积型量必须在改变状态之前积分"
    # My integration logic above did this.

    # Perturbation check:
    # none/lam_up/mu_up/c_up
    # c_up changes capacity.

    # Time unit: Hour.
    # W output in minutes.

    # Ready to generate.
