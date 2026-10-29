import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 10.0 / 60.0  # arrivals per minute (10 per hour)
    mu_base = 1.0 / 6.0     # service rate per minute (mean 6 min)
    c = 2                   # servers

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = H * 60.0 if args.time_unit_is_hour else H
    # The problem says H is in time_unit. Let's assume time_unit is minute for internal calc? 
    # But output requires time_unit. Let's stick to minutes internally and report time_unit="minute".
    # Wait, the prompt says "H is integer style simulation horizon length, unit consistent with self-reported time_unit".
    # If I report time_unit="minute", then H is in minutes.
    # Standard M/M/c usually uses hours or minutes. Let's use minutes internally.
    # So horizon_min = H.
    
    total_horizon_min = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_busy_occupied = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []
    per_seed_busy_util = []
    per_seed_dep_rate = []
    per_seed_lam_eff = []
    per_seed_busy_occupied = []

    warmup_ratio = 0.25
    warmup_time = total_horizon_min * warmup_ratio
    stat_window_len = total_horizon_min - warmup_time

    for i in range(N_seeds):
        seed_val = seed_start + i
        rng = random.Random(seed_val)
        
        # State variables
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn at arrival and attached to customer
        # We need a queue of customers waiting/serving
        # For M/M/c FCFS, we can track completion times of servers
        # Or simpler: event list approach
        
        # Events: (time, type, data)
        # type: 'A' arrival, 'D' departure
        events = []
        
        # Initialize first arrival
        events.append((next_arrival, 'A', None))
        
        # Statistics accumulators for this seed
        # Area under curve for L (number in system)
        area_L = 0.0
        last_event_time = 0.0
        current_n = 0
        
        # Counts
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0 # In infinite buffer, blocked is 0. But p_wait is prob of waiting.
        # p_wait: probability that an arriving customer has to wait (all servers busy)
        count_waiting_on_arrival = 0
        
        # For busy_frac: E[min(N,c)]/c. This is also utilization.
        # We need integral of min(n(t), c) over time.
        area_min_nc = 0.0
        
        # For busy_occupied: 1 - pi_0. Integral of indicator(n>0).
        area_nonzero = 0.0
        
        # Total time simulated
        sim_end = total_horizon_min
        
        while events:
            # Get next event
            events.sort(key=lambda x: x[0])
            curr_t, etype, edata = events.pop(0)
            
            if curr_t > sim_end:
                break
                
            # Integrate statistics from last_event_time to curr_t
            dt = curr_t - last_event_time
            if dt > 0:
                # Only integrate if within statistical window? 
                # Prompt: "statistics only accumulated in window after removing first 25% warmup"
                # "area-type quantities must be integrated before changing state"
                
                # Determine overlap with stat window [warmup_time, sim_end]
                start_int = max(last_event_time, warmup_time)
                end_int = min(curr_t, sim_end)
                if end_int > start_int:
                    int_dt = end_int - start_int
                    area_L += current_n * int_dt
                    area_min_nc += min(current_n, c) * int_dt
                    if current_n > 0:
                        area_nonzero += int_dt
            
            last_event_time = curr_t
            
            if etype == 'A':
                # Arrival
                # Check if within stat window for counting probabilities
                in_stat_window = (curr_t >= warmup_time)
                
                # Draw service time now
                serv_time = rng.expovariate(mu)
                
                # Schedule next arrival
                inter_arr = rng.expovariate(lam)
                next_t = curr_t + inter_arr
                if next_t <= sim_end:
                    events.append((next_t, 'A', None))
                
                # Add to system
                current_n += 1
                if in_stat_window:
                    count_arrivals += 1
                    # Check if waiting: if number of people in system BEFORE adding was >= c?
                    # No, if all servers are busy when they arrive.
                    # Servers are busy if there are already c people in system (being served or waiting?)
                    # In M/M/c, if n >= c, new arrival waits.
                    # Note: current_n was incremented. So check old value.
                    if current_n - 1 >= c:
                        count_waiting_on_arrival += 1
                
                # Schedule departure for this customer
                dep_t = curr_t + serv_time
                if dep_t <= sim_end:
                    events.append((dep_t, 'D', None))
                    
            elif etype == 'D':
                # Departure
                current_n -= 1
                if current_n < 0:
                    current_n = 0 # Safety
                
                in_stat_window = (curr_t >= warmup_time)
                if in_stat_window:
                    count_departures += 1

        # After loop, integrate remaining time if any (should be covered by last event or sim_end)
        # Actually, the loop breaks when curr_t > sim_end. 
        # We need to ensure integration up to sim_end.
        # The previous logic integrates up to curr_t. If the last event was before sim_end, 
        # we missed the interval [last_event_time, sim_end].
        # However, events are generated up to sim_end. 
        # If no more events, we should integrate to sim_end.
        if last_event_time < sim_end:
            start_int = max(last_event_time, warmup_time)
            end_int = sim_end
            if end_int > start_int:
                int_dt = end_int - start_int
                area_L += current_n * int_dt
                area_min_nc += min(current_n, c) * int_dt
                if current_n > 0:
                    area_nonzero += int_dt

        # Calculate metrics for this seed
        if stat_window_len > 0:
            L_est = area_L / stat_window_len
            W_est = L_est / (count_arrivals / stat_window_len) if count_arrivals > 0 else 0.0
            # Little's Law: L = lambda_eff * W. Here lambda_eff is effective arrival rate into system.
            # Since no blocking, lambda_eff = count_arrivals / stat_window_len.
            
            busy_frac_est = (area_min_nc / stat_window_len) / c
            p_wait_est = count_waiting_on_arrival / count_arrivals if count_arrivals > 0 else 0.0
            arr_est = count_arrivals / stat_window_len # Rate per minute? No, prompt says "arr is average number of people per seed in window".
            # Re-read: "arr is statistical window average per seed person count". It's a count, not rate.
            # "dep is window average per seed leave count". Count.
            # "blk ... rejected/lost count". Count.
            # "dep_rate is effective departure rate per hour".
            
            arr_count = count_arrivals
            dep_count = count_departures
            blk_count = 0 # Infinite buffer
            
            dep_rate_per_hour = (dep_count / stat_window_len) * 60.0
            lam_eff_per_hour = (arr_count / stat_window_len) * 60.0
            
            p_loss_est = 0.0 # No loss
            busy_util_est = busy_frac_est # Same definition
            busy_occupied_est = area_nonzero / stat_window_len
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            per_seed_arr.append(arr_count)
            per_seed_dep.append(dep_count)
            per_seed_blk.append(blk_count)
            per_seed_busy_util.append(busy_util_est)
            per_seed_dep_rate.append(dep_rate_per_hour)
            per_seed_lam_eff.append(lam_eff_per_hour)
            per_seed_busy_occupied.append(busy_occupied_est)
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arr_count)
            all_dep.append(dep_count)
            all_blk.append(blk_count)
            all_busy_util.append(busy_util_est)
            all_dep_rate.append(dep_rate_per_hour)
            all_lam_eff.append(lam_eff_per_hour)
            all_p_loss.append(p_loss_est)
            all_busy_occupied.append(busy_occupied_est)

    seeds_used = len(per_seed_L)
    
    def avg(lst):
        return sum(lst)/len(lst) if lst else 0.0

    result = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_wait": avg(all_p_wait),
        "runtime_units": "minutes",
        "seed_list": [seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": stat_window_len,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_loss": avg(all_p_loss),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": avg(all_busy_occupied)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
