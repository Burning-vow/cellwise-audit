import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 12.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seeds_used = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        n = 0
        last_event_time = 0.0
        area_n = 0.0
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_service_time_sum = 0.0
        num_served_in_window = 0
        
        next_arrival = rng.expovariate(lam)
        service_times = []
        departure_events = []
        
        while t < horizon:
            next_departure = min(departure_events) if departure_events else float('inf')
            
            if next_arrival <= next_departure and next_arrival < horizon:
                dt = next_arrival - t
                if t >= warmup_end:
                    area_n += n * dt
                t = next_arrival
                
                if n < 1:
                    st = 1.0 / mu
                    service_times.append(st)
                    dep_time = t + st
                    departure_events.append(dep_time)
                    n += 1
                    if t >= warmup_end:
                        arrivals_in_window += 1
                        total_service_time_sum += st
                        num_served_in_window += 1
                else:
                    if t >= warmup_end:
                        blocked_in_window += 1
                        arrivals_in_window += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif next_departure < horizon and next_departure != float('inf'):
                dt = next_departure - t
                if t >= warmup_end:
                    area_n += n * dt
                t = next_departure
                
                if departure_events:
                    departure_events.remove(next_departure)
                    n -= 1
                    if t >= warmup_end:
                        departures_in_window += 1
                        
            else:
                break
        
        win_len = horizon - warmup_end
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = total_service_time_sum / num_served_in_window if num_served_in_window > 0 else 0.0
        busy_frac_est = area_n / win_len if win_len > 0 else 0.0
        p_loss_est = blocked_in_window / arrivals_in_window if arrivals_in_window > 0 else 0.0
        p_wait_est = 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals_in_window)
        all_dep.append(departures_in_window)
        all_blk.append(blocked_in_window)
        seeds_used += 1
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": "hour",
        "seed_list": [a.seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
