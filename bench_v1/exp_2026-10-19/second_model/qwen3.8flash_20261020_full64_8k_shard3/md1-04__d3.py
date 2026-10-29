import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    N_seeds = a.seeds
    H = a.horizon
    seed_start = a.seed_start
    pert = a.pert
    
    lam_base = 6.0
    mu_base = 12.0
    c = 1
    
    if pert == "lam_up":
        lam = lam_base * 1.2
    elif pert == "mu_up":
        mu = mu_base * 1.2
    elif pert == "c_up":
        c = 2
        mu = mu_base
        lam = lam_base
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = "hour"
    service_time_fixed = 5.0 / 60.0
    
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
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
        n_in_sys = 0
        busy_until = 0.0
        arrivals = []
        departures = []
        
        next_arrival = rng.expovariate(lam)
        
        area_n = 0.0
        total_service_time = 0.0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked_window = 0
        
        prev_t = 0.0
        prev_n = 0
        
        while t < H:
            events = []
            if next_arrival is not None and next_arrival <= H:
                events.append(("arr", next_arrival))
            if busy_until > t and busy_until <= H:
                events.append(("dep", busy_until))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - prev_t
            if prev_t >= H * warmup_frac:
                area_n += prev_n * dt
            
            if etype == "arr":
                t = etime
                if prev_t >= H * warmup_frac:
                    num_arrivals_window += 1
                
                if n_in_sys < c:
                    n_in_sys += 1
                    st = service_time_fixed
                    dep_time = t + st
                    if dep_time <= H:
                        departures.append(dep_time)
                        if busy_until < dep_time:
                            busy_until = dep_time
                    else:
                        pass
                    arrivals.append((t, dep_time))
                else:
                    if prev_t >= H * warmup_frac:
                        num_blocked_window += 1
                
                next_arrival = t + rng.expovariate(lam)
                if next_arrival > H:
                    next_arrival = None
            else:
                t = etime
                if n_in_sys > 0:
                    n_in_sys -= 1
                    if prev_t >= H * warmup_frac:
                        num_departures_window += 1
                
                if departures:
                    min_dep = min(departures)
                    if min_dep <= H:
                        busy_until = min_dep
                    else:
                        busy_until = float('inf')
                else:
                    busy_until = float('inf')
            
            prev_t = t
            prev_n = n_in_sys
        
        if prev_t < H:
            dt = H - prev_t
            if prev_t >= H * warmup_frac:
                area_n += prev_n * dt
        
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = (area_n / num_departures_window) if num_departures_window > 0 else 0.0
        busy_frac_est = area_n / win_len if win_len > 0 else 0.0
        p_loss_est = num_blocked_window / num_arrivals_window if num_arrivals_window > 0 else 0.0
        p_wait_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(num_arrivals_window)
        all_dep.append(num_departures_window)
        all_blk.append(num_blocked_window)
        seeds_used_list.append(s)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    
    dep_rate = avg_dep / win_len * 3600.0 if win_len > 0 else 0.0
    lam_eff = dep_rate / 60.0 if win_len > 0 else 0.0
    
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W * 60.0, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x * 60.0, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
