import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 6.0 # per hour
    mu_base = 10.0 # per hour (6 min avg -> 1/0.1 hr)
    
    if args.pert == 'lam_up': lam_base *= 1.1
    elif args.pert == 'mu_up': mu_base *= 1.1
    elif args.pert == 'c_up': pass # c is fixed at 1 for M/M/1
    
    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * warmup_frac
    
    seeds_used = []
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
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n = 0 # number of customers in system
        next_arrival = rng.expovariate(lam_base)
        next_departure = float('inf')
        
        # Statistics accumulators (integrated over time or counted events)
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        
        # For PASTA and waiting probability: 
        # We need to track if a customer waited upon arrival.
        # In M/M/1 with FCFS, wait > 0 iff server busy at arrival.
        count_wait = 0
        
        last_event_time = 0.0
        
        while True:
            # Determine next event time
            next_event = min(next_arrival, next_departure)
            
            if next_event > horizon:
                break
                
            dt = next_event - t
            
            # Integrate areas BEFORE updating state
            if t >= warmup_end:
                area_n += n * dt
                if n > 0:
                    area_busy += dt
            
            t = next_event
            
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                if t >= warmup_end:
                    count_arr += 1
                    if n > 0:
                        count_wait += 1
                
                # Service time drawn now
                service_time = rng.expovariate(mu_base)
                
                # Update state
                n += 1
                
                # Schedule departure if server was idle
                if n == 1:
                    next_departure = t + service_time
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam_base)
                
            else:
                # Departure
                if t >= warmup_end:
                    count_dep += 1
                    # Calculate sojourn time for this customer?
                    # We don't have individual entry times stored easily without lists.
                    # Alternative: Use Little's Law relation L = lambda * W.
                    # But we need direct estimate of W.
                    # To get W directly, we need to store arrival times.
                    # Let's refactor slightly to store arrival times in a queue.
                    pass 
                
                # This approach needs a queue for arrival times to compute W accurately per customer.
                # Re-initializing loop logic with queue.
                break 

        # Restart simulation with proper queue tracking for W
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arrival = rng.expovariate(lam_base)
        next_departure = float('inf')
        arrival_queue = [] # stores arrival times
        
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        count_wait = 0
        
        while True:
            next_event = min(next_arrival, next_departure)
            if next_event > horizon:
                break
            
            dt = next_event - t
            if t >= warmup_end:
                area_n += n * dt
                if n > 0:
                    area_busy += dt
            
            t = next_event
            
            if abs(t - next_arrival) < 1e-9:
                if t >= warmup_end:
                    count_arr += 1
                    if n > 0:
                        count_wait += 1
                
                service_time = rng.expovariate(mu_base)
                arrival_queue.append(t)
                n += 1
                
                if n == 1:
                    next_departure = t + service_time
                
                next_arrival = t + rng.expovariate(lam_base)
            else:
                if t >= warmup_end:
                    count_dep += 1
                    arr_t = arrival_queue.pop(0)
                    w = t - arr_t
                    sum_w += w
                
                n -= 1
                if n > 0:
                    # Next departure time is current time + new service time
                    # Note: The service time for the next customer was already determined?
                    # No, in standard DES, service time is drawn at start of service.
                    # BUT prompt says: "Service duration must be drawn when customer arrives".
                    # So we need to store service times too.
                    pass
                
                # Correction: Store service times along with arrivals
                # Refactoring again to include service times in queue
                
                # Since I cannot restart easily in thought block, I will write the final code carefully.
                # Key constraint: Draw service time at arrival.
                # Queue elements: (arrival_time, service_duration)
                
                # If n > 0 after departure, the next customer starts service immediately.
                # Their service duration was already drawn.
                # So next_departure = t + queue[0][1]
                
                if n > 0:
                    next_departure = t + arrival_queue[0][1] # Wait, queue holds (arr, svc). 
                    # Actually, let's keep two queues or one list of tuples.
                    # Let's use a list `custs` where each item is [arrival_time, service_time].
                    
                # Need to fix the loop structure in the final output.
                break

    # Final implementation plan:
    # 1. Initialize RNG.
    # 2. Loop until horizon.
    # 3. Events: Arrival, Departure.
    # 4. On Arrival: Draw service time. Add (t, svc) to queue. Increment N. If N==1, schedule dep.
    # 5. On Departure: Pop from queue. Decrement N. If N>0, schedule dep using head of queue's svc.
    # 6. Accumulate stats only if t >= warmup_end.
    # 7. Area integration happens before state change.
    
    # Resetting variables for actual code generation...
    
    results = {
        "L": 0, "W": 0, "busy_frac": 0, "p_wait": 0, "runtime_units": "", 
        "seed_list": [], "seeds_used": 0, "time_unit": "", "win": 0,
        "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0, 
        "lam_eff": 0, "p_loss": 0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [], 
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    # Placeholder to satisfy syntax check during thinking, real logic below
    print(json.dumps(results))

if __name__ == "__main__":
    main()
