import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in hours
    lam_base = 6.0
    mu_base = 12.0 # 5 min mean -> 1/ (5/60) = 12 per hour
    c = 1
    K = 6 # capacity including service

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Capacity is fixed by problem statement "only 1 doctor", but perturbation might imply changing effective capacity or just a distractor? 
        # Problem says "perturbation only changes parameters not structure". If c_up means increasing capacity, it contradicts "1 doctor". 
        # However, usually c refers to number of servers. Here c=1. Let's assume c_up increases the number of servers if allowed, but problem says "only 1 doctor".
        # Re-reading: "扰动只改参数不改结构". Structure is M/M/1/K. Changing c would change structure to M/M/c/K.
        # Perhaps c_up refers to cost? No, no cost mentioned.
        # Let's look at standard perturbations. lam_up, mu_up are clear. c_up might be a typo for something else or implies changing the capacity limit K?
        # But K is also structural.
        # Given the strict constraint "only 1 doctor", I will treat c_up as having no effect on lambda/mu, or perhaps it's a trick.
        # Actually, often in these tasks, c is the number of servers. If pert=c_up, maybe it allows more servers? But prompt says "only 1 doctor".
        # I will stick to base parameters for c_up unless specified otherwise, or assume it affects nothing relevant to the single-server queue logic provided.
        # Wait, let's look at the keys. busy_util uses c. If c changes, busy_util changes.
        # If pert is c_up, I'll set c=2? But "only 1 doctor" is hard-coded in description.
        # Let's assume c_up is invalid or does nothing for this specific single-doctor scenario, OR it modifies the arrival rate/service rate indirectly?
        # Safest bet: Ignore c_up effect on structure, keep c=1. Or maybe it means "capacity up"? i.e. K increases?
        # Let's assume standard queueing perturbations: lam_up (increase arrival), mu_up (increase service rate). c_up likely means increase number of servers.
        # BUT the problem text says "only 1 doctor". This is a contradiction if c_up changes c.
        # I will implement c_up as increasing the number of servers to 2, as that is the standard meaning of parameter 'c' in queues, despite the text description being static. The text describes the BASE case. Perturbations modify parameters.
        pass
    
    # Reset based on pert
    lam = lam_base
    mu = mu_base
    c_val = 1
    K_val = 6

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c_val = 2
        K_val = 7 # Usually capacity scales with servers? Or stays same? Prompt says "waiting area + room total 6". If doctors increase, capacity might stay 6 or increase.
                  # Standard M/M/c/K. If c changes, K usually remains the system capacity limit.
                  # Let's keep K=6.
    
    time_unit = 'hour'
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    
    seeds_used_list = []
    
    for s_idx in range(N_seeds):
        current_seed = seed_start + s_idx
        seeds_used_list.append(current_seed)
        rng = random.Random(current_seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn upon arrival and attached to customer
        # We need a list of customers in system: (arrival_time, service_duration)
        # And a variable for when the server becomes free
        server_free_time = 0.0
        
        # Statistics accumulators (for integration)
        # Area under L(t) curve
        area_L = 0.0
        last_event_time = 0.0
        current_num_in_system = 0
        
        # Counters
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_waiting_times = 0.0 # For W calculation (total time in system)
        
        # Warmup handling
        warmup_end = horizon_hours * 0.25
        stats_start_time = warmup_end
        stats_end_time = horizon_hours
        
        # To handle warmup correctly with event-driven simulation:
        # We simulate until horizon_hours.
        # We integrate L(t) only from stats_start_time to stats_end_time.
        # We count arrivals/departures/blocks only if they occur within [stats_start_time, stats_end_time)?
        # Usually, "window" implies events happening in that window contribute to counts, and state integrals cover that window.
        # Customers arriving before warmup end but leaving after? Their waiting time contribution?
        # Standard practice: Discard data generated during warmup.
        # For L (average number in system): Integral of L(t) over [T_warm, T_end] / (T_end - T_warm).
        # For W (average time in system): Sum of (departure_time - arrival_time) for customers who DEPARTED in [T_warm, T_end]? 
        # Or customers who ARRIVED in [T_warm, T_end]?
        # Little's Law consistency: L = lambda_eff * W.
        # If we use departures in window for W, and integral for L, we should use effective arrival rate in window.
        # Let's define:
        # L: Time-average number in system during [T_warm, T_end].
        # W: Average time in system for customers who COMPLETED service during [T_warm, T_end].
        # p_loss: Blocks / Arrivals during [T_warm, T_end].
        # p_wait: Proportion of arrivals in [T_warm, T_end] that had to wait (server busy upon arrival).
        
        # Event loop
        while True:
            # Determine next event time
            # Events: Arrival, Departure
            
            # Calculate next departure time if any customer is in service
            # Note: In M/M/1, only one service at a time.
            # If server is busy, next departure is server_free_time.
            # If server is idle, next departure is infinity.
            
            next_departure = float('inf')
            if current_num_in_system > 0:
                # There is someone in service. The completion time is stored in server_free_time.
                # However, if multiple people are waiting, the next departure is indeed server_free_time.
                next_departure = server_free_time
            
            next_event_time = min(next_arrival, next_departure)
            
            if next_event_time > horizon_hours:
                break
                
            # Integrate L(t) from last_event_time to next_event_time
            dt = next_event_time - last_event_time
            if last_event_time < stats_end_time and next_event_time > stats_start_time:
                # Overlap interval
                start_int = max(last_event_time, stats_start_time)
                end_int = min(next_event_time, stats_end_time)
                if end_int > start_int:
                    area_L += current_num_in_system * (end_int - start_int)
            
            # Process event
            if next_event_time == next_arrival:
                # Arrival
                count_arrivals_total = count_arrivals # placeholder
                if next_event_time >= stats_start_time and next_event_time < stats_end_time:
                    count_arrivals += 1
                    
                # Check capacity
                if current_num_in_system < K_val:
                    # Accept
                    # Draw service time now
                    svc_time = rng.expovariate(mu)
                    # Add to system
                    current_num_in_system += 1
                    
                    # Check if server was idle
                    if current_num_in_system == 1:
                        # Server starts immediately
                        server_free_time = next_event_time + svc_time
                        # Waiting time is 0
                        if next_event_time >= stats_start_time and next_event_time < stats_end_time:
                            # This customer departs later. We track waiting time at departure.
                            pass
                    else:
                        # Server busy, customer waits
                        # We need to store the arrival time and service time for this customer to calculate W at departure.
                        # Since we process FIFO, we can maintain a queue of (arrival_time, service_time)
                        # But we already incremented count. We need a data structure.
                        # Let's refactor slightly: Use a list `queue` where index 0 is in-service.
                        # Actually, simpler: Just track `server_free_time`.
                        # When a new arrival comes and server is busy, they join the back.
                        # We need to know their arrival time to compute W when they leave.
                        # So we must store them.
                        
                        # Let's restart the state management logic properly.
                        pass
                else:
                    # Block
                    if next_event_time >= stats_start_time and next_event_time < stats_end_time:
                        count_blocks += 1
                
                # Schedule next arrival
                next_arrival = next_event_time + rng.expovariate(lam)
                
            elif next_event_time == next_departure:
                # Departure
                # Who leaves? The first person in the queue.
                # We need access to the queue.
                # Refactoring needed.
                pass
            
            last_event_time = next_event_time

        # The above loop logic is flawed because I didn't initialize the queue structure.
        # Let's rewrite the simulation core cleanly.
        
        # Reset for clean implementation
        rng = random.Random(current_seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        server_free_time = 0.0
        queue = [] # List of dicts: {'arr_t': ..., 'svc_t': ...}
        # Note: queue[0] is currently in service if len(queue)>0 and t < server_free_time?
        # Better: queue contains ALL customers in system.
        # If queue is not empty, the head is in service.
        # server_free_time indicates when the head will finish.
        
        current_num_in_system = 0
        last_event_time = 0.0
        area_L = 0.0
        
        count_arrivals_win = 0
        count_blocks_win = 0
        count_departures_win = 0
        sum_W_win = 0.0
        count_waited_win = 0 # Arrivals that found server busy
        
        stats_start = warmup_end
        stats_end = horizon_hours
        
        while True:
            # Next departure time
            if len(queue) > 0:
                next_departure = server_free_time
            else:
                next_departure = float('inf')
            
            next_event = min(next_arrival, next_departure)
            
            if next_event > stats_end:
                # Finalize integration up to stats_end
                dt = stats_end - last_event_time
                if last_event_time < stats_end:
                     area_L += len(queue) * (stats_end - last_event_time)
                break
            
            # Integrate L
            dt = next_event - last_event_time
            if last_event_time < stats_end and next_event > stats_start:
                start_i = max(last_event_time, stats_start)
                end_i = min(next_event, stats_end)
                if end_i > start_i:
                    area_L += len(queue) * (end_i - start_i)
            
            # Handle Arrival
            if next_event == next_arrival:
                in_window = (next_event >= stats_start and next_event < stats_end)
                if in_window:
                    count_arrivals_win += 1
                
                if len(queue) < K_val:
                    # Admit
                    svc_t = rng.expovariate(mu)
                    cust = {'arr_t': next_event, 'svc_t': svc_t}
                    queue.append(cust)
                    
                    # Did they wait?
                    # If server was busy (len(queue) > 1 before append? No, check if server_free_time > next_event)
                    # If server_free_time > next_event, server is busy.
                    # But if queue was empty, server_free_time <= next_event (idle).
                    # If queue was not empty, server is busy.
                    if in_window:
                        if len(queue) > 1: # Was there someone ahead?
                            count_waited_win += 1
                        # Note: If len(queue)==1, they started immediately.
                    
                    # Update server_free_time
                    # If server was idle (queue length became 1 from 0), start now.
                    # If server was busy, this customer joins back.
                    # The server_free_time is determined by the CURRENT head of queue finishing.
                    # When a new customer arrives, if the server was idle, it starts serving them.
                    # If the server was busy, the new customer waits.
                    
                    # Logic for server_free_time update:
                    # It doesn't change immediately upon arrival unless the server was idle.
                    # If server was idle (queue was empty before arrival):
                    if len(queue) == 1:
                        server_free_time = next_event + svc_t
                    # Else: server_free_time remains what it was (time when current head finishes).
                    
                else:
                    # Blocked
                    if in_window:
                        count_blocks_win += 1
                
                next_arrival = next_event + rng.expovariate(lam)
                
            # Handle Departure
            elif next_event == next_departure:
                in_window = (next_event >= stats_start and next_event < stats_end)
                if in_window:
                    count_departures_win += 1
                
                # Remove head
                departed_cust = queue.pop(0)
                w_time = next_event - departed_cust['arr_t']
                if in_window:
                    sum_W_win += w_time
                
                # Update server_free_time for next customer if any
                if len(queue) > 0:
                    # Next customer starts immediately
                    next_cust = queue[0]
                    server_free_time = next_event + next_cust['svc_t']
                else:
                    server_free_time = float('inf') # Idle
            
            last_event_time = next_event

        # Calculate metrics for this seed
        win_len = stats_end - stats_start
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
        else:
            L_est = area_L / win_len
            
            if count_departures_win > 0:
                W_est = sum_W_win / count_departures_win
            else:
                W_est = 0.0
            
            # Busy fraction: 1 - pi_0. 
            # pi_0 is proportion of time system is empty.
            # We integrated L(t). We didn't integrate indicator(I{N>0}).
            # Need to track time spent non-empty.
            # Let's re-calculate or add tracker.
            # Simpler: Track area_nonempty.
            # I missed tracking area_nonempty in the loop.
            # Let's patch: I will re-run the logic mentally or assume I can derive it?
            # No, I must code it.
            # I will add a variable `area_nonempty` and update it alongside `area_L`.
            
            # Since I cannot go back and edit the loop easily in this thought block without rewriting the whole string,
            # I will rewrite the simulation part in the final code to include `area_nonempty`.
            
            # For now, placeholders:
            busy_frac_est = 0.0 
            p_loss_est = count_blocks_win / count_arrivals_win if count_arrivals_win > 0 else 0.0
            p_wait_est = count_waited_win / count_arrivals_win if count_arrivals_win > 0 else 0.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals_win)
        all_blk.append(count_blocks_win)
        all_dep.append(count_departures_win)

    # Aggregate results
    seeds_used = len(all_L)
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_p_loss = sum(all_p
