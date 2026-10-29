import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # in hours
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H_horizon = args.horizon
    S_start = args.seed_start
    pert_name = args.pert

    # Parameters
    base_lam = 9.0 # per hour
    base_mu = 10.0 # per hour (6 min mean -> 1/0.1 hr)
    c = 1
    K = 4 # capacity including service
    
    lam = base_lam
    mu = base_mu
    
    if pert_name == 'lam_up':
        lam *= 1.1
    elif pert_name == 'mu_up':
        mu *= 1.1
    elif pert_name == 'c_up':
        pass # c is fixed by problem statement "only 1 doctor", but if we were to perturb c, it would be here. 
              # The prompt says "perturbation only changes parameters not structure". c is a parameter of the system definition? 
              # Usually c_up means increasing servers. But the problem says "only 1 doctor". 
              # Let's assume c_up increases capacity K or servers? 
              # Given "MM1K", usually M/M/1/K. If c_up implies changing c, then c becomes >1? 
              # But the problem description fixes "1 doctor". 
              # However, standard discrete event sim tasks often allow perturbing lambda, mu, and sometimes capacity/servers.
              # If c_up is specified, I will interpret it as increasing the number of servers c from 1 to 2? 
              # Or does it mean increasing K? 
              # Let's look at the variable names: lam_up, mu_up, c_up. 
              # In queueing theory, c is number of servers. 
              # If I change c, the model changes from M/M/1/K to M/M/c/K. 
              # The prompt says "perturbation only changes parameters not structure". Changing c from 1 to 2 is a parameter change in the general M/M/c/K model, but the specific instance is M/M/1/K. 
              # To be safe and consistent with "M/M/1" in title mm1K-05, maybe c_up refers to K? 
              # No, K is usually capacity. c is servers. 
              # Let's stick to the most common interpretation: c is number of servers. 
              # If c_up is active, set c=2. 
              # BUT, the problem text says "only 1 doctor". 
              # If I change c, I violate the text description for that run? 
              # The instruction says "perturbation only changes parameters". 
              # I will implement c_up as setting c=2. If this breaks the "1 doctor" constraint logically, it's what the flag implies. 
              # Alternatively, maybe c_up means "capacity up"? i.e., K increases? 
              # Let's check typical naming conventions. lam, mu, c are standard. 
              # I'll assume c is server count. 
              # Wait, if c changes, the logic for service completion needs to handle multiple servers. 
              # My current plan assumes single server logic or generic multi-server? 
              # Generic multi-server is safer. 
              # Let's write generic M/M/c/K logic.
    
    if pert_name == 'c_up':
        c = 2 # Increase servers to 2
        
    # Time unit: Hours internally, convert W to minutes at end.
    time_unit = "hour"
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_time_sum = 0.0
    total_arrivals_sum = 0
    total_departures_sum = 0
    total_blocked_sum = 0
    total_wait_count_sum = 0 # Number of customers who waited (arrival found server busy)
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    warmup_time = H_horizon * warmup_ratio
    
    for i in range(N_seeds):
        seed_val = S_start + i
        seed_list.append(seed_val)
        rng = random.Random(seed_val)
        
        # State variables
        t = 0.0
        n_in_system = 0 # Includes those in service and waiting
        num_servers_busy = 0
        
        # Event lists
        # We need to track service completions. 
        # Since service times are exponential, we can just keep a list of completion times for each customer currently in service.
        # For M/M/c, when a customer enters service, we generate their departure time.
        # When a departure happens, we decrement num_servers_busy.
        # If there are waiting customers, one moves to service immediately.
        
        # To manage events efficiently without a heap library (standard lib only), 
        # we can use a simple list and find min, or since we process sequentially, 
        # we can maintain a sorted list of next event times? 
        # Actually, standard approach: 
        # Next Arrival Time: t_arr_next
        # List of Departure Times: dep_times
        
        # Initialize first arrival
        u = rng.random()
        t_arr_next = - (1/lam) * __import__('math').log(u) if u > 0 else 0.0
        
        dep_times = [] # Sorted list of future departure times
        
        # Statistics accumulators for this seed (post-warmup)
        # Area under L(t) curve
        area_L = 0.0
        last_t = 0.0
        last_n = 0
        
        # Busy fraction accumulation
        # We need integral of indicator(num_servers_busy > 0) over time
        # This is equivalent to summing time intervals where system is non-empty? 
        # No, busy_frac defined as 1 - pi_0. pi_0 is prob system empty.
        # So we integrate 1 if n_in_system > 0 else 0.
        area_non_empty = 0.0
        
        # Waiting time accumulation
        # Sum of (departure_time - arrival_time) for all completed services in window
        sum_wait_times = 0.0
        count_completed = 0
        
        # Counts
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_count = 0 # Customers who had to wait (arrived when all servers busy)
        
        # Simulation loop
        while t < H_horizon:
            # Determine next event time
            # Candidates: t_arr_next, min(dep_times) if any
            
            next_dep = min(dep_times) if dep_times else float('inf')
            next_event = min(t_arr_next, next_dep)
            
            if next_event >= H_horizon:
                # Process remaining time until horizon
                dt = H_horizon - t
                if t >= warmup_time:
                    # Accumulate areas
                    # Current state is n_in_system, num_servers_busy
                    # Area L += n * dt
                    # Area NonEmpty += (1 if n>0 else 0) * dt
                    area_L += n_in_system * dt
                    if n_in_system > 0:
                        area_non_empty += dt
                break
            
            # Advance time
            dt = next_event - t
            if t >= warmup_time:
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_non_empty += dt
            
            t = next_event
            
            # Handle Event
            if abs(t - t_arr_next) < 1e-9:
                # Arrival
                arr_count += 1
                
                # Check if blocked
                if n_in_system >= K:
                    blk_count += 1
                else:
                    # Enter system
                    n_in_system += 1
                    
                    # Check if server available
                    if num_servers_busy < c:
                        # Start service immediately
                        num_servers_busy += 1
                        # Generate service time
                        u_s = rng.random()
                        svc_time = - (1/mu) * __import__('math').log(u_s) if u_s > 0 else 0.0
                        dep_time = t + svc_time
                        dep_times.append(dep_time)
                        # Note: Customer did NOT wait
                    else:
                        # Must wait
                        wait_count += 1
                        # Store arrival time for this customer? 
                        # Problem: We don't track individual customers easily in this aggregate view.
                        # To calculate W, we need sum(departure - arrival).
                        # With M/M/c, FIFO discipline is assumed unless stated otherwise.
                        # We need to know which arrival corresponds to which departure.
                        # Simple approach: Keep a queue of arrival times for waiting customers.
                        # And a list of "in-service" customers' arrival times? 
                        # Actually, easier: 
                        # Maintain a queue `wait_queue` of arrival times.
                        # When a server becomes free, pop from `wait_queue`, assign new departure time.
                        # But we already generated departure times upon entry to service.
                        # Correction: Service time starts when they ENTER SERVICE, not when they ARRIVE.
                        # So, if they wait, we don't generate departure time yet.
                        
                        # Revised Logic:
                        # 1. On Arrival:
                        #    If blocked: record block.
                        #    Else: add to `n_in_system`.
                        #    If `num_servers_busy < c`:
                        #       `num_servers_busy++`
                        #       Generate SVC time. Add DEP time to `dep_times`.
                        #       Record that this customer started service at `t`. 
                        #       We need to link this departure to an arrival time to compute wait.
                        #       If they didn't wait, wait=0.
                        #    Else:
                        #       Add arrival time `t` to `wait_queue`.
                
                # Re-implementing the arrival handling inside the loop properly requires restructuring slightly.
                # Let's restart the inner logic design.
                
                # State:
                # n_in_system
                # num_servers_busy
                # dep_times: list of (time, arrival_time_of_customer_being_served)? 
                # No, dep_times just needs to trigger the event. 
                # When a dep event occurs, we know a customer leaves. 
                # Which customer? The one whose service finished. 
                # If we use FIFO, the customer leaving is the one who entered service earliest among those still in service? 
                # No, service times are independent. 
                # Standard M/M/c simulation:
                # Queue Q holds arrival times of waiting customers.
                # Servers hold (start_service_time, expected_end_time). 
                # But we don't need start_service_time if we just want W. 
                # W = Departure_Time - Arrival_Time.
                # So we need to associate each departure with its original arrival time.
                
                # Let's maintain:
                # `waiting_customers`: deque/list of arrival times.
                # `serving_customers`: list of tuples (arrival_time, departure_time).
                # `dep_times`: derived from serving_customers for event scheduling.
                
                # This is getting complex for a "no class" constraint. 
                # Alternative: 
                # Just store arrival times in a global list `all_arrivals`? No, memory leak.
                
                # Let's refine the event handler.
                
                # Variables needed outside loop:
                # wait_q = [] # List of arrival times for waiting customers
                # serv_list = [] # List of [arrival_time, departure_time] for customers currently in service
                
                # Initialization before loop:
                # wait_q = []
                # serv_list = []
                # dep_times = [] # Cache for sorting/min finding? 
                # Actually, we can just scan serv_list for min departure time each step? O(N) per step. Acceptable for small sims.
                
                # Let's rewrite the loop body carefully.
                
                # ... (Previous code aborted mid-thought) ...
                
                # Resetting implementation strategy for clarity within constraints.
                
                # I will re-write the whole function cleanly.
                
                pass 

    # Due to complexity of inline rewriting, I will provide the clean final code below.
    
    # Helper to get log safely
    import math
    
    def exp_rand(rng, rate):
        u = rng.random()
        return -math.log(u) / rate if u > 0 else 0.0

    results = {
        "L": 0.0, "W": 0.0, "busy_frac": 0.0, "p_loss": 0.0,
        "runtime_units": "hours", "seed_list": [], "seeds_used": 0,
        "time_unit": "hour", "win": 0.0,
        "arr": 0.0, "blk": 0.0, "busy_util": 0.0, "dep": 0.0, "dep_rate": 0.0,
        "lam_eff": 0.0, "p_wait": 0.0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    # Re-run logic properly
    total_stats = {"L_area":0, "W_sum":0, "BusyArea":0, "Arr":0, "Blk":0, "Dep":0, "WaitCnt":0, "ServUtilSum":0}
    
    for i in range(N_seeds):
        seed_val = S_start + i
        rng = random.Random(seed_val)
        
        t = 0.0
        n_sys = 0
        n_serv = 0
        
        # Queues
        wait_q = [] # arrival times
        serv_q = [] # list of dicts {'arr': t_arr, 'dep': t_dep}
        
        # Stats accumulators for this seed
        s_L_area = 0.0
        s_BusyArea = 0.0 # Integral of 1(n_sys > 0)
        s_W_sum = 0.0
        s_Arr = 0
        s_Blk = 0
        s_Dep = 0
        s_WaitCnt = 0 # Count of arrivals that joined wait_q
        s_ServUtilSum = 0.0 # Integral of n_serv
        
        # Initial arrival
        t_arr_next = exp_rand(rng, lam)
        
        while t < H_horizon:
            # Find next event
            next_dep = min([x['dep'] for x in serv_q]) if serv_q else float('inf')
            next_ev = min(t_arr_next, next_dep)
            
            if next_ev >= H_horizon:
                dt = H_horizon - t
                if t >= warmup_time:
                    s_L_area += n_sys * dt
                    if n_sys > 0: s_BusyArea += dt
                    s_ServUtilSum += n_serv * dt
                break
            
            dt = next_ev - t
            if t >= warmup_time:
                s_L_area += n_sys * dt
                if n_sys > 0: s_BusyArea += dt
                s_ServUtilSum += n_serv * dt
            
            t = next_ev
            
            if abs(t - t_arr_next) < 1e-9:
                # Arrival
                s_Arr += 1
                if n_sys >= K:
                    s_Blk += 1
                else:
                    n_sys += 1
                    if n_serv < c:
                        n_serv += 1
                        d_time = exp_rand(rng, mu)
                        serv_q.append({'arr': t, 'dep': t + d_time})
                    else:
                        wait_q.append(t)
                        s_WaitCnt += 1
                
                # Schedule next arrival
                t_arr_next = t + exp_rand(rng, lam)
                
            else:
                # Departure
                # Find the customer departing now
                # There might be multiple if ties, but continuous dist makes ties rare.
                # Remove one with dep == t
                idx = -1
                for j, cust in enumerate(serv_q):
                    if abs(cust['dep'] - t) < 1e-9:
                        idx = j
                        break
                
                if idx != -1:
                    cust = serv_q.pop(idx)
                    n_serv -= 1
                    n_sys -= 1
                    s_Dep += 1
                    
                    # Calculate wait time for this customer
                    # W = Dep - Arr
                    w_time = t - cust['arr']
                    if t >= warmup_time:
                        s_W_sum += w_time
                    
                    # If someone is waiting, move them to service
                    if wait_q:
                        arr_time = wait_q.pop(0)
                        n_serv += 1
                        d_time = exp_rand(rng, mu)
                        serv_q.append({'arr': arr_time, 'dep': t + d_time})
                
                # Update next dep cache implicitly by scanning serv_q next loop iteration
        
        # End of Seed Loop
        
        win_len = H_horizon - warmup_time
        if win_len <= 0: win_len = 1e-9
        
        # Per-seed stats
        p_L = s_L_area / win_len
        p_W = (s_W_sum / s_Dep) * 60.0 if s_Dep > 0 else 0.0 # Convert hours to minutes
        p_BusyFrac = s_BusyArea / win_len
        p_Ploss = s_Blk / s_Arr if s_Arr > 0 else 0.0
        p_Pwait = s_WaitCnt / s_Arr if s_Arr > 0 else 0.0
        p_Util = s_ServUtilSum / (win_len * c) if c > 0 else 0.0
        
        per_seed_L.append(p_L)
        per_seed_W.append(p_W)
        per_seed_busy_frac.append(p_BusyFrac)
        per_seed_p_loss.append(p_Ploss)
        per_seed_p_wait.append(p_Pwait)
        
        # Accumulate for global average
        total_stats["L_area"] += s_L_area
        total_stats["W_sum"] += s_W_sum
        total_stats["BusyArea"] += s_BusyArea
        total_stats["Arr"] += s_Arr
        total_stats["Blk"] += s_Blk
        total_stats["Dep"] += s_Dep
        total_stats["WaitCnt"] += s_WaitCnt
        total_stats["ServUtilSum"] += s_ServUtilSum

    seeds_used = N_seeds
    total_win = seeds_used * (H_horizon - warmup_time)
    
    # Global Averages
    g_L = total_stats["L_area"] / total_win if total_win > 0 else 0
    g_W = (total_stats["W_sum"] / total_stats["Dep"]) * 60.0 if total_stats["Dep"] > 0 else 0
    g_BusyFrac = total_stats["BusyArea"] / total_win if total_win > 0 else 0
    g_Ploss = total_stats["Blk"] / total_stats["Arr"] if total_stats["Arr"] > 0 else 0
    g_Pwait = total_stats["WaitCnt"] / total_stats["Arr"] if total_stats["Arr"] > 0 else 0
    g_Util = total_stats["ServUtilSum"] / (total_win * c) if c > 0 else 0
    
    # Derived metrics
    avg_arr_per_seed = total_stats["Arr"] / seeds_used
    avg_blk_per_seed = total_stats["Blk"] / seeds_used
    avg_dep_per_seed = total_stats["Dep"] / seeds_used
    dep_rate = avg_dep_per_seed / (H_horizon - warmup_time) if (H_horizon - warmup_time) > 0 else 0
    lam_eff = dep_rate # Effective arrival rate equals departure rate in steady state
    
    results.update({
        "L": round(g_L, 6),
        "W": round(g_W, 6),
        "busy_frac": round(g_BusyFrac, 6),
        "p_loss": round(g_Ploss, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(H_horizon - warmup_time, 6),
        "arr": round(avg_arr_per_seed, 6),
        "blk": round(avg_blk_per_seed, 6),
        "busy_util": round(g_Util, 6),
        "dep": round(avg_dep_per_seed, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(g_Pwait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    })
    
    print(json.dumps(results))

if __name__ == "__main__":
    main()
