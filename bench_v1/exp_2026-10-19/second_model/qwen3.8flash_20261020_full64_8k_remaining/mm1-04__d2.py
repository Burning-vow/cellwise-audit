import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 6.0, 12.0
    if a.pert == "lam_up": lam_base *= 1.1
    elif a.pert == "mu_up": mu_base *= 1.1
    elif a.pert == "c_up": pass
    time_unit = "hour"
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk, total_time_in_sys, total_busy_time, total_wait_time, total_customers_served = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        n_in_sys = 0
        area_n = 0.0
        last_event_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        custs_served = 0
        sum_w = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        while t < horizon:
            if not queue and service_end is None:
                ev_t = next_arr
                ev_type = 'arr'
            else:
                ev_arr = next_arr
                ev_dep = service_end if service_end is not None else float('inf')
                if ev_arr <= ev_dep:
                    ev_t = ev_arr
                    ev_type = 'arr'
                else:
                    ev_t = ev_dep
                    ev_type = 'dep'
            dt = ev_t - last_event_t
            if last_event_t >= win_start or (last_event_t < win_start and ev_t > win_start):
                overlap_start = max(last_event_t, win_start)
                overlap_end = min(ev_t, horizon)
                if overlap_end > overlap_start:
                    odt = overlap_end - overlap_start
                    area_n += n_in_sys * odt
                    if n_in_sys > 0:
                        busy_time += odt
            if ev_type == 'arr':
                t = ev_t
                if t >= win_start:
                    arr_count += 1
                svc_dur = rng.expovariate(mu_base)
                if n_in_sys == 0 and service_end is None:
                    service_end = t + svc_dur
                    n_in_sys = 1
                    queue.append((t, svc_dur))
                else:
                    n_in_sys += 1
                    queue.append((t, svc_dur))
                next_arr = t + rng.expovariate(lam_base)
            else:
                t = ev_t
                if t >= win_start:
                    dep_count += 1
                if queue:
                    arr_t, dur = queue.pop(0)
                    w = t - arr_t
                    sum_w += w
                    wait_time_sum += w
                    custs_served += 1
                    if len(queue) == 0:
                        service_end = None
                        n_in_sys -= 1
                    else:
                        service_end = t + queue[0][1]
                        n_in_sys -= 1
                else:
                    service_end = None
                    n_in_sys = 0
            last_event_t = t
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = sum_w / custs_served if custs_served > 0 else 0.0
        bf_est = busy_time / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = wait_time_sum / sum_w if sum_w > 0 else 0.0
        # p_wait: fraction of customers who waited? Or probability an arriving customer waits?
        # Typically p_wait = P(wait>0). Let's compute properly.
        # We need to track how many had wait > 0 among those served in window.
        # Re-run logic would be needed, but let's approximate with existing data or fix.
        # Actually, we didn't track count of waiting customers separately.
        # Let's adjust: during dep event, if w > 0 then counted as waited.
        # But we already popped. Let's restructure slightly or use a proxy.
        # For M/M/1, p_wait = rho. But simulation should measure it.
        # I'll add a counter for waited customers.
        pass
    # The above loop has a flaw: p_wait calculation needs number of customers who waited.
    # Let me rewrite the inner loop more carefully within the same structure constraint.
    
    # Reset accumulators for correct implementation
    total_arr, total_dep, total_blk, total_time_in_sys, total_busy_time, total_wait_time, total_customers_served = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        n_in_sys = 0
        area_n = 0.0
        last_event_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        custs_served = 0
        sum_w = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        num_waited = 0
        
        while t < horizon:
            if not queue and service_end is None:
                ev_t = next_arr
                ev_type = 'arr'
            else:
                ev_arr = next_arr
                ev_dep = service_end if service_end is not None else float('inf')
                if ev_arr <= ev_dep:
                    ev_t = ev_arr
                    ev_type = 'arr'
                else:
                    ev_t = ev_dep
                    ev_type = 'dep'
            
            dt = ev_t - last_event_t
            if last_event_t < win_start and ev_t > win_start:
                # Partial integration from win_start to ev_t
                odt = ev_t - win_start
                area_n += n_in_sys * odt
                if n_in_sys > 0:
                    busy_time += odt
            elif last_event_t >= win_start:
                odt = ev_t - last_event_t
                area_n += n_in_sys * odt
                if n_in_sys > 0:
                    busy_time += odt
            
            if ev_type == 'arr':
                t = ev_t
                if t >= win_start:
                    arr_count += 1
                svc_dur = rng.expovariate(mu_base)
                if n_in_sys == 0 and service_end is None:
                    service_end = t + svc_dur
                    n_in_sys = 1
                    queue.append((t, svc_dur))
                else:
                    n_in_sys += 1
                    queue.append((t, svc_dur))
                next_arr = t + rng.expovariate(lam_base)
            else:
                t = ev_t
                if t >= win_start:
                    dep_count += 1
                if queue:
                    arr_t, dur = queue.pop(0)
                    w = t - arr_t
                    if t >= win_start:
                        sum_w += w
                        wait_time_sum += w
                        custs_served += 1
                        if w > 0:
                            num_waited += 1
                    if len(queue) == 0:
                        service_end = None
                        n_in_sys -= 1
                    else:
                        service_end = t + queue[0][1]
                        n_in_sys -= 1
                else:
                    service_end = None
                    n_in_sys = 0
            last_event_t = t
        
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = sum_w / custs_served if custs_served > 0 else 0.0
        bf_est = busy_time / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = num_waited / custs_served if custs_served > 0 else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_time_in_sys += sum_w
        total_busy_time += busy_time
        total_wait_time += wait_time_sum
        total_customers_served += custs_served
    
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0.0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0.0
    
    arr_avg = total_arr / seeds_used if seeds_used > 0 else 0.0
    dep_avg = total_dep / seeds_used if seeds_used > 0 else 0.0
    blk_avg = total_blk / seeds_used if seeds_used > 0 else 0.0
    dep_rate = dep_avg / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate
    busy_util = avg_bf
    busy_occupied = avg_bf
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W * 60, 6), # Convert hours to minutes
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
