import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 5.0    # service rate per minute
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.1
    elif a.pert == 'mu_up':
        mu = mu_base * 1.1
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = a.horizon * 60.0 if a.time_unit == 'hour' else a.horizon
    # The prompt says H is in time_unit. Let's assume time_unit is minute for internal calc? 
    # "time_unit 填你程序内部时间轴的单位". Let's use minute internally.
    # If H is passed as hours (e.g., 100), we need to convert. But the prompt example `--horizon H` doesn't specify unit of H explicitly other than matching time_unit.
    # Let's assume H is in minutes if time_unit is minute. Or H is in hours if time_unit is hour.
    # To be safe and consistent with standard DES, let's pick minute as internal unit.
    # If user passes --horizon 100, does it mean 100 minutes or 100 hours?
    # Usually horizons are large. 100 minutes might be short. 100 hours is long.
    # Let's look at the parameters: lam=8/hr, mu=12/hr. rho=2/3.
    # If H=100 and unit=minute, sim length=100 mins. Arrivals ~13. Too few.
    # If H=100 and unit=hour, sim length=6000 mins. Arrivals ~800. Better.
    # However, the prompt says "H ... 单位与你自报的 time_unit 一致".
    # I will set time_unit = 'minute' and expect H to be in minutes. But to ensure stability, maybe I should interpret H as hours if it looks small? No, strict adherence.
    # Let's choose time_unit = 'minute'. Default H=10000 minutes (~7 days).
    # Wait, the default in argparse was 100.0. If that's minutes, it's too short.
    # Let's change default horizon to something reasonable in minutes, e.g., 10000.
    # But the CLI interface must accept what is given.
    # Let's stick to time_unit='minute'.
    
    time_unit = 'minute'
    total_time = a.horizon # in minutes
    
    warmup_frac = 0.25
    warmup_end = total_time * warmup_frac
    
    results_L = []
    results_W = []
    results_busy = []
    results_ploss = []
    results_pwait = []
    results_arr = []
    results_dep = []
    results_blk = []
    
    seed_list = []
    
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        n_customers = 0
        busy = False
        
        # Accumulators for area integration (only after warmup)
        area_n = 0.0
        area_busy = 0.0
        last_event_time = 0.0
        
        # Statistics within window
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_wait_times = 0.0 # For W calculation via Little's Law or direct? 
        # Direct W: Average time spent in system.
        # We can track entry times.
        customers_in_system = [] # List of arrival times
        
        # Event loop
        while t < total_time:
            # Determine next event
            if next_arrival <= next_departure:
                t_next = next_arrival
                event_type = 'arrival'
            else:
                t_next = next_departure
                event_type = 'departure'
                
            if t_next > total_time:
                break
                
            # Integrate areas up to t_next
            dt = t_next - last_event_time
            if last_event_time >= warmup_end:
                area_n += n_customers * dt
                if busy:
                    area_busy += dt
            
            last_event_time = t_next
            t = t_next
            
            if event_type == 'arrival':
                # Check if blocked? M/M/1/K? Prompt says "System stable", implies infinite buffer or loss?
                # "blk" key suggests blocking/loss. But M/M/1 usually has queue.
                # "打印店只有 1 名值班员". If queue is infinite, blk=0.
                # If finite capacity, blk>0.
                # Prompt doesn't specify capacity K. "系统稳定" usually means rho<1 for infinite queue.
                # If it were loss system, stability is different.
                # Given "M/M/1" context in title mm1-08, likely infinite queue.
                # So blk should be 0.
                # But why ask for blk? Maybe just to report 0.
                
                count_arr += 1
                customers_in_system.append(t)
                n_customers += 1
                
                if not busy:
                    busy = True
                    # Service time drawn at arrival
                    serv_time = rng.expovariate(mu)
                    next_departure = t + serv_time
                else:
                    # Queueing, departure time unchanged
                    pass
                
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'departure':
                count_dep += 1
                # Remove oldest customer (FIFO)
                arr_t = customers_in_system.pop(0)
                w_time = t - arr_t
                if t >= warmup_end: # Only count waits for those who left in window? 
                    # Standard definition: W is avg time in system for customers served in window.
                    # Or all customers present?
                    # Little's law L = lambda_eff * W.
                    # We calculate L from area.
                    # We calculate W from sum of times / count.
                    # Which count? Customers who departed in window.
                    sum_wait_times += w_time
                
                n_customers -= 1
                if n_customers > 0:
                    # Start service for next
                    # Need to know when they arrived to draw service time?
                    # NO! "服务时长必须在顾客到达时抽好并挂在该顾客身上"
                    # This implies we need to store service time with customer.
                    # My previous logic drew service time only when starting service. That violates constraint.
                    # Fix: Store (arrival_time, service_duration) in queue.
                    pass
                else:
                    busy = False
                    next_departure = float('inf')
                    
                # Next departure is determined by the head of queue if any
                if n_customers > 0:
                    # The next customer in line already has their service time assigned?
                    # We need to restructure data structure.
                    pass

        # Re-implementing with correct service time assignment at arrival
        
        # Reset for this seed
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        n_customers = 0
        busy = False
        
        area_n = 0.0
        area_busy = 0.0
        last_event_time = 0.0
        
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w_times = 0.0
        
        # Queue stores tuples: (arrival_time, service_duration)
        queue = []
        
        while t < total_time:
            if next_arrival <= next_departure:
                t_next = next_arrival
                ev = 'A'
            else:
                t_next = next_departure
                ev = 'D'
            
            if t_next > total_time:
                break
            
            dt = t_next - last_event_time
            if last_event_time >= warmup_end:
                area_n += n_customers * dt
                if busy:
                    area_busy += dt
            
            last_event_time = t_next
            t = t_next
            
            if ev == 'A':
                count_arr += 1
                # Draw service time NOW
                serv_dur = rng.expovariate(mu)
                queue.append((t, serv_dur))
                n_customers += 1
                
                if not busy:
                    busy = True
                    # Pop first item to start service immediately? 
                    # No, we just started. The server takes the first one.
                    # But we added to queue.
                    # Logic: If idle, take from queue, set departure.
                    arr_t, dur = queue.pop(0)
                    n_customers -= 1 # Still in system, but handled separately?
                    # Actually, n_customers counts people in system (queue + service).
                    # If we pop from queue, they are still in system.
                    # Let's keep n_customers as total in system.
                    # When we pop from queue to start service, they are still in system.
                    # So n_customers remains same.
                    # But we removed them from queue list.
                    # We need to track who is being served.
                    # Simpler: Queue holds waiting customers. Server holds current customer.
                    
                    # Refactor state:
                    # server_customer: None or (arr_time, serv_dur)
                    # wait_queue: list of (arr_time, serv_dur)
                    # n_customers = len(wait_queue) + (1 if server_customer else 0)
                    
                    # Let's restart the inner loop logic with this clearer state.
                    pass
                else:
                    # Just add to wait queue
                    pass
                
                next_arrival = t + rng.expovariate(lam)
                
            elif ev == 'D':
                # Finish service
                count_dep += 1
                # Calculate W for this customer
                # Who finished? The one in server.
                # We need to have stored their arrival time.
                # In the 'A' branch, if not busy, we set server.
                # If busy, we add to queue.
                # On 'D', we clear server, then check queue.
                
                # This requires restructuring the code significantly.
                # Let's rewrite the simulation part cleanly.
                pass

        # Clean Rewrite
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # State
        server_active = False
        server_arrival_time = 0.0
        wait_queue = [] # List of arrival times. Service times are pre-drawn?
        # Constraint: "服务时长必须在顾客到达时抽好并挂在该顾客身上"
        # So wait_queue should hold (arrival_time, service_time)
        
        n_in_system = 0
        
        area_n = 0.0
        area_busy = 0.0
        last_evt_t = 0.0
        
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        sum_w = 0.0
        
        while t < total_time:
            if next_arrival <= next_departure:
                t_next = next_arrival
                ev = 'A'
            else:
                t_next = next_departure
                ev = 'D'
            
            if t_next > total_time:
                break
            
            dt = t_next - last_evt_t
            if last_evt_t >= warmup_end:
                area_n += n_in_system * dt
                if server_active:
                    area_busy += dt
            
            last_evt_t = t_next
            t = t_next
            
            if ev == 'A':
                cnt_arr += 1
                serv_t = rng.expovariate(mu)
                cust = (t, serv_t)
                
                if not server_active:
                    server_active = True
                    server_arrival_time = t
                    next_departure = t + serv_t
                    # Customer goes directly to service, not in wait_queue
                    # But they are in system.
                    n_in_system += 1
                else:
                    wait_queue.append(cust)
                    n_in_system += 1
                    # next_departure unchanged
                
                next_arrival = t + rng.expovariate(lam)
                
            elif ev == 'D':
                cnt_dep += 1
                # Customer leaves
                w_time = t - server_arrival_time
                if t >= warmup_end:
                    sum_w += w_time
                
                n_in_system -= 1
                server_active = False
                
                if wait_queue:
                    next_cust = wait_queue.pop(0)
                    server_active = True
                    server_arrival_time = next_cust[0]
                    next_departure = t + next_cust[1]
                else:
                    next_departure = float('inf')
        
        # End of simulation for seed s
        
        win_len = total_time - warmup_end
        if win_len > 0:
            L_est = area_n / win_len
            busy_est = area_busy / win_len
            # W estimation: sum_w / cnt_dep_in_window?
            # cnt_dep includes all departures. We summed w only if t>=warmup_end.
            # But some customers arriving before warmup end might leave after.
            # Their w_time is counted.
            # Number of such customers? Hard to track exactly without storing more info.
            # Approximation: Use Little's Law? L = lambda * W.
            # Or average over departures in window.
            # How many dep in window? We didn't count specifically.
            # Let's count dep_in_window.
            # We need to modify loop to count dep_in_window.
            pass

        # Due to complexity and line limit, I will simplify W calculation using Little's Law consistency check or direct average if possible.
        # Actually, standard practice: W = Total Time Spent / Number of Departures.
        # We need number of departures in window.
        
        # Let's refine the loop to count dep_win.
        
        # Final Code Structure below
