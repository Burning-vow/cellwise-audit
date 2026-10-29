import argparse
import json
import random
import heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # c is fixed at 1 for this problem, but if we were to change capacity it would be here.
        # The prompt says "perturbation only changes parameters not structure". 
        # For M/M/1, c=1 is structural. If c_up meant increasing servers, it would break the single server assumption.
        # However, usually c_up might mean changing a parameter related to cost or something else, 
        # but given the context of queueing, let's assume standard M/M/1 and ignore c_up effect on structure,
        # or perhaps it implies a different lambda/mu? 
        # Let's stick to none/lam_up/mu_up affecting rates. c_up doesn't make sense for M/M/1 unless it's a typo for something else.
        # We will treat c_up as no-op for rates if it doesn't fit, or maybe it affects nothing.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon_minutes = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_p_loss = []
    all_lam_eff = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used_list = []

    warmup_ratio = 0.25
    warmup_time = horizon_minutes * warmup_ratio
    stat_window_len = horizon_minutes - warmup_time

    for i in range(N_seeds):
        current_seed = seed_start + i
        seeds_used_list.append(current_seed)
        rng = random.Random(current_seed)
        
        # Event types: 0=Arrival, 1=Departure
        events = []
        
        # State variables
        n_in_system = 0
        last_event_time = 0.0
        
        # Accumulators for area integration (time-weighted)
        # We need to integrate N(t) over [warmup_time, horizon]
        # And also track waiting times for customers who arrive after warmup? 
        # No, W is average sojourn time. We should sum sojourn times of customers who DEPART within the window?
        # Or customers who ARRIVE within the window?
        # Standard steady-state estimation:
        # L = Time-average number in system. Integrate N(t) from t_warmup to T_end, divide by (T_end - t_warmup).
        # W = Average sojourn time. Sum of sojourn times of customers who COMPLETE service within the window?
        # Usually, Little's Law holds for the whole system. To estimate W, we can sum the sojourn times of all customers
        # who depart during the statistical window, divided by the number of such departures.
        # Alternatively, sum sojourn times of customers arriving in the window? But they might not depart.
        # Best practice for discrete event simulation with truncation:
        # Use the "departures within window" method for W, ensuring consistency with L via Little's Law approximation.
        # Or use the "arrivals within window" and only count those that depart? That biases towards short services.
        # Let's use: Sum of sojourn times for customers who DEPART in [t_warmup, T_end].
        # Count of such departures = dep_count.
        # W_est = total_sojourn_departed / dep_count.
        
        # For p_wait: Probability that an arriving customer has to wait.
        # In M/M/1, this is rho. Empirically: fraction of arrivals (in window?) that find server busy.
        # Let's count arrivals in the window that find n >= 1 (server busy).
        # Note: If arrival happens before warmup ends, do we count it?
        # The prompt says "statistics accumulated only in the window after removing first 25% warmup".
        # So we only consider events happening in [t_warmup, T_end].
        
        # Variables for current run
        area_n = 0.0
        total_sojourn_time = 0.0
        num_departures_in_window = 0
        num_arrivals_in_window = 0
        num_waiting_arrivals_in_window = 0
        num_blocked_in_window = 0 # M/M/1 infinite buffer, so 0 blocked always.
        
        # Customer tracking
        # Each customer needs: arrival_time, service_duration
        # Since we process events sequentially, we can store active customers' info.
        # When a departure occurs, we know which customer left? 
        # In FCFS, the one leaving is the one who arrived earliest among those still present.
        # We can maintain a queue of arrival times.
        
        arrival_queue = [] # List of arrival times of customers currently in system (waiting or being served)
        
        # Generate initial arrival
        next_arrival_time = rng.expovariate(lam)
        heapq.heappush(events, (next_arrival_time, 0))
        
        # Initial state: empty system
        
        while events:
            t, etype = heapq.heappop(events)
            
            if t > horizon_minutes:
                break
                
            dt = t - last_event_time
            
            # Update area integral if we are in the statistical window
            # The interval [last_event_time, t] contributes n_in_system * dt to the area.
            # We need to clip this interval to [warmup_time, horizon_minutes].
            
            start_int = max(last_event_time, warmup_time)
            end_int = min(t, horizon_minutes)
            
            if start_int < end_int:
                area_n += n_in_system * (end_int - start_int)
                
            last_event_time = t
            
            if etype == 0: # Arrival
                # Check if this arrival is in the statistical window
                if t >= warmup_time:
                    num_arrivals_in_window += 1
                    if n_in_system >= 1:
                        num_waiting_arrivals_in_window += 1
                
                # Add to queue
                arrival_queue.append(t)
                n_in_system += 1
                
                # Schedule next arrival
                inter_arrival = rng.expovariate(lam)
                heapq.heappush(events, (t + inter_arrival, 0))
                
                # If server was idle, start service immediately
                if n_in_system == 1:
                    serv_time = rng.expovariate(mu)
                    heapq.heappush(events, (t + serv_time, 1))
                    
            elif etype == 1: # Departure
                # This departure corresponds to the head of the queue (FCFS)
                arr_t = arrival_queue.pop(0)
                sojourn = t - arr_t
                
                # Check if this departure is in the statistical window
                if t >= warmup_time:
                    total_sojourn_time += sojourn
                    num_departures_in_window += 1
                    
                n_in_system -= 1
                
                # If there are more customers, start service for the next one
                if n_in_system > 0:
                    serv_time = rng.expovariate(mu)
                    heapq.heappush(events, (t + serv_time, 1))
        
        # Calculate metrics for this seed
        if stat_window_len > 0:
            L_est = area_n / stat_window_len
        else:
            L_est = 0.0
            
        if num_departures_in_window > 0:
            W_est = total_sojourn_time / num_departures_in_window
        else:
            W_est = 0.0
            
        # Busy fraction: E[min(N,1)] / 1. 
        # Area of min(N,1) is just the time when N>=1.
        # We didn't explicitly integrate min(N,1). 
        # But note: area_n integrates N. 
        # We need another accumulator for busy time.
        # Let's re-run logic? No, I missed accumulating busy time.
        # Correction: I need to accumulate busy_time_area as well.
        
        # Since I cannot go back, I must recalculate or fix the loop.
        # Wait, I am generating code. I should have included busy_time accumulation.
        # Let me rewrite the inner loop part mentally to ensure correctness.
        
        # Re-evaluating the code structure above:
        # I missed `busy_time_area`.
        # I will add it now in the final code block.
        
        pass 

    # Since I need to output valid code, I will construct the full correct version below.
    # The previous draft had a flaw in missing busy time accumulation.
    
    # Corrected Logic Plan:
    # 1. Initialize accumulators: area_n, area_busy, total_sojourn, counts.
    # 2. Loop events.
    # 3. On each step, calculate overlap of [last_t, t] with [warmup, horizon].
    # 4. Add n * overlap to area_n.
    # 5. Add min(n, 1) * overlap to area_busy.
    # 6. Process event.
    # 7. At end, compute stats.

    # Let's write the actual code string.

    results = {
        "L": 0.0,
        "W": 0.0,
        "busy_frac": 0.0,
        "p_wait": 0.0,
        "runtime_units": "minute",
        "seed_list": [],
        "seeds_used": 0,
        "time_unit": "minute",
        "win": 0.0,
        "arr": 0.0,
        "blk": 0.0,
        "busy_util": 0.0,
        "dep": 0.0,
        "dep_rate": 0.0,
        "lam_eff": 0.0,
        "p_loss": 0.0,
        "per_seed_L": [],
        "per_seed_W": [],
        "per_seed_busy_frac": [],
        "per_seed_p_loss": [],
        "per_seed_p_wait": []
    }
    
    # Resetting for actual execution flow in the generated code
    # I will generate the clean code now.

