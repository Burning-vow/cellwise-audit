import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 12.0
    c = 1
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    elif a.pert == 'c_up':
        c = 2
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = 0
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_p_loss = []
    all_lam_eff = []
    all_dep_rate = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        in_service = None
        n_in_system = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        
        area_n = 0.0
        area_time = 0.0
        total_sojourn = 0.0
        busy_area = 0.0
        occupied_area = 0.0
        last_event_t = 0.0
        
        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if in_service is not None and in_service[1] <= horizon:
                events.append(('dep', in_service[1]))
            
            if not events:
                break
            
            ev_type, ev_t = min(events, key=lambda x: x[1])
            
            dt = ev_t - last_event_t
            if last_event_t >= win_start or (last_event_t < win_start and ev_t > win_start):
                overlap_start = max(last_event_t, win_start)
                overlap_end = min(ev_t, horizon)
                overlap_dt = overlap_end - overlap_start
                if overlap_dt > 0:
                    area_n += n_in_system * overlap_dt
                    area_time += overlap_dt
                    if n_in_system > 0:
                        busy_area += overlap_dt
                    if in_service is not None:
                        occupied_area += overlap_dt
            
            last_event_t = ev_t
            t = ev_t
            
            if ev_type == 'arr':
                st = rng.expovariate(mu)
                if len(queue) == 0 and in_service is None:
                    in_service = (t, t + st)
                    n_in_system += 1
                    arr_count += 1
                elif in_service is not None:
                    if len(queue) < 10000:
                        queue.append((t, st))
                        n_in_system += 1
                        arr_count += 1
                        wait_count += 1
                    else:
                        blk_count += 1
                next_arr = t + rng.expovariate(lam)
            
            elif ev_type == 'dep':
                if in_service is not None:
                    arrival_t = in_service[0]
                    soj = t - arrival_t
                    if arrival_t >= win_start:
                        total_sojourn += soj
                    dep_count += 1
                    n_in_system -= 1
                    in_service = None
                    if queue:
                        q_item = queue.pop(0)
                        in_service = (q_item[0], t + q_item[1])
                        n_in_system += 1
        
        if seeds_used == 0:
            pass
        
        L_est = area_n / area_time if area_time > 0 else 0.0
        W_est = total_sojourn / dep_count if dep_count > 0 else 0.0
        busy_frac_est = busy_area / area_time if area_time > 0 else 0.0
        p_wait_est = wait_count / arr_count if arr_count > 0 else 0.0
        p_loss_est = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0.0
        busy_util_est = busy_area / (area_time * c) if area_time > 0 else 0.0
        busy_occ_est = occupied_area / area_time if area_time > 0 else 0.0
        lam_eff_est = dep_count / win_len if win_len > 0 else 0.0
        dep_rate_est = dep_count / win_len if win_len > 0 else 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_p_loss.append(p_loss_est)
        all_lam_eff.append(lam_eff_est)
        all_dep_rate.append(dep_rate_est)
        seeds_used += 1
    
    def avg(lst):
        return sum(lst)/len(lst) if lst else 0.0
    
    result = {
        "L": round(avg(all_L), 6),
        "W": round(avg(all_W)*60, 6),
        "busy_frac": round(avg(all_busy_frac), 6),
        "p_wait": round(avg(all_p_wait), 6),
        "runtime_units": time_unit,
        "seed_list": [a.seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg(all_arr), 6),
        "blk": round(avg(all_blk), 6),
        "busy_util": round(avg(all_busy_util), 6),
        "dep": round(avg(all_dep), 6),
        "dep_rate": round(avg(all_dep_rate), 6),
        "lam_eff": round(avg(all_lam_eff), 6),
        "p_loss": round(avg(all_p_loss), 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x*60, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
