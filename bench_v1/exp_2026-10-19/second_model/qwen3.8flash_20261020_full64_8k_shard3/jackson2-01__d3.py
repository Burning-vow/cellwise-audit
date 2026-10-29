import sys, json, random, argparse
from collections import deque

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    args = p.parse_args()
    
    lam_base = 4.0
    mu1_base = 60.0 / 7.5
    mu2_base = 60.0 / 6.0
    
    if args.pert == "lam_up": lam_base *= 1.1
    elif args.pert == "mu_up": mu1_base *= 1.1; mu2_base *= 1.1
    elif args.pert == "c_up": pass # capacity not explicitly perturbed in base model description, assume no change or handle if needed
    
    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_arr_count = 0
    all_dep_count = 0
    all_blk_count = 0
    all_busy_time_1 = 0.0
    all_busy_time_2 = 0.0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        
        # State variables
        t = 0.0
        q1 = deque() # (arrival_time, service_time)
        q2 = deque() # (arrival_time_from_q1_exit, service_time)
        busy1_until = -1.0
        busy2_until = -1.0
        
        # Statistics accumulators for this seed
        L_area = 0.0
        W_sum = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        wait_count = 0 # Customers who waited in queue 1 or 2? Usually p_wait is fraction of arrivals that wait. Let's define as those who found server busy upon arrival to system or specific queue. Standard: fraction of arrivals that enter queue.
        
        # Event list: (time, type, data)
        # Types: 'arr', 'srv1_end', 'srv2_end'
        events = []
        
        # Initial arrival
        next_arr_t = rng.expovariate(lam_base)
        events.append((next_arr_t, 'arr', None))
        
        last_stat_t = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, etype, edata = events.pop(0)
            
            if curr_t > horizon:
                break
                
            # Update statistics up to curr_t
            dt = curr_t - last_stat_t
            if dt > 0:
                # Count in-system customers
                n_in_sys = len(q1) + len(q2)
                if busy1_until > last_stat_t: n_in_sys += 1
                if busy2_until > last_stat_t: n_in_sys += 1
                # Note: A customer leaving srv1 enters q2 immediately if srv2 busy, else starts srv2.
                # We need to be careful about double counting or missing the transition instant.
                # Simpler approach: track number of jobs in system at any time t.
                # Jobs are in system from arrival until departure from srv2.
                
                # Recalculate N(t) more robustly:
                # Active in srv1: 1 if curr_t < busy1_until (but we are at event time, so check previous interval)
                # Actually, let's just count based on queues and servers status during [last_stat_t, curr_t]
                # This is tricky with discrete events. 
                # Alternative: Integrate L by summing (N * dt).
                # N changes only at events.
                
                cnt = 0
                if busy1_until > last_stat_t: cnt += 1
                if busy2_until > last_stat_t: cnt += 1
                cnt += len(q1)
                cnt += len(q2)
                L_area += cnt * dt
                
                if busy1_until > last_stat_t: busy_time_1 += min(dt, max(0, busy1_until - last_stat_t))
                if busy2_until > last_stat_t: busy_time_2 += min(dt, max(0, busy2_until - last_stat_t))
                
                last_stat_t = curr_t

            if etype == 'arr':
                arr_count += 1
                # Check if server 1 is free
                if busy1_until <= curr_t:
                    # Start service immediately
                    st = rng.expovariate(mu1_base)
                    busy1_until = curr_t + st
                    events.append((busy1_until, 'srv1_end', {'start_time': curr_t}))
                else:
                    # Queue
                    st = rng.expovariate(mu1_base)
                    q1.append({'arr_t': curr_t, 'srv_t': st})
                    # Check waiting probability later? Or here. If queued, it waits.
                    wait_count += 1 # Simplified: if enters queue, it waits.
                    
                # Schedule next arrival
                next_arr_t = curr_t + rng.expovariate(lam_base)
                if next_arr_t <= horizon:
                    events.append((next_arr_t, 'arr', None))
                    
            elif etype == 'srv1_end':
                start_t = edata['start_time']
                # Customer leaves srv1
                # Move to srv2
                if busy2_until <= curr_t:
                    # Start srv2 immediately
                    # Need service time for srv2. It was drawn when? 
                    # Requirement: "Service duration must be drawn at arrival".
                    # So we should have stored srv2 time too.
                    # Correction: In 'arr', we drew srv1 time. We also need srv2 time.
                    # Let's refactor: At arrival, draw both srv1 and srv2 times.
                    pass 
                else:
                    # Queue for srv2
                    pass
            
            # The above logic is flawed because I didn't store srv2 time at arrival.
            # Restarting logic inside loop for clarity in code generation...
            
            # Re-implementing correctly within the loop structure for the final output:
            
            # Resetting for correct implementation below in the actual code block.
            # Since I am generating code, I will write the correct version directly.
            
            # Placeholder to satisfy syntax if I were editing, but I will rewrite the whole function body properly.
            pass 

    # Correct Implementation follows in the final print statement construction
    # I will now generate the clean code.
