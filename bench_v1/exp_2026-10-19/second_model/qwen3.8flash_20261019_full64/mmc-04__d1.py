import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0) # in minutes? No, prompt says H unit matches time_unit. Let's assume minute for internal logic or hour? Prompt: "average 10 people per hour", "service 10 mins". Usually simulation time is in minutes or hours. Let's use MINUTES as time_unit to avoid fractions for service rate.
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H_horizon = args.horizon
    S_start = args.seed_start
    pert_name = args.pert
    
    # Parameters
    # Arrival rate lambda: 10 per hour -> 10/60 per minute
    lam_base = 10.0 / 60.0 
    # Service rate mu: 10 min mean -> 1/10 per minute
    mu_base = 1.0 / 10.0
    c = 2 # servers
    
    if pert_name == 'lam_up':
        lam = lam_base * 1.1
    elif pert_name == 'mu_up':
        mu = mu_base * 1.1
    elif pert_name == 'c_up':
        pass # structure change not allowed by prompt "perturbation only changes parameters", but c is param. However prompt says "don't change structure". c=2 is fixed in problem statement. Let's ignore c_up or treat as no-op if it implies structural change. The prompt says "NAME takes none/lam_up/mu_up/c_up". If c_up means changing capacity, that's a parameter. But the problem says "simultaneously open 2 counters". I will stick to base params unless specified otherwise. Actually, standard perturbation might just scale rates. Let's assume c_up does nothing or scales something else? Given "only change parameters", maybe c is a parameter. But the queue discipline FCFS and 2 servers are core. I'll keep c=2.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    horizon_min = H_horizon # Assuming input H is in minutes based on typical sim tasks, but prompt says "H ... unit consistent with self-reported time_unit". If I report minute, H is minutes.
    
    # Warmup: remove first 25% of horizon
    warmup_end = 0.25 * horizon_min
    window_len = horizon_min - warmup_end
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    results_busy_util = []
    results_dep_rate = []
    results_lam_eff = []
    results_p_wait_list = []
    
    seed_list = []
    
    for i in range(N_seeds):
        current_seed = S_start + i
        seed_list.append(current_seed)
        rng = random.Random(current_seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0, 0.0] # Time when each server becomes free
        queue = deque() # List of (arrival_time, service_duration)
        
        # Statistics accumulators (for area integration)
        # We need to integrate L(t) over time.
        # L(t) = number of customers in system (waiting + being served)
        # We track events. Between events, state is constant.
        
        last_event_time = 0.0
        current_num_in_system = 0
        
        # Accumulators for the statistical window [warmup_end, horizon_min]
        # Area under L(t) curve within window
        area_L_window = 0.0
        # Sum of waiting times (time in system) for customers who DEPARTED within window?
        # W is average time in system. Usually calculated as Total Time in System / Number of Departures.
        # Or via Little's Law L = lambda * W. 
        # The prompt asks for W (avg wait+service). 
        # Method 1: Track individual customer sojourn times. Sum them up for those completed in window? 
        # Problem: Customers arriving before window end but leaving after? 
        # Standard discrete event sim for steady state stats:
        # L = Integral(L(t))dt / T_window
        # W = Sum(sojourn_times of customers who departed during window) / Count(departures during window)? 
        # This can be biased if arrivals/departures don't match.
        # Better approach for W: Use Little's Law estimate from L and effective arrival rate? 
        # Or accumulate total time spent by all customers present in the system during the window?
        # Let's use the definition: W = Average time in system.
        # In DES, we often compute W by summing the sojourn time of each customer who completes service within the observation window, divided by the number of such completions.
        # However, this ignores customers still in system at end.
        # Alternative: Integrate L(t) to get L. Then W = L / lambda_effective.
        # lambda_effective = (arrivals in window - losses?) / window_length.
        # Since there is no loss (infinite queue), arrivals = departures in steady state.
        # So W = L / lam.
        # But the prompt asks for p_wait (prob of waiting upon arrival). This requires tracking arrivals.
        
        # Let's track:
        # 1. Area of L(t) for L calculation.
        # 2. For p_wait: count arrivals where queue length > 0 OR both servers busy.
        # 3. For W: We can calculate it as L / lam_eff. Or sum sojourns. 
        #    Prompt asks for W explicitly. Using L/lam is robust if lam is known. 
        #    But let's try to be precise. 
        #    Let's accumulate `total_sojourn_time` for customers who DEPARTED in the window.
        #    And `count_departures`.
        #    Then W_est = total_sojourn / count_departures.
        #    Note: This might differ slightly from L/lam due to edge effects.
        #    Given "area-type quantities must be integrated before state change", L is definitely integral.
        #    W is an average. 
        
        # Variables for window accumulation
        num_arrivals_window = 0
        num_departures_window = 0
        num_waiting_on_arrival = 0
        total_sojourn_window = 0.0
        
        # Helper to update area
        def add_area(dt, n):
            nonlocal area_L_window
            if dt <= 0: return
            # Check overlap with window
            start_overlap = max(last_event_time, warmup_end)
            end_overlap = min(t, horizon_min)
            if end_overlap > start_overlap:
                overlap_dt = end_overlap - start_overlap
                area_L_window += n * overlap_dt

        # Initial state
        # At t=0, system empty.
        
        while t < horizon_min:
            # Determine next event time
            arr_t = next_arrival
            # Find earliest server completion
            serv_t = min(servers_free_at)
            
            # Next event time
            if arr_t < serv_t:
                next_t = arr_t
                event_type = 'arrival'
            else:
                next_t = serv_t
                event_type = 'departure'
                
            # Cap at horizon
            if next_t > horizon_min:
                break
                
            # Update area for the interval [last_event_time, next_t]
            dt = next_t - last_event_time
            add_area(dt, current_num_in_system)
            
            # Process event
            t = next_t
            
            if event_type == 'arrival':
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Check if waiting needed
                # Waiting if queue is not empty OR both servers are busy (servers_free_at > t)
                # Actually, if any server is free (servers_free_at[i] <= t), they go straight to service.
                # Else, they join queue.
                
                # Determine if this customer waits
                # A customer waits if they cannot start service immediately.
                # Start service immediately if exists server s.t. servers_free_at[s] <= t.
                can_start_immediately = False
                for s in range(c):
                    if servers_free_at[s] <= t:
                        can_start_immediately = True
                        break
                
                if not can_start_immediately:
                    num_waiting_on_arrival += 1
                
                # Record arrival in window?
                if t >= warmup_end:
                    num_arrivals_window += 1
                    
                # Add to system
                # Draw service time NOW
                svc_time = rng.expovariate(mu)
                
                # Assign to server or queue
                assigned_server = -1
                for s in range(c):
                    if servers_free_at[s] <= t:
                        assigned_server = s
                        break
                
                if assigned_server != -1:
                    # Start service
                    servers_free_at[assigned_server] = t + svc_time
                    # Customer enters service. 
                    # We need to know when they leave to add to departure stats.
                    # Store (departure_time, arrival_time, svc_time) in a list of active services?
                    # Or just rely on the fact that servers_free_at tracks the end time.
                    # But we need to link the specific customer to their departure to calculate sojourn.
                    # Let's maintain a list of scheduled departures: (dep_time, arr_time)
                    # When a departure happens, we pop the earliest one.
                    # But multiple servers...
                    # Simpler: Keep a global list of pending departures?
                    # Or: When assigning to server, push (t + svc_time, t) to a heap/list.
                    
                    # Let's use a simple list for active customers in service/waiting.
                    # Actually, for statistics, we just need to know when a customer leaves.
                    # We can store the departure time associated with the server slot.
                    # But if a server finishes, we need to know which customer left.
                    # Since FCFS, the customer who started service on that server is the one leaving.
                    # We need to track (server_id, dep_time, arr_time).
                    
                    # Let's refactor:
                    # Instead of just servers_free_at, let's have a list of events.
                    # But standard DES loop handles this.
                    # When a customer starts service on server s, we set servers_free_at[s] = dep_time.
                    # We also need to record that a customer with arrival time `t` will depart at `dep_time`.
                    # We can append `(dep_time, t)` to a list `pending_departures`.
                    # When processing a departure event at time `next_t`, we find the entry in `pending_departures` with dep_time == next_t.
                    # There should be exactly one (assuming continuous distribution).
                    
                    pending_departures.append((t + svc_time, t))
                    current_num_in_system += 1
                else:
                    # Join queue
                    queue.append((t, svc_time))
                    current_num_in_system += 1
                    
            elif event_type == 'departure':
                # Find which server finished
                # It's the one with servers_free_at == t (within float precision)
                # Or simply, we process the earliest departure.
                # We need to identify the customer.
                # Look through pending_departures for dep_time == t.
                
                # Remove from pending_departures
                # Since we appended them, and we process in order of time, the head of the list (if sorted) or search?
                # We didn't sort pending_departures. But we process events in chronological order.
                # The departure event corresponds to the minimum servers_free_at.
                # Let's find the index in servers_free_at that equals t.
                finished_server = -1
                for s in range(c):
                    if abs(servers_free_at[s] - t) < 1e-9:
                        finished_server = s
                        break
                
                if finished_server == -1:
                    # Should not happen
                    continue
                
                # Find the customer who was on this server.
                # We stored (dep_time, arr_time) in pending_departures.
                # We need to match dep_time.
                # Since floats, exact match might fail. But we used the same value.
                # Let's iterate pending_departures to find one with dep_time close to t.
                # Optimization: Since we process in order, the first element in pending_departures should be the one?
                # Not necessarily, because arrivals happen between departures.
                # But pending_departures contains ALL customers currently in service.
                # When a customer starts service, we add to pending_departures.
                # When they leave, we remove.
                # Is it possible that a later-added customer leaves earlier? Yes, if service time is shorter.
                # So pending_departures is not sorted by departure time.
                # We must search.
                
                idx_to_remove = -1
                arr_time_customer = None
                for k, (d, a) in enumerate(pending_departures):
                    if abs(d - t) < 1e-9:
                        idx_to_remove = k
                        arr_time_customer = a
                        break
                
                if idx_to_remove == -1:
                    # Error handling
                    continue
                
                del pending_departures[idx_to_remove]
                
                # Calculate sojourn time
                sojourn = t - arr_time_customer
                
                # Update stats if departure in window
                if t >= warmup_end:
                    num_departures_window += 1
                    total_sojourn_window += sojourn
                
                current_num_in_system -= 1
                
                # Check if queue has waiting customers
                if len(queue) > 0:
                    # Pop front
                    q_arr_time, q_svc_time = queue.popleft()
                    # Start service on the freed server
                    servers_free_at[finished_server] = t + q_svc_time
                    # Add to pending departures
                    pending_departures.append((t + q_svc_time, q_arr_time))
                    # Note: The customer moved from queue to service. 
                    # Current_num_in_system remains same (one left, one entered service).
                    # Wait, I decremented current_num_in_system above.
                    # Now I increment back?
                    # No, the customer was already counted in current_num_in_system while in queue.
                    # So moving from queue to service doesn't change total count.
                    # But I did `current_num_in_system -= 1` for the departing customer.
                    # Then I take one from queue. That customer was already in the count.
                    # So net change is -1. Correct.
                    # Do NOT increment current_num_in_system here.
                else:
                    # Server becomes idle
                    servers_free_at[finished_server] = float('inf') # Mark as idle? 
                    # Or just leave it. If no queue, server is free.
                    # But our check `servers_free_at[s] <= t` works if we set it to t?
                    # If we set to inf, then `inf <= t` is false. Good.
                    # But next arrival needs to see it as free.
                    # If we set to t, then `t <= next_arrival` is true.
                    # Let's set to t. It represents "free since t".
                    servers_free_at[finished_server] = t

            last_event_time = t

        # Final area update up to horizon
        dt = horizon_min - last_event_time
        add_area(dt, current_num_in_system)
        
        # Calculate metrics for this seed
        # L = Area / Window Length
        if window_len > 0:
            L_val = area_L_window / window_len
        else:
            L_val = 0.0
            
        # W = Total Sojourn / Num Departures
        if num_departures_window > 0:
            W_val = total_sojourn_window / num_departures_window
        else:
            W_val = 0.0
            
        # p_wait = Num Arrivals Waiting / Num Arrivals
        if num_arrivals_window > 0:
            p_wait_val = num_waiting_on_arrival / num_arrivals_window
        else:
            p_wait_val = 0.0
            
        # busy_frac = E[min(N,c)]/c ?
        # Prompt: "busy_frac definition: ... = E[min(N,c)]/c"
        # Wait, usually utilization rho = lambda/mu.
        # E[min(N,c)] is the expected number of busy servers.
        # So busy_frac = (Expected Busy Servers) / c.
        # How to compute Expected Busy Servers?
        # We can integrate the number of busy servers over time.
        # Let's add another accumulator: area_busy_servers.
        # In the loop, we need to track how many servers are busy.
        # I didn't track that separately.
        # I can re-calculate or modify loop.
        # Modification: Inside the loop, determine `num_busy` at each step.
        # `num_busy` = count of servers with `servers_free_at[s] > last_event_time`? 
        # No, `servers_free_at[s]` is the END time of current service.
        # If `servers_free_at[s] > t_current_interval_start`, then server is busy during the interval?
        # Actually, simpler
