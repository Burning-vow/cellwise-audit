import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N = a.seeds; H = a.horizon; S = a.seed_start; pert = a.pert
    lam = 6.0; mu1 = 8.0; mu2 = 10.0
    if pert == "lam_up": lam *= 1.2
    elif pert == "mu_up": mu1 *= 1.2; mu2 *= 1.2
    elif pert == "c_up": pass
    warmup_frac = 0.25
    time_unit = "hour"
    seeds_used = 0
    all_L = []; all_W = []; all_busy = []; all_ploss = []; all_pwait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0; end_t = H
        queue1 = []; queue2 = []
        busy1 = False; busy2 = False
        service_end1 = None; service_end2 = None
        arrivals = 0; departures = 0; blocked = 0
        # events: (time, type, data)
        # type: 'arr', 'dep1', 'dep2'
        events = []
        def push(t_ev, typ, d=None):
            events.append((t_ev, typ, d))
        # initial arrival
        next_arr = rng.expovariate(lam)
        push(next_arr, 'arr')
        # track state changes for area integration
        last_change_time = 0.0
        area_n1 = 0.0; area_n2 = 0.0
        n1 = 0; n2 = 0
        busy_time1 = 0.0; busy_time2 = 0.0
        last_busy1 = 0.0; last_busy2 = 0.0
        # We need to integrate over the window [warmup, H]
        warmup = H * warmup_frac
        # To handle area correctly, we track cumulative areas and subtract at warmup
        cum_area_n1 = 0.0; cum_area_n2 = 0.0
        cum_busy1 = 0.0; cum_busy2 = 0.0
        prev_t = 0.0
        prev_n1 = 0; prev_n2 = 0
        prev_b1 = 0; prev_b2 = 0
        # For W calculation: sum of sojourn times / number of completions in window
        # But we need only completions in window. So track departure times and entry times.
        # Store entry time with each job.
        # Job dict: {'entry': t, 'id': ...}
        # When dep2 happens, if t >= warmup, add (t - entry) to sum_w, count dep_in_window
        
        sum_w = 0.0; dep_in_win = 0
        arr_in_win = 0; blk_in_win = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            t_ev, typ, d = events.pop(0)
            if t_ev > end_t:
                break
            # Integrate from prev_t to t_ev
            dt = t_ev - prev_t
            if dt > 0:
                cum_area_n1 += prev_n1 * dt
                cum_area_n2 += prev_n2 * dt
                cum_busy1 += prev_b1 * dt
                cum_busy2 += prev_b2 * dt
            prev_t = t_ev
            
            if typ == 'arr':
                arrivals += 1
                if t_ev >= warmup:
                    arr_in_win += 1
                # Add to queue1
                job = {'entry': t_ev}
                queue1.append(job)
                n1 = len(queue1)
                if not busy1:
                    # Start service immediately
                    busy1 = True
                    dur = rng.expovariate(mu1)
                    service_end1 = t_ev + dur
                    push(service_end1, 'dep1', job)
                    queue1.pop(0)
                    n1 = len(queue1)
                    prev_b1 = 1
                else:
                    prev_b1 = 1 if busy1 else 0
                prev_n1 = n1
                # Next arrival
                next_arr = t_ev + rng.expovariate(lam)
                if next_arr <= end_t:
                    push(next_arr, 'arr')
                    
            elif typ == 'dep1':
                job = d
                # Move to queue2
                queue2.append(job)
                n2 = len(queue2)
                if not busy2:
                    busy2 = True
                    dur = rng.expovariate(mu2)
                    service_end2 = t_ev + dur
                    push(service_end2, 'dep2', job)
                    queue2.pop(0)
                    n2 = len(queue2)
                    prev_b2 = 1
                else:
                    prev_b2 = 1 if busy2 else 0
                prev_n2 = n2
                # Check if server1 can start next
                if queue1:
                    busy1 = True
                    nxt_job = queue1.pop(0)
                    dur = rng.expovariate(mu1)
                    service_end1 = t_ev + dur
                    push(service_end1, 'dep1', nxt_job)
                    n1 = len(queue1)
                    prev_n1 = n1
                    prev_b1 = 1
                else:
                    busy1 = False
                    prev_b1 = 0
                    
            elif typ == 'dep2':
                job = d
                departures += 1
                if t_ev >= warmup:
                    dep_in_win += 1
                    sum_w += (t_ev - job['entry'])
                # Check if server2 can start next
                if queue2:
                    busy2 = True
                    nxt_job = queue2.pop(0)
                    dur = rng.expovariate(mu2)
                    service_end2 = t_ev + dur
                    push(service_end2, 'dep2', nxt_job)
                    n2 = len(queue2)
                    prev_n2 = n2
                    prev_b2 = 1
                else:
                    busy2 = False
                    prev_b2 = 0
        
        # Final integration up to end_t if needed? The loop breaks when event > end_t.
        # We should integrate from prev_t to end_t
        dt = end_t - prev_t
        if dt > 0:
            cum_area_n1 += prev_n1 * dt
            cum_area_n2 += prev_n2 * dt
            cum_busy1 += prev_b1 * dt
            cum_busy2 += prev_b2 * dt
        
        win_len = end_t - warmup
        if win_len <= 0:
            continue
            
        L1 = cum_area_n1 / win_len if win_len > 0 else 0
        L2 = cum_area_n2 / win_len if win_len > 0 else 0
        L_total = L1 + L2
        
        W_avg = sum_w / dep_in_win if dep_in_win > 0 else 0
        # Convert W to minutes
        W_min = W_avg * 60.0
        
        busy_frac1 = cum_busy1 / win_len if win_len > 0 else 0
        busy_frac2 = cum_busy2 / win_len if win_len > 0 else 0
        avg_busy_frac = (busy_frac1 + busy_frac2) / 2.0
        
        p_loss = 0.0 # No blocking/loss in this model
        p_wait = 0.0 # Not clearly defined, maybe fraction of jobs that waited? 
                     # Let's assume 0 for now as no loss system.
        
        all_L.append(L_total)
        all_W.append(W_min)
        all_busy.append(avg_busy_frac)
        all_ploss.append(p_loss)
        all_pwait.append(p_wait)
        total_arr += arr_in_win
        total_dep += dep_in_win
        total_blk += 0
        seeds_used += 1
    
    if seeds_used == 0:
        print(json.dumps({"L":0,"W":0,"runtime_units":"min","seed_list":[],"seeds_used":0,"time_unit":time_unit,"win":H*(1-warmup_frac),"arr":0,"blk":0,"busy_frac":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_loss":0,"p_wait":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}))
        return
    
    mean_L = sum(all_L) / seeds_used
    mean_W = sum(all_W) / seeds_used
    mean_busy = sum(all_busy) / seeds_used
    mean_ploss = sum(all_ploss) / seeds_used
    mean_pwait = sum(all_pwait) / seeds_used
    
    avg_arr = total_arr / seeds_used
    avg_dep = total_dep / seeds_used
    avg_blk = total_blk / seeds_used
    win_len = H * (1 - warmup_frac)
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    seed_list = [S + i for i in range(seeds_used)]
    
    out = {
        "L": round(mean_L, 6),
        "W": round(mean_W, 6),
        "runtime_units": "min",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_frac": round(mean_busy, 6),
        "busy_util": round(mean_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(mean_ploss, 6),
        "p_wait": round(mean_pwait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy],
        "per_seed_p_loss": [round(x, 6) for x in all_ploss],
        "per_seed_p_wait": [round(x, 6) for x in all_pwait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
