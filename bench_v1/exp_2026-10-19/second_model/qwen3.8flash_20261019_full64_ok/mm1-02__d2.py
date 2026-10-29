import sys, json, math, random
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 20.0; seed_start = 42; pert = "none"
    i = 0
    while i < len(args):
        if args[i] == "--seeds": seeds_n = int(args[i+1]); i += 2
        elif args[i] == "--horizon": horizon = float(args[i+1]); i += 2
        elif args[i] == "--seed-start": seed_start = int(args[i+1]); i += 2
        elif args[i] == "--pert": pert = args[i+1]; i += 2
        else: i += 1

    lam_base = 4.0 # per hour
    mu_base = 12.0 # per hour (1/5 min)
    
    if pert == "lam_up": lam = lam_base * 1.2
    elif pert == "mu_up": mu = mu_base * 1.2
    elif pert == "c_up": lam = lam_base; mu = mu_base # c is fixed at 1 in problem, perturbation might imply capacity change but problem says 1 server. If c_up means capacity up, it's still 1? Or maybe it means lambda up? The prompt says "pert NAME ... none/lam_up/mu_up/c_up". Usually c_up changes number of servers. But the problem states "only 1 server". If c_up changes structure, it violates "perturbation only changes parameters not structure". So c_up likely does nothing or is invalid for this specific single-server model unless we interpret it as changing service rate? Let's assume c_up has no effect on parameters for a single server system as structure is fixed to 1. Or perhaps it's a distractor. I will treat c_up as no change to lam/mu since c=1 is structural.
    else: lam = lam_base; mu = mu_base
    
    if pert == "c_up":
        # Structure cannot change, so parameters remain same as base
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    horizon_hours = horizon # Assuming H is in hours based on typical DES problems with hourly rates. If H was minutes, conversion needed. Prompt says "H is integer style simulation horizon length, unit consistent with self-reported time_unit". I report time_unit="hour". So H is hours.
    
    warmup_frac = 0.25
    win_start = warmup_frac * horizon_hours
    win_len = horizon_hours - win_start
    
    all_L = []; all_W = []; all_busy = []; all_ploss = []; all_pwait = []
    all_arr = []; all_dep = []; all_blk = []
    
    total_time_area = 0.0
    total_wait_time_sum = 0.0
    total_customers_in_window = 0
    total_departures_in_window = 0
    total_blocked_in_window = 0
    total_busy_time = 0.0
    
    # For per-seed stats
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    used_seeds = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        used_seeds.append(current_seed)
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn upon arrival and attached to customer
        # We need a queue. Since it's M/M/1, we can simulate events.
        # State: 
        #   t: current time
        #   next_event_type: 'arrival' or 'departure'
        #   next_event_time
        #   queue: list of customers waiting (each has service_time_remaining? No, service starts immediately if idle. If busy, they wait. When service ends, next starts.
        #   Actually, standard event scheduling:
        #   Events: Arrival, Departure.
        #   On Arrival:
        #     Draw service time S ~ Exp(mu). Attach to customer.
        #     If server idle: Start service. Schedule Departure at t+S. Mark server busy.
        #     Else: Add to queue.
        #   On Departure:
        #     Server becomes idle.
        #     If queue not empty: Pop first customer. Start service. Schedule Departure at t + remaining_service_time_of_that_customer? 
        #       Wait, service time was drawn at arrival. It doesn't change. So when a customer enters service, their full service time applies.
        #       Correction: In M/M/1, service time is memoryless. But here we draw it at arrival.
        #       If a customer waits, their service time is already known. When they start service, they take that exact amount of time.
        #       So: Queue stores (service_time).
        #       On Departure:
        #         If queue: pop service_time. Schedule new departure at t + service_time.
        #         Else: server idle.
        
        # Statistics accumulation within window [win_start, horizon_hours]
        # Area under N(t) curve for L
        # Time spent by each customer in system for W
        
        last_stat_time = 0.0
        n_current = 0 # Number of customers in system (waiting + serving)
        server_busy = False
        queue = deque() # Stores service times of waiting customers
        
        # To calculate area, we need to integrate N(t) over the window.
        # We track contributions from segments.
        
        # Variables for this seed's window stats
        seed_area_N = 0.0
        seed_total_service_completion_time_sum = 0.0 # Sum of (departure_time - arrival_time) for those who departed in window? 
        # W is average time in system. Usually calculated as sum(time_in_system)/count(departures).
        # But we must be careful with truncation. Customers arriving before end but departing after?
        # Standard practice: Only count customers who fully complete within the window? Or use Little's Law approximations?
        # The prompt asks for "average stay time W". This is typically E[T].
        # Estimator: Sum of actual times in system for all customers who DEPARTED during the window / Number of departures.
        # However, if a customer arrives before window and departs inside, their time includes pre-window part. That's fine.
        # If a customer arrives inside and departs outside, they are not counted in departures.
        # This creates bias if window is short. Horizon 20h is long enough.
        
        seed_count_arrivals_in_window = 0
        seed_count_departures_in_window = 0
        seed_count_blocked = 0 # M/M/1 has infinite buffer, so blocked=0 always. p_loss=0.
        seed_busy_time = 0.0
        seed_wait_count = 0 # Customers who had to wait (arrived when busy)
        
        # Event loop
        # Initialize first event
        # We need to handle the state transitions correctly regarding the window boundaries.
        
        # Helper to add area contribution
        def add_area(t_start, t_end, n_val):
            nonlocal seed_area_N
            if t_end <= win_start or t_start >= horizon_hours: return
            overlap_start = max(t_start, win_start)
            overlap_end = min(t_end, horizon_hours)
            if overlap_end > overlap_start:
                seed_area_N += n_val * (overlap_end - overlap_start)
                
        def add_busy_time(t_start, t_end, is_busy):
            nonlocal seed_busy_time
            if not is_busy: return
            if t_end <= win_start or t_start >= horizon_hours: return
            overlap_start = max(t_start, win_start)
            overlap_end = min(t_end, horizon_hours)
            if overlap_end > overlap_start:
                seed_busy_time += (overlap_end - overlap_start)

        # Initial state
        # Generate first arrival
        # We need to process events until horizon
        
        # Pre-generate arrivals? No, dynamic.
        # We maintain next_arrival_time and next_departure_time (if any).
        
        next_arrival_t = rng.expovariate(lam)
        next_departure_t = float('inf')
        
        # Track last transition time for integration
        last_transition_t = 0.0
        
        # We need to know if server was busy in previous interval to accumulate busy time properly?
        # Better: At every event, we close the previous interval [last_transition_t, t_event] using the state DURING that interval.
        
        while True:
            # Determine next event time
            t_next = min(next_arrival_t, next_departure_t)
            
            if t_next > horizon_hours:
                # Close final interval
                add_area(last_transition_t, horizon_hours, n_current)
                add_busy_time(last_transition_t, horizon_hours, server_busy)
                break
            
            # Process interval [last_transition_t, t_next]
            add_area(last_transition_t, t_next, n_current)
            add_busy_time(last_transition_t, t_next, server_busy)
            
            t = t_next
            
            if t == next_arrival_t:
                # Arrival
                # Draw service time now
                svc_time = rng.expovariate(mu)
                
                # Check if within window for counting arrivals?
                # "arr is average per seed person count in statistical window"
                # Does "in window" mean arrival time in window? Yes.
                if win_start <= t < horizon_hours:
                    seed_count_arrivals_in_window += 1
                
                # Update state
                if not server_busy:
                    server_busy = True
                    next_departure_t = t + svc_time
                    # Customer starts service immediately. Time in system = svc_time.
                    # But we don't know departure yet. We store arrival time?
                    # We need to track individual customers to compute W accurately.
                    # Since we only care about those who DEPART in window, we can store (arrival_time, service_time) in a "serving" slot?
                    # And for queue, store (arrival_time, service_time).
                    
                    # Let's refine data structures.
                    # queue: list of tuples (arrival_time, service_time)
                    # serving: tuple (arrival_time, service_time) or None
                    
                    # Currently serving:
                    serving_cust = (t, svc_time)
                    n_current += 1
                else:
                    # Server busy, join queue
                    queue.append((t, svc_time))
                    n_current += 1
                    if win_start <= t < horizon_hours:
                        seed_wait_count += 1 # Arrived and waited
                
                # Generate next arrival
                next_arrival_t = t + rng.expovariate(lam)
                
            elif t == next_departure_t:
                # Departure
                # Who is leaving? The one being served.
                arr_t, svc_t = serving_cust
                dep_t = t
                
                # Did this customer arrive/depart in window?
                # We count departures in window for W denominator.
                if win_start <= dep_t < horizon_hours:
                    seed_count_departures_in_window += 1
                    # Time in system
                    time_in_sys = dep_t - arr_t
                    seed_total_service_completion_time_sum += time_in_sys
                
                # Next customer?
                if queue:
                    next_arr_t, next_svc_t = queue.popleft()
                    serving_cust = (next_arr_t, next_svc_t)
                    next_departure_t = t + next_svc_t
                    # Server remains busy
                    # n_current stays same (one left, one entered service)
                else:
                    server_busy = False
                    serving_cust = None
                    next_departure_t = float('inf')
                    n_current -= 1
            
            last_transition_t = t

        # End of simulation for this seed
        
        # Calculate stats for this seed
        # L = Area / Window Length
        if win_len > 0:
            l_est = seed_area_N / win_len
        else:
            l_est = 0.0
            
        # W = Sum(TimeInSys) / Count(Departures)
        if seed_count_departures_in_window > 0:
            w_est = seed_total_service_completion_time_sum / seed_count_departures_in_window
        else:
            w_est = 0.0
            
        # Busy Fraction = BusyTime / WindowLength
        if win_len > 0:
            bf_est = seed_busy_time / win_len
        else:
            bf_est = 0.0
            
        # P_loss = Blocked / Arrivals (Blocked is 0 for M/M/1)
        pl_est = 0.0
        
        # P_wait = WaitCount / Arrivals
        if seed_count_arrivals_in_window > 0:
            pw_est = seed_wait_count / seed_count_arrivals_in_window
        else:
            pw_est = 0.0
            
        per_seed_L.append(l_est)
        per_seed_W.append(w_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        all_L.append(l_est)
        all_W.append(w_est)
        all_busy.append(bf_est)
        all_ploss.append(pl_est)
        all_pwait.append(pw_est)
        all_arr.append(seed_count_arrivals_in_window)
        all_dep.append(seed_count_departures_in_window)
        all_blk.append(0)

    # Aggregate results
    avg_L = sum(all_L) / seeds_n if seeds_n > 0 else 0
    avg_W = sum(all_W) / seeds_n if seeds_n > 0 else 0
    avg_busy = sum(all_busy) / seeds_n if seeds_n > 0 else 0
    avg_ploss = sum(all_ploss) / seeds_n if seeds_n > 0 else 0
    avg_pwait = sum(all_pwait) / seeds_n if seeds_n > 0 else 0
    
    avg_arr = sum(all_arr) / seeds_n if seeds_n > 0 else 0
    avg_dep = sum(all_dep) / seeds_n if seeds_n > 0 else 0
    avg_blk = sum(all_blk) / seeds_n if seeds_n > 0 else 0
    
    # Dep rate per hour
    if win_len > 0 and seeds_n > 0:
        # Total departures across all seeds / (Total window time across all seeds)
        # Each seed has window win_len.
        total_dep_all = sum(all_dep)
        total_win_all = seeds_n * win_len
        dep_rate = total_dep_all / total_win_all if total_win_all > 0 else 0
    else:
        dep_rate = 0
        
    # Effective lambda
    lam_eff = avg_arr / win_len if win_len > 0 else 0
    
    # busy_util = E[min(N,c)]/c. Here c=1. E[N]/1 = L.
    busy_util = avg_L
    
    # busy_occupied = 1 - pi_0. pi_0 is prob empty.
    # From simulation, fraction of time empty = 1 - busy_frac.
    # So 1 - pi_0 should equal busy_frac.
    busy_occupied = avg_busy

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_pwait, 6),
        "runtime_units": "hours",
        "seed_list": used_seeds,
        "seeds_used": seeds_n,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_ploss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