if __name__ == "__main__":
    import argparse
    import json
    import random
    import heapq

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--seeds', type=int, default=10)
        parser.add_argument('--horizon', type=float, default=1000.0)
        parser.add_argument('--seed-start', type=int, default=42)
        parser.add_argument('--pert', type=str, default='none')
        args = parser.parse_args()

        N_seeds = args.seeds
        H = args.horizon
        seed_start = args.seed_start
        pert = args.pert

        # Parameters in minutes
        lam_base = 8.0 / 60.0  # arrivals per minute
        mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
        
        if pert == 'lam_up':
            lam = lam_base * 1.1
            mu = mu_base
        elif pert == 'mu_up':
            lam = lam_base
            mu = mu_base * 1.1
        elif pert == 'c_up':
            lam = lam_base
            mu = mu_base
        else:
            lam = lam_base
            mu = mu_base

        time_unit = "minute"
        horizon_minutes = H
        warmup_ratio = 0.25
        warmup_time = horizon_minutes * warmup_ratio
        stat_window_len = horizon_minutes - warmup_time

        all_L = []
        all_W = []
        all_busy_frac = []
        all_p_wait = []
        all_arr = []
        all_dep = []
        all_blk = []
        all_busy_util = []
        all_busy_occupied = []
        all_p_loss = []
        all_lam_eff = []
        all_dep_rate = []
        
        per_seed_L = []
        per_seed_W = []
        per_seed_busy_frac = []
        per_seed_p_loss = []
        per_seed_p_wait = []
        
        seeds_used_list = []

        for i in range(N_seeds):
            current_seed = seed_start + i
            seeds_used_list.append(current_seed)
            rng = random.Random(current_seed)
            
            events = []
            n_in_system = 0
            last_event_time = 0.0
            
            area_n = 0.0
            area_busy = 0.0 # Integral of min(N, 1)
            total_sojourn_time = 0.0
            num_departures_in_window = 0
            num_arrivals_in_window = 0
            num_waiting_arrivals_in_window = 0
            num_blocked_in_window = 0
            
            arrival_queue = []
            
            next_arrival_time = rng.expovariate(lam)
            heapq.heappush(events, (next_arrival_time, 0))
            
            while events:
                t, etype = heapq.heappop(events)
                
                if t > horizon_minutes:
                    break
                
                dt = t - last_event_time
                
                start_int = max(last_event_time, warmup_time)
                end_int = min(t, horizon_minutes)
                
                if start_int < end_int:
                    overlap = end_int - start_int
                    area_n += n_in_system * overlap
                    area_busy += min(n_in_system, 1) * overlap
                    
                last_event_time = t
                
                if etype == 0: # Arrival
                    if t >= warmup_time:
                        num_arrivals_in_window += 1
                        if n_in_system >= 1:
                            num_waiting_arrivals_in_window += 1
                    
                    arrival_queue.append(t)
                    n_in_system += 1
                    
                    inter_arrival = rng.expovariate(lam)
                    heapq.heappush(events, (t + inter_arrival, 0))
                    
                    if n_in_system == 1:
                        serv_time = rng.expovariate(mu)
                        heapq.heappush(events, (t + serv_time, 1))
                        
                elif etype == 1: # Departure
                    arr_t = arrival_queue.pop(0)
                    sojourn = t - arr_t
                    
                    if t >= warmup_time:
                        total_sojourn_time += sojourn
                        num_departures_in_window += 1
                        
                    n_in_system -= 1
                    
                    if n_in_system > 0:
                        serv_time = rng.expovariate(mu)
                        heapq.heappush(events, (t + serv_time, 1))
            
            # Compute seed-level metrics
            if stat_window_len > 0:
                L_est = area_n / stat_window_len
                busy_frac_est = area_busy / stat_window_len
            else:
                L_est = 0.0
                busy_frac_est = 0.0
                
            if num_departures_in_window > 0:
                W_est = total_sojourn_time / num_departures_in_window
            else:
                W_est = 0.0
                
            if num_arrivals_in_window > 0:
                p_wait_est = num_waiting_arrivals_in_window / num_arrivals_in_window
            else:
                p_wait_est = 0.0
                
            p_loss_est = 0.0 # Infinite buffer
            blk_est = 0.0
            
            # busy_util = E[min(N,c)]/c. Here c=1, so same as busy_frac.
            busy_util_est = busy_frac_est
            
            # busy_occupied = 1 - pi_0. 
            # pi_0 is probability system is empty.
            # area_empty = stat_window_len - area_busy (since min(N,1) is 1 when N>0, 0 when N=0)
            # Actually min(N,1) is 1 if N>=1, 0 if N=0.
            # So area_busy is exactly the time spent non-empty.
            # busy_occupied = area_busy / stat_window_len = busy_frac_est.
            busy_occupied_est = busy_frac_est
            
            lam_eff_est = num_arrivals_in_window / stat_window_len if stat_window_len > 0 else 0.0
            dep_rate_est = num_departures_in_window / stat_window_len if stat_window_len > 0 else 0.0
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(num_arrivals_in_window)
            all_dep.append(num_departures_in_window)
            all_blk.append(blk_est)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occupied_est)
            all_p_loss.append(p_loss_est)
            all_lam_eff.append(lam_eff_est)
            all_dep_rate.append(dep_rate_est)
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)

        # Aggregate results
        avg_L = sum(all_L) / len(all_L) if all_L else 0.0
        avg_W = sum(all_W) / len(all_W) if all_W else 0.0
        avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
        avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
        avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
        avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
        avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
        avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
        avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0.0
        avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
        avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
        avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0
        
        # Convert dep_rate to per hour
        dep_rate_per_hour = avg_dep_rate * 60.0
        lam_eff_per_hour = avg_lam_eff * 60.0

        output = {
            "L": round(avg_L, 6),
            "W": round(avg_W, 6),
            "busy_frac": round(avg_busy_frac, 6),
            "p_wait": round(avg_p_wait, 6),
            "runtime_units": "minute",
            "seed_list": seeds_used_list,
            "seeds_used": N_seeds,
            "time_unit": "minute",
            "win": round(stat_window_len, 6),
            "arr": round(avg_arr, 6),
            "blk": round(avg_blk, 6),
            "busy_util": round(avg_busy_util, 6),
            "dep": round(avg_dep, 6),
            "dep_rate": round(dep_rate_per_hour, 6),
            "lam_eff": round(lam_eff_per_hour, 6),
            "p_loss": round(avg_p_loss, 6),
            "per_seed_L": [round(x, 6) for x in per_seed_L],
            "per_seed_W": [round(x, 6) for x in per_seed_W],
            "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
            "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
            "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
        }
        
        print(json.dumps(output))

    main()
