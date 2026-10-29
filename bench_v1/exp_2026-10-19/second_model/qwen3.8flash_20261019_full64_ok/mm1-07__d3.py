import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 60.0 / 6.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        custs = [] 
        arr_count = 0
        dep_count = 0
        blk_count = 0
        area_L = 0.0
        area_busy = 0.0
        area_wait = 0.0
        total_time_in_sys = 0.0
        last_event_t = 0.0
        state_N = 0
        is_busy = False
        service_end = None
        
        while t < H:
            events = []
            if next_arr <= H:
                events.append(('arr', next_arr))
            if service_end is not None and service_end <= H:
                events.append(('dep', service_end))
            
            if not events:
                break
                
            ev_type, ev_t = min(events, key=lambda x: x[1])
            
            dt = ev_t - last_event_t
            if last_event_t >= warmup:
                area_L += state_N * dt
                if is_busy:
                    area_busy += dt
            
            t = ev_t
            last_event_t = t
            
            if ev_type == 'arr':
                arr_count += 1
                svc_time = rng.expovariate(mu)
                if state_N == 0:
                    is_busy = True
                    service_end = t + svc_time
                    state_N = 1
                    wait_time = 0.0
                    total_time_in_sys += svc_time
                    if t >= warmup:
                        pass 
                else:
                    custs.append((t, svc_time))
                    state_N += 1
                    if t >= warmup:
                        pass
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                dep_count += 1
                if custs:
                    arr_t, svc_t = custs.pop(0)
                    wait_time = t - arr_t
                    total_time_in_sys += wait_time + svc_t
                    if t >= warmup:
                        area_wait += wait_time
                    service_end = t + svc_t
                    state_N -= 1 
                else:
                    is_busy = False
                    service_end = None
                    state_N = 0
                    
        if last_event_t < H and last_event_t >= warmup:
             dt = H - last_event_t
             area_L += state_N * dt
             if is_busy:
                 area_busy += dt
                 
        L_est = area_L / win if win > 0 else 0
        W_est = (total_time_in_sys / dep_count) if dep_count > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        p_wait_est = (area_wait / win) if win > 0 else 0 
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_blk.append(blk_count)
        all_dep.append(dep_count)
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(0.0)
        per_seed_p_wait.append(p_wait_est)
        seeds_used_list.append(s)
        
    avg_L = sum(all_L)/N_seeds
    avg_W = sum(all_W)/N_seeds
    avg_busy_frac = sum(all_busy_frac)/N_seeds
    avg_p_wait = sum(all_p_wait)/N_seeds
    avg_arr = sum(all_arr)/N_seeds
    avg_blk = sum(all_blk)/N_seeds
    avg_dep = sum(all_dep)/N_seeds
    
    dep_rate = (avg_dep / win) * 1.0 
    lam_eff = dep_rate
    p_loss = avg_blk / avg_arr if avg_arr > 0 else 0.0
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
