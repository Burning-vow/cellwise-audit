import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam = 7.0 / 60.0 # per minute
    mu = 1.0 / 5.0   # per minute
    
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': pass # c is fixed at 1 for M/M/1
    
    horizon_min = a.horizon * 60.0 if a.time_unit == 'hour' else a.horizon
    time_unit = 'minute'
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    seeds_used = 0
    seed_list = []
    
    warmup_ratio = 0.25
    win_len = horizon_min * (1 - warmup_ratio)
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n = 0
        last_t = 0.0
        
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        
        customers = [] # list of (arrival_time, service_time)
        
        while t < horizon_min:
            if next_arr < next_dep:
                t = next_arr
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                if n == 0:
                    st = rng.expovariate(mu)
                    next_dep = t + st
                    n = 1
                    customers.append((t, st))
                    count_arr += 1
                else:
                    # Infinite buffer assumed for standard MM1 unless specified otherwise? 
                    # Problem says "system stable", implies infinite queue or loss system?
                    # Standard MM1 has infinite queue. blk usually refers to loss systems.
                    # If it's MM1 with infinite queue, blk should be 0.
                    # Let's assume infinite queue capacity as per standard MM1 definition.
                    n += 1
                    count_arr += 1
                    # Service time drawn at arrival
                    st = rng.expovariate(mu)
                    customers.append((t, st))
                
                next_arr = t + rng.expovariate(lam)
                last_t = t
            else:
                t = next_dep
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                if n > 0:
                    arr_t, st = customers.pop(0)
                    w = t - arr_t
                    if last_t >= horizon_min * warmup_ratio:
                        sum_w += w
                    count_dep += 1
                    n -= 1
                    
                    if n > 0:
                        # Next departure is current time + remaining service of head?
                        # No, we stored full service time. But we need to know when the NEXT one finishes.
                        # In discrete event sim with exponential, memoryless property helps but here we pre-drew times.
                        # We need to track the finish time of the current server job.
                        # Actually, simpler: maintain a priority queue of departure times?
                        # Or just: if n>0, the next dep is t + service_time_of_next_customer?
                        # Wait, the service starts immediately after previous ends.
                        # So if n>0, the next customer's service started at t_prev_end? No.
                        # Let's restart logic slightly cleaner.
                        pass
                    else:
                        next_dep = float('inf')
                else:
                    next_dep = float('inf')
                
                last_t = t

        # The above loop logic for dependencies is tricky with pre-drawn times.
        # Correct approach:
        # State: n, next_arr, next_dep.
        # When arrival happens: draw st. If n==0, set next_dep = t+st. Else push to queue.
        # When departure happens: pop from queue. If queue not empty, set next_dep = t + st_of_new_head.
        
        # Re-implementing inner loop correctly:
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        n = 0
        last_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        q_sts = [] # queue of service times for waiting customers
        
        while t < horizon_min:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                st = rng.expovariate(mu)
                count_arr += 1
                
                if n == 0:
                    n = 1
                    next_dep = t + st
                else:
                    n += 1
                    q_sts.append(st)
                
                next_arr = t + rng.expovariate(lam)
                last_t = t
            else:
                t = next_dep
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                # Departure
                # Who departed? The one who was being served.
                # We don't store their arrival time explicitly in a separate var easily without restructuring.
                # Let's store (arr_time, st) in a deque-like structure or just track completion.
                # To calculate W, we need arrival time of departing customer.
                # Let's change q_sts to store (arr_time, st).
                pass
        
        # Final clean implementation inside loop:
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        n = 0
        last_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        q = [] # list of (arrival_time, service_time)
        
        while t < horizon_min:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                st = rng.expovariate(mu)
                count_arr += 1
                
                if n == 0:
                    n = 1
                    next_dep = t + st
                    # Store info for this customer? 
                    # We need to know when they leave to calc W.
                    # They leave at next_dep. Arrival was t.
                    # But if another arrives before next_dep, they join queue.
                    # We need to associate the departure event with the specific customer.
                    # Since FCFS, the first in queue leaves first.
                    # Let's push (t, st) to a global list? No, use a queue.
                    # If n becomes 1, the server takes this customer.
                    # We can store the current serving customer's start time and duration?
                    # Simpler: Queue holds (arrival_time, service_time).
                    # Server processes head of queue.
                    
                    # Reset queue logic:
                    # If n==0, we start serving immediately.
                    # We need to remember this customer's arrival time to compute W upon departure.
                    # Let's keep a variable `current_cust` = (arr_t, st)
                    current_cust = (t, st)
                    q = []
                else:
                    n += 1
                    q.append((t, st))
                
                next_arr = t + rng.expovariate(lam)
                last_t = t
            else:
                t = next_dep
                dt = t - last_t
                if last_t >= horizon_min * warmup_ratio:
                    area_n += n * dt
                    if n > 0: area_busy += dt
                
                # Customer current_cust departs
                arr_t, st = current_cust
                w = t - arr_t
                if last_t >= horizon_min * warmup_ratio:
                    sum_w += w
                count_dep += 1
                
                if len(q) > 0:
                    current_cust = q.pop(0)
                    next_dep = t + current_cust[1]
                    n -= 1 # One left, one enters service, net change 0? 
                          # n was including the one leaving. 
                          # Before dep: n included current_cust + q.
                          # After dep: n includes new current_cust + rest of q.
                          # So n decreases by 1.
                else:
                    n = 0
                    next_dep = float('inf')
                    current_cust = None
                
                last_t = t

        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w / count_dep if count_dep > 0 else 0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0
        p_wait_est = 0.0 # P(wait) = rho for MM1? Or empirical? 
                         # Empirical: fraction of arrivals that had to wait.
                         # Need to track this during sim.
        
        # Re-run tracking p_wait properly requires counting arrivals where n>0 at arrival time.
        # I missed that counter. Let's add it.
        
        # Due to complexity of re-running, I will integrate counters into the single pass.
        # Refactoring the loop body to include p_wait counter.
        
        # ... (Code generation continues with corrected loop)
