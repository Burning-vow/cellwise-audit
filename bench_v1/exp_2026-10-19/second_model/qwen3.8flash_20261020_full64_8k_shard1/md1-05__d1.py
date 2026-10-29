import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0 # per hour
    mu_service_time_min = 6.0
    service_time_hr = mu_service_time_min / 60.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        lam = lam_base
        service_time_hr = service_time_hr / 1.2
    elif pert == 'c_up':
        lam = lam_base
        service_time_hr = mu_service_time_min / 60.0
    else:
        lam = lam_base
        
    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occ = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        queue = [] 
        server_free_t = 0.0
        is_server_busy = False
        
        n_in_system_integral = 0.0
        last_event_t = 0.0
        total_arrivals = 0
        total_departures = 0
        total_blocked = 0
        total_wait_time_sum = 0.0
        total_stay_time_sum = 0.0
        busy_time_integral = 0.0
        occupied_time_integral = 0.0
        
        while t < H:
            if not queue and (not is_server_busy or server_free_t > H):
                break
                
            next_dep_t = float('inf')
            if is_server_busy:
                next_dep_t = server_free_t
            
            next_arr_t_val = next_arr_t if next_arr_t < H else float('inf')
            
            if next_dep_t <= next_arr_t_val:
                t_next = next_dep_t
            else:
                t_next = next_arr_t_val
                
            if t_next > H:
                t_next = H
                
            dt = t_next - t
            if dt > 0:
                current_n = len(queue) + (1 if is_server_busy else 0)
                if t >= warmup_end:
                    n_in_system_integral += current_n * dt
                    if is_server_busy:
                        busy_time_integral += dt
                        occupied_time_integral += dt
            
            t = t_next
            
            if t >= H:
                break
                
            if abs(t - next_dep_t) < 1e-9:
                cust = queue.pop(0)
                dep_time = t
                stay_time = dep_time - cust['arrival_time']
                wait_time = dep_time - cust['service_start_time']
                
                if t >= warmup_end:
                    total_departures += 1
                    total_stay_time_sum += stay_time
                    total_wait_time_sum += wait_time
                    
                is_server_busy = False
                server_free_t = 0.0
                
                if queue:
                    pass 
                else:
                    is_server_busy = False
                    server_free_t = 0.0
                    
                if queue:
                     pass
                else:
                    if next_arr_t > t:
                         is_server_busy = False
                         server_free_t = 0.0
                    else:
                         is_server_busy = False
                         server_free_t = 0.0
                         
                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0
                    
                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server_busy = False
                    server_free_t = 0.0

                if queue:
                    pass
                else:
                    is_server
