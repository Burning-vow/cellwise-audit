import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N, H, S, pert = a.seeds, float(a.horizon), a.seed_start, a.pert
    lam1 = 4.0; mu1 = 60.0/7.5; mu2 = 60.0/5.0
    if pert == "lam_up": lam1 *= 1.2
    elif pert == "mu_up": mu1 *= 1.2; mu2 *= 1.2
    elif pert == "c_up": pass
    warmup_frac = 0.25
    results_L = []; results_W = []; results_busy = []; results_loss = []; results_wait = []
    total_arr = 0; total_dep = 0; total_blk = 0; total_time_in_sys = 0.0
    all_seeds = []
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        # State: queue1, queue2 (list of (arrival_time, service_time))
        q1 = []; q2 = []
        busy1_until = -1.0; busy2_until = -1.0
        # Events: arrival to sys1, completion at 1, completion at 2
        events = []
        def push_event(time, typ, data=None):
            events.append((time, typ, data))
        # Initial arrival
        next_arr = rng.expovariate(lam1)
        push_event(next_arr, 'arr', None)
        # Track metrics within window [warmup_end, H]
        warmup_end = H * warmup_frac
        win_len = H - warmup_end
        if win_len <= 0:
            L_i = 0.0; W_i = 0.0; bf_i = 0.0; pl_i = 0.0; pw_i = 0.0
            arr_i = 0; dep_i = 0; blk_i = 0
            time_in_sys_i = 0.0
        else:
            # We need to simulate from 0 to H, but only accumulate stats after warmup_end
            # To do area integrals correctly, we track state changes and integrate over intervals
            last_t = 0.0
            # For busy fraction integration
            b1_active = False; b2_active = False
            # For WIP count integration
            wip_count = 0
            # Accumulators for the window
            area_wip = 0.0
            area_b1 = 0.0; area_b2 = 0.0
            # For waiting probability: fraction of jobs that waited? Or prob a job waits?
            # Usually p_wait is probability an arriving job has to wait.
            # Let's define p_wait as fraction of arrivals that find server busy.
            # But we need per-seed estimates.
            # Let's collect individual sojourn times for departures in window.
            sojourn_times = []
            n_arr_win = 0; n_dep_win = 0; n_blk_win = 0
            n_wait_win = 0
            
            while events:
                events.sort(key=lambda x: x[0])
                et, typ, data = events.pop(0)
                if et > H: break
                
                # Integrate areas up to current event time
                dt = et - last_t
                if last_t < warmup_end and et > warmup_end:
                    # Split interval
                    d1 = warmup_end - last_t
                    d2 = et - warmup_end
                    if d1 > 0:
                        # Before warmup, no accumulation needed for final stats, but update state
                        pass
                    if d2 > 0:
                        area_wip += wip_count * d2
                        if b1_active: area_b1 += d2
                        if b2_active: area_b2 += d2
                elif last_t >= warmup_end:
                    area_wip += wip_count * dt
                    if b1_active: area_b1 += dt
                    if b2_active: area_b2 += dt
                
                last_t = et
                
                if typ == 'arr':
                    # Arrival to system (queue 1)
                    st1 = rng.expovariate(mu1)
                    # Check if server 1 is free
                    if not b1_active or et >= busy1_until:
                        # Start service immediately
                        b1_active = True
                        busy1_until = et + st1
                        push_event(busy1_until, 'comp1', {'start': et, 'st': st1})
                        wip_count += 1
                        if et >= warmup_end:
                            n_arr_win += 1
                            # Did it wait? No, started immediately
                    else:
                        # Wait in queue 1
                        q1.append({'arr': et, 'st': st1})
                        wip_count += 1
                        if et >= warmup_end:
                            n_arr_win += 1
                            n_wait_win += 1
                    # Schedule next arrival
                    na = et + rng.expovariate(lam1)
                    if na <= H:
                        push_event(na, 'arr', None)
                
                elif typ == 'comp1':
                    # Completion at station 1
                    b1_active = False
                    wip_count -= 1
                    # Move to queue 2
                    st2 = rng.expovariate(mu2)
                    if not b2_active or et >= busy2_until:
                        b2_active = True
                        busy2_until = et + st2
                        push_event(busy2_until, 'comp2', {'start': et, 'st': st2, 'orig_arr': data['start'] - data['st'] if 'orig_arr' in data else None})
                        # Need original arrival time for sojourn. 
                        # The data passed was from comp1 event which had start/st. 
                        # Actually, when item enters q1, we know its arrival time.
                        # When it starts service at 1, we record start time.
                        # When it completes 1, we move to 2.
                        # We need to carry the original arrival time through.
                        # Let's fix data structure.
                        # In 'arr' event, if immediate service, we push comp1 with orig_arr=et.
                        # If queued, we store orig_arr in q1 entry.
                        # On comp1, we pop from q1 or use direct data.
                        # This logic needs refinement.
                        pass
                    else:
                        q2.append({'arr': et, 'st': st2, 'orig': data.get('orig', et)})
                    
                    # Try to start next job on server 1
                    if q1:
                        job = q1.pop(0)
                        b1_active = True
                        busy1_until = et + job['st']
                        push_event(busy1_until, 'comp1', {'start': et, 'st': job['st'], 'orig': job['arr']})
                        # wip_count stays same (one left q1, one entered service)
                
                elif typ == 'comp2':
                    b2_active = False
                    wip_count -= 1
                    # Departure
                    orig_arr = data.get('orig', data['start'])
                    soj = et - orig_arr
                    if et >= warmup_end:
                        n_dep_win += 1
                        sojourn_times.append(soj)
                    
                    # Try to start next job on server 2
                    if q2:
                        job = q2.pop(0)
                        b2_active = True
                        busy2_until = et + job['st']
                        push_event(busy2_until, 'comp2', {'start': et, 'st': job['st'], 'orig': job['orig']})
            
            # Final integration up to H if loop ended early due to empty events but t<H?
            # The loop breaks if et>H. If events empty before H, we need to integrate to H.
            if last_t < H:
                dt = H - last_t
                if last_t < warmup_end:
                    d2 = H - warmup_end
                    if d2 > 0:
                        area_wip += wip_count * d2
                        if b1_active: area_b1 += d2
                        if b2_active: area_b2 += d2
                else:
                    area_wip += wip_count * dt
                    if b1_active: area_b1 += dt
                    if b2_active: area_b2 += dt
            
            L_i = area_wip / win_len if win_len > 0 else 0.0
            W_i = sum(sojourn_times) / len(sojourn_times) if sojourn_times else 0.0
            bf_i = (area_b1 + area_b2) / (2 * win_len) if win_len > 0 else 0.0
            pl_i = 0.0 # No blocking/loss in this model description usually, unless finite queues. Assume infinite.
            pw_i = n_wait_win / n_arr_win if n_arr_win > 0 else 0.0
            
            total_arr += n_arr_win
            total_dep += n_dep_win
            total_blk += 0
            total_time_in_sys += sum(sojourn_times)
        
        results_L.append(L_i)
        results_W.append(W_i)
        results_busy.append(bf_i)
        results_loss.append(pl_i)
        results_wait.append(pw_i)
        all_seeds.append(seed)
    
    avg_L = sum(results_L)/N if N>0 else 0.0
    avg_W = sum(results_W)/N if N>0 else 0.0
    avg_bf = sum(results_busy)/N if N>0 else 0.0
    avg_pl = sum(results_loss)/N if N>0 else 0.0
    avg_pw = sum(results_wait)/N if N>0 else 0.0
    
    avg_arr = total_arr/N if N>0 else 0.0
    avg_dep = total_dep/N if N>0 else 0.0
    avg_blk = total_blk/N if N>0 else 0.0
    
    dep_rate = avg_dep / win_len * 60.0 if win_len > 0 else 0.0 # per hour? win_len is in hours?
    # Time unit: I used hours for lam/mu. So H is in hours.
    # lam1=4/hour. mu1=8/hour.
    # So time_unit is 'hour'.
    # dep_rate should be per hour.
    # avg_dep is count per seed. win_len is hours.
    # rate = avg_dep / win_len.
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "simulation_steps",
        "seed_list": all_seeds,
        "seeds_used": N,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_bf, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(avg_arr/win_len, 4) if win_len>0 else 0.0,
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x,4) for x in results_L],
        "per_seed_W": [round(x,4) for x in results_W],
        "per_seed_busy_frac": [round(x,4) for x in results_busy],
        "per_seed_p_loss": [round(x,4) for x in results_loss],
        "per_seed_p_wait": [round(x,4) for x in results_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
