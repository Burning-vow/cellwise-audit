import sys, json, random, math

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    N = a.seeds
    H = float(a.horizon)
    S = a.seed_start
    pert = a.pert
    
    lam_base = 4.0
    mu_base = 10.0
    c_base = 0.0
    
    if pert == "lam_up":
        lam = lam_base * 1.2
    elif pert == "mu_up":
        mu = mu_base * 1.2
    elif pert == "c_up":
        c = c_base + 1.0
    else:
        lam = lam_base
        mu = mu_base
        c = c_base
    
    time_unit = "hour"
    horizon_hours = H
    warmup_frac = 0.25
    warmup_end = horizon_hours * (1 - warmup_frac)
    win_len = horizon_hours - warmup_end
    
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
    seed_list = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        service_end1 = None
        service_end2 = None
        
        total_wip_area = 0.0
        last_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_time_sum = 0.0
        busy1_time = 0.0
        busy2_time = 0.0
        last_busy1_t = 0.0
        last_busy2_t = 0.0
        
        events = []
        
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        
        add_event(next_arr, 'arr')
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            ev = events.pop(0)
            t = ev[0]
            typ = ev[1]
            
            if t > horizon_hours:
                break
            
            wip_now = len(queue1) + len(queue2) + (1 if busy1 else 0) + (1 if busy2 else 0)
            dt = t - last_t
            if last_t < warmup_end and t > warmup_end:
                split_dt = warmup_end - last_t
                total_wip_area += wip_now * split_dt
                remaining = dt - split_dt
                if remaining > 0:
                    total_wip_area += wip_now * remaining
            elif t <= warmup_end:
                pass
            else:
                total_wip_area += wip_now * dt
            last_t = t
            
            if typ == 'arr':
                arr_count += 1
                proc_time = rng.expovariate(mu) / 60.0
                item = {'proc_time': proc_time, 'arrival_time': t}
                if not busy1:
                    busy1 = True
                    service_end1 = t + proc_time
                    add_event(service_end1, 'srv1_done', item)
                else:
                    queue1.append(item)
                next_arr_t = t + rng.expovariate(lam)
                if next_arr_t <= horizon_hours:
                    add_event(next_arr_t, 'arr')
                    
            elif typ == 'srv1_done':
                item = ev[2]
                busy1 = False
                if queue1:
                    nxt = queue1.pop(0)
                    busy1 = True
                    service_end1 = t + nxt['proc_time']
                    add_event(service_end1, 'srv1_done', nxt)
                if not busy2:
                    busy2 = True
                    service_end2 = t + item['proc_time']
                    add_event(service_end2, 'srv2_done', item)
                else:
                    queue2.append(item)
                    
            elif typ == 'srv2_done':
                item = ev[2]
                busy2 = False
                if queue2:
                    nxt = queue2.pop(0)
                    busy2 = True
                    service_end2 = t + nxt['proc_time']
                    add_event(service_end2, 'srv2_done', nxt)
                dep_count += 1
                stay = t - item['arrival_time']
                if item['arrival_time'] >= warmup_end:
                    wait_time_sum += stay
                    
            elif typ == 'blk':
                blk_count += 1
                
        L_est = total_wip_area / win_len if win_len > 0 else 0.0
        W_est = wait_time_sum / dep_count if dep_count > 0 else 0.0
        W_min = W_est * 60.0
        busy_frac_est = (busy1_time + busy2_time) / (2 * win_len) if win_len > 0 else 0.0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_min)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        seed_list.append(seed)
    
    seeds_used = len(per_seed_L)
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0.0
    avg_busy = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used > 0 else 0.0
    avg_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0.0
    avg_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0.0
    avg_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0.0
    dep_rate = avg_dep / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_frac": round(avg_busy, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
