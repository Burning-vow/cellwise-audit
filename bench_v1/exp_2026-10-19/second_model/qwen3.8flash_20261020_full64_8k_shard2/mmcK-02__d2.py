import sys, json, random
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            val = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[key] = val
            i += 2
        else:
            i += 1
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 100.0))
    S = int(args.get('seed-start', 1))
    pert = args.get('pert', 'none')
    
    time_unit = "hour"
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hour
    c = 2
    K = 4
    
    if pert == 'lam_up': lam_base *= 1.2
    elif pert == 'mu_up': mu_base *= 1.2
    elif pert == 'c_up': c += 1; K += 1
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for s_idx in range(N):
        seed = S + s_idx
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        servers_free_at = [0.0, 0.0] # Assuming c=2 initially, but c might change. 
        # Better to use a list of size c
        servers_free_at = [0.0] * c
        
        queue = deque() # Stores arrival times of waiting cars
        system_count = 0 # Cars in system (served + waiting)
        
        # State variables for integration
        last_event_time = 0.0
        current_system_count = 0
        busy_start_time = 0.0
        is_busy = False
        
        # Accumulators for this seed
        seed_L_area = 0.0
        seed_busy_time = 0.0
        seed_arr = 0
        seed_dep = 0
        seed_blk = 0
        seed_W_sum = 0.0
        seed_wait_count = 0
        
        # We need to handle events until H
        # Events: Arrival, Departure
        
        # Pre-generate service times? No, generate on arrival as required.
        # But we need to know when departures happen.
        # Strategy: Event-driven simulation.
        
        # Initial state
        # If no cars, next event is arrival.
        
        while True:
            # Determine next event time
            arr_t = next_arr if next_arr <= H else float('inf')
            
            # Find earliest departure among active servers
            dep_t = float('inf')
            dep_server_idx = -1
            for k in range(c):
                if servers_free_at[k] > last_event_time and servers_free_at[k] < dep_t:
                    dep_t = servers_free_at[k]
                    dep_server_idx = k
            
            # If both are inf, break
            if arr_t == float('inf') and dep_t == float('inf'):
                break
                
            # Choose next event
            if arr_t <= dep_t:
                # Process interval before arrival
                dt = arr_t - last_event_time
                if dt > 0:
                    # Integrate L
                    if last_event_time >= H * warmup_ratio:
                        seed_L_area += current_system_count * dt
                        if is_busy:
                            seed_busy_time += dt
                    
                    # Update time
                    last_event_time = arr_t
                
                # Handle Arrival at arr_t
                if arr_t > H: break # Should not happen due to check above, but safe
                
                seed_arr += 1
                
                # Check capacity
                if current_system_count < K:
                    # Accept car
                    # Generate service time now
                    svc_time = rng.expovariate(mu_base)
                    
                    # Find free server
                    free_server = -1
                    for k in range(c):
                        if servers_free_at[k] <= arr_t:
                            free_server = k
                            break
                    
                    if free_server != -1:
                        # Start service immediately
                        servers_free_at[free_server] = arr_t + svc_time
                        # This car does not wait
                        # W contribution will be added at departure? 
                        # Or we can store entry time.
                        # Let's store (arrival_time, start_service_time) or just arrival_time and calculate W at dep.
                        # Since it starts immediately, start_time = arr_t.
                        # We need to track which car corresponds to which server completion.
                        # Simpler: When a car enters service, record its arrival time associated with that server slot.
                        # But servers are shared. 
                        # Alternative: Maintain a list of (arrival_time, finish_time) for cars in service.
                        # And a queue for waiting cars.
                        
                        # Let's refactor state representation slightly for clarity within the loop constraints.
                        # Actually, standard M/M/c/K logic:
                        # If server free, assign car to server. Record arrival time in a structure linked to that server's next release.
                        # If no server free, push arrival time to queue.
                        
                        # To calculate W, we need arrival time of departing car.
                        # Let's keep a list `in_service` of tuples (server_idx, arrival_time).
                        # But server_idx changes.
                        
                        # Easier approach:
                        # Keep `queue` of arrival times for waiting cars.
                        # Keep `servers` array where each element is either None or (arrival_time, finish_time).
                        # Wait, finish_time depends on service time drawn at arrival.
                        
                        # Revised State:
                        # servers: list of length c. Each item is None or (arrival_time, finish_time).
                        # queue: deque of arrival_times.
                        
                        # Let's re-initialize structures properly outside the inner loop logic flow.
                        pass
                    else:
                        # Must be waiting
                        queue.append(arr_t)
                        # Car is in system, count increases
                        current_system_count += 1
                        if not is_busy:
                            is_busy = True
                            # Busy fraction definition: station not empty. 
                            # If a car arrives and waits, station is not empty.
                            # If a car arrives and gets served, station is not empty.
                            # So any car in system makes it busy.
                else:
                    # Blocked
                    seed_blk += 1
                    # System count unchanged
                
                # Schedule next arrival
                next_arr = arr_t + rng.expovariate(lam_base)
                
                # Note: The code above has a flaw in updating current_system_count and servers.
                # I need to rewrite the event handling block cleanly.
                
                # Resetting logic for the single function constraint...
                # I will implement a cleaner event loop below.
                break # Exit this messy attempt to restart clean logic in final code generation mentally.
            
            else:
                # Departure
                pass

# The thought process got tangled. I will write the clean version directly.
