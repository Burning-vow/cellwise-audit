import random
import json
import argparse
import heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0  # 5 per hour
    c = 2
    K = 4  # max capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        K = 5
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
    
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        current_seed = seed_start + i
        rng = random.Random(current_seed)
        
        # Simulation state
        t = 0.0
        events = [] # heap of (time, type, data)
        # type: 0=arrival, 1=departure
        
        # State variables
        n_in_system = 0 # number of cars in system (waiting + serving)
        n_serving = 0   # number of cars currently being served
        
        # Statistics accumulators (for area integration and counts)
        last_event_time = 0.0
        area_n = 0.0
        area_busy = 0.0 # time when n_in_system > 0
        area_util = 0.0 # integral of min(n_in_system, c)
        
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        total_wait_time = 0.0 # sum of waiting times for completed services
        
        # Warmup period: first 25% of horizon
        warmup_end = H * 0.25
        
        # We need to track stats only after warmup.
        # To do this correctly with area integrals, we reset accumulators at warmup_end?
        # No, standard way: run simulation, but only accumulate stats from t >= warmup_end.
        # However, the prompt says "statistics only accumulated in window after removing first 25% warmup".
        # And "area-type quantities must be integrated before changing state".
        
        # Let's maintain global accumulators that are updated every event step, 
        # but we subtract the pre-warmup part or just start accumulating from warmup_end.
        # Easier: Run simulation. At each event, calculate delta_t. 
        # If the interval [last_event_time, t] overlaps with [warmup_end, H], add overlap length * value to stat.
        
        # Initialize first arrival
        next_arrival = rng.expovariate(lam)
        heapq.heappush(events, (next_arrival, 0, None))
        
        # Trackers for post-warmup stats
        pw_area_n = 0.0
        pw_area_busy = 0.0
        pw_area_util = 0.0
        pw_count_arr = 0
        pw_count_dep = 0
        pw_count_blk = 0
        pw_total_wait = 0.0
        pw_window_len = H - warmup_end
        
        while events:
            t_curr, ev_type, ev_data = heapq.heappop(events)
            
            if t_curr > H:
                break
            
            # Calculate time since last event for area integration
            dt = t_curr - last_event_time
            
            # Integrate areas over the intersection of [last_event_time, t_curr] and [warmup_end, H]
            # Since we stop at H, and warmup is fixed, we can check overlap.
            start_int = max(last_event_time, warmup_end)
            end_int = min(t_curr, H)
            
            if start_int < end_int:
                len_int = end_int - start_int
                # Current state during this interval was determined by previous events
                # n_in_system and n_serving are constant between events
                
                pw_area_n += n_in_system * len_int
                if n_in_system > 0:
                    pw_area_busy += len_int
                pw_area_util += min(n_in_system, c) * len_int

            # Process Event
            if ev_type == 0: # Arrival
                count_arrivals += 1
                if t_curr >= warmup_end:
                    pw_count_arr += 1
                
                if n_in_system < K:
                    # Accept car
                    n_in_system += 1
                    
                    # Generate service time now
                    serv_time = rng.expovariate(mu)
                    
                    if n_serving < c:
                        # Start service immediately
                        n_serving += 1
                        dep_time = t_curr + serv_time
                        heapq.heappush(events, (dep_time, 1, {'start_time': t_curr, 'serv_time': serv_time}))
                    else:
                        # Wait
                        # Store info needed to calculate wait time later? 
                        # Actually, we just need to know when it starts service.
                        # We push a dummy event? No, standard M/M/c/K logic:
                        # When a server becomes free, it picks up the next waiting car.
                        # But here we don't have explicit queue objects in heap easily without complex structure.
                        # Alternative: When departure happens, if there are waiting cars, one starts service.
                        # How to know how long they waited?
                        # We need to store the arrival time of waiting cars.
                        # Let's use a simple list/queue for waiting cars' arrival times.
                        pass 
                        
                    # Correction: Need a queue for waiting cars to compute W properly.
                    # Let's introduce a queue variable outside loop? No, inside function scope.
                    # I'll refactor slightly to include a waiting_queue.
                    
                else:
                    # Blocked
                    count_blocked += 1
                    if t_curr >= warmup_end:
                        pw_count_blk += 1

            elif ev_type == 1: # Departure
                # This event corresponds to a specific car finishing service
                # The car leaves the system
                n_in_system -= 1
                n_serving -= 1
                
                count_departures += 1
                if t_curr >= warmup_end:
                    pw_count_dep += 1
                
                # Check if any car was waiting
                # We need to access the waiting queue. 
                # Since I didn't define it in the outer scope yet, let's assume I will fix the code structure below.
                # For now, placeholder logic.
                
                # Schedule next arrival
                next_arrival = t_curr + rng.expovariate(lam)
                if next_arrival <= H:
                    heapq.heappush(events, (next_arrival, 0, None))

            last_event_time = t_curr

        # End of simulation for this seed
        # Note: The above loop has a flaw regarding the waiting queue implementation.
        # I will rewrite the core loop to handle the queue correctly within the single main function constraint.
        
        # Resetting for correct implementation in final code block...
        # The thought process identified the need for a queue.
        
        # Re-running mental simulation with Queue:
        # Variables: wait_q (list of arrival times)
        # On Arrival: if accepted, if servers available -> start service, push dep event. Else -> append arr_time to wait_q.
        # On Departure: pop from wait_q if not empty. New start_time = t_curr. Serv_time generated? 
        # NO! Prompt says: "Service duration must be drawn at customer arrival and attached to them."
        # So, on Arrival: draw serv_time. Store (arr_time, serv_time) in wait_q if no server.
        # If server available: start service immediately. Push dep event with (t_curr + serv_time).
        # On Departure: decrement n_serving. If wait_q not empty: pop front item (arr_time, serv_time). 
        #   Start service: new_start = t_curr. Push dep event (new_start + serv_time).
        #   Calculate wait time for this car: new_start - arr_time. Add to total_wait.
        
        # This requires storing tuples in the queue.
        
        # Let's finalize the code structure based on this.
        
        # Accumulate results for this seed
        if pw_window_len > 0:
            L_est = pw_area_n / pw_window_len
            busy_frac_est = pw_area_busy / pw_window_len
            util_est = pw_area_util / pw_window_len
            p_loss_est = pw_count_blk / pw_count_arr if pw_count_arr > 0 else 0.0
            # W estimation: Total wait time / Number of departures in window?
            # Careful: Cars arriving before warmup might leave after warmup.
            # Standard practice: Only count waits for cars that DEPARTED in the window?
            # Or cars that ARRIVED in the window?
            # Usually Little's Law consistency suggests using arrivals/departures in window.
            # Let's use: Sum of wait times for cars that departed in the window.
            # But my `pw_total_wait` accumulation needs to happen when a car starts service or finishes?
            # Wait time is known when service STARTS.
            # So when a car moves from Queue to Service, we add (Start_Time - Arr_Time) to accumulator IF Start_Time >= warmup_end?
            # Or if the car is counted in the window?
            # Let's stick to: Count wait time for cars whose SERVICE START occurred in the window.
            # And compare with Departures in window? This might mismatch.
            # Better: Average wait time of customers who ARRIVED in the window and eventually got served?
            # Simpler robust metric: Total time spent in system (W+Serv) vs L?
            # Let's calculate W as: (Total Time in System for departed cars in window) / Departs in window?
            # No, W is usually waiting time in queue.
            # Let's accumulate `wait_sum` when a car starts service.
            # Condition: If start_time >= warmup_end, add wait_duration to `pw_total_wait`.
            # Then W = pw_total_wait / pw_count_dep? Not exactly, because some cars started before warmup and left after.
            # Given the strict constraints, I will implement:
            # W = (Sum of waiting times for all cars that started service in the window) / (Number of cars that started service in the window).
            # But I don't track "starts" separately from "departs".
            # Let's track `pw_count_starts` and `pw_total_wait`.
            
            # Recalculating stats collection strategy for final code:
            # 1. Area integrals: Done via overlap calculation.
            # 2. Counts: Arrivals, Blocks, Departures done via timestamp check.
            # 3. Waiting Time: When a car begins service (either immediately on arrival or from queue), 
            #    if begin_time >= warmup_end, add (begin_time - arrival_time) to pw_total_wait and increment pw_count_starts.
            #    W = pw_total_wait / pw_count_starts.
            
            # Busy Utilization: E[min(N,c)]/c.
            # busy_occupied = 1 - pi_0 = fraction of time system non-empty.
            
            # Output keys mapping:
            # L: avg number in system
            # W: avg waiting time (minutes!) -> Convert hours to minutes.
            # busy_frac: 1 - pi_0 (fraction of time non-empty)
            # p_loss: blocked / arrived
            # runtime_units: "hour"
            # seed_list: list of seeds used
            # seeds_used: count
            # time_unit: "hour"
            # win: window length in hours
            # arr: avg arrivals per seed in window
            # blk: avg blocks per seed in window
            # busy_util: avg utilization per seed
            # dep: avg departures per seed in window
            # dep_rate: effective departure rate (per hour)
            # lam_eff: effective arrival rate (accepted arrivals / window)
            # p_wait: probability of waiting (fraction of accepted arrivals that had to wait?)
            #    Or fraction of time queue non-empty? Usually P(wait) = P(N>=c).
            #    Let's use empirical: count_starts_from_queue / count_accepted_in_window?
            #    Or simpler: Fraction of time n_in_system > c?
            #    Let's use: (Time where n_in_system > c) / Window.
            
            # I need to track `pw_area_wait` (time where n_in_system > c) for p_wait.
            
            pass 

    # Final aggregation across seeds
    # ...
