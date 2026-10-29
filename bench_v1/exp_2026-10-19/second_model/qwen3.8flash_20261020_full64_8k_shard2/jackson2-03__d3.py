import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    lam_base = 4.0
    mu_base = 10.0
    
    if a.pert == "lam_up":
        lam = lam_base * 1.2
    elif a.pert == "mu_up":
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L_area = []
    all_W_sum = []
    all_arr_count = []
    all_dep_count = []
    all_blk_count = []
    all_busy1_time = []
    all_busy2_time = []
    all_p_loss = []
    all_p_wait = []
    
    time_unit = "hour"
    
    for s_idx in range(seeds_used):
        rng = random.Random(seed_list[s_idx])
        
        t = 0.0
        queue1 = []
        queue2 = []
        busy1_until = -1.0
        busy2_until = -1.0
        
        next_arrival = rng.expovariate(lam)
        
        events = []
        
        def add_event(time, kind, data=None):
            events.append((time, kind, data))
            
        add_event(next_arrival, "arrival", None)
        
        last_state_change_t = 0.0
        area_L = 0.0
        sum_W = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        busy1_total = 0.0
        busy2_total = 0.0
        wait_events = 0
        total_jobs_in_sys_at_entry = 0
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            ev_time, ev_kind, ev_data = events.pop(0)
            
            if ev_time > horizon:
                break
                
            dt = ev_time - last_state_change_t
            
            n1 = len(queue1) + (1 if busy1_until > last_state_change_t else 0)
            n2 = len(queue2) + (1 if busy2_until > last_state_change_t else 0)
            L_current = n1 + n2
            
            if last_state_change_t < win_start and ev_time >= win_start:
                overlap = min(ev_time, horizon) - max(last_state_change_t, win_start)
                if overlap > 0:
                    area_L += L_current * overlap
            elif last_state_change_t >= win_start:
                area_L += L_current * dt
                
            if busy1_until > last_state_change_t:
                b1_overlap = min(busy1_until, ev_time) - max(last_state_change_t, 0)
                if b1_overlap > 0:
                    busy1_total += b1_overlap
            if busy2_until > last_state_change_t:
                b2_overlap = min(busy2_until, ev_time) - max(last_state_change_t, 0)
                if b2_overlap > 0:
                    busy2_total += b2_overlap
                    
            last_state_change_t = ev_time
            
            if ev_kind == "arrival":
                job_id = count_arr
                service_time_1 = rng.expovariate(mu)
                service_time_2 = rng.expovariate(mu)
                
                if ev_time >= win_start:
                    count_arr += 1
                    total_jobs_in_sys_at_entry += n1 + n2
                    if n1 > 0 or busy1_until > ev_time:
                        wait_events += 1
                        
                if busy1_until <= ev_time:
                    busy1_until = ev_time + service_time_1
                    add_event(busy1_until, "service1_done", {"job_id": job_id, "st2": service_time_2})
                else:
                    queue1.append({"job_id": job_id, "st2": service_time_2, "arr_t": ev_time})
                    
                next_arrival = ev_time + rng.expovariate(lam)
                add_event(next_arrival, "arrival", None)
                
            elif ev_kind == "service1_done":
                job_info = ev_data
                jid = job_info["job_id"]
                st2 = job_info["st2"]
                
                if busy2_until <= ev_time:
                    busy2_until = ev_time + st2
                    add_event(busy2_until, "service2_done", {"job_id": jid, "arr_t": None})
                else:
                    queue2.append({"job_id": jid, "st2": st2, "arr_t": None})
                    
            elif ev_kind == "service2_done":
                job_info = ev_data
                jid = job_info["job_id"]
                
                if ev_time >= win_start:
                    count_dep += 1
                    
                if queue1:
                    next_job = queue1.pop(0)
                    busy1_until = ev_time + next_job.get("st1_remaining", 0) 
                    # Wait, we didn't store st1 remaining properly in arrival logic above?
                    # Let's re-evaluate structure.
                    pass

        # Re-implementing loop more carefully to ensure correctness within constraints
        # The previous draft had issues with tracking state across queues correctly for W calculation.
        
        # Reset variables for clean implementation
        rng = random.Random(seed_list[s_idx])
        t = 0.0
        q1 = [] # list of dicts: {id, arr_t, st1, st2}
        q2 = [] # list of dicts: {id, arr_t, st2}
        b1_end = -1.0
        b2_end = -1.0
        
        next_arr = rng.expovariate(lam)
        heap = [(next_arr, 'A', None)]
        
        area_L = 0.0
        sum_W = 0.0
        cnt_A = 0
        cnt_D = 0
        cnt_B = 0
        busy1_acc = 0.0
        busy2_acc = 0.0
        wait_cnt = 0
        last_t = 0.0
        
        import heapq
        
        while heap:
            cur_t, typ, data = heapq.heappop(heap)
            if cur_t > horizon:
                break
            
            dt = cur_t - last_t
            
            # Calculate current system size for area integration
            n1 = len(q1) + (1 if b1_end > last_t else 0)
            n2 = len(q2) + (1 if b2_end > last_t else 0)
            L_val = n1 + n2
            
            # Integrate area only if the interval overlaps with window
            start_int = max(last_t, win_start)
            end_int = min(cur_t, horizon)
            if end_int > start_int:
                area_L += L_val * (end_int - start_int)
                
            # Accumulate busy times
            if b1_end > last_t:
                bs1 = min(b1_end, cur_t) - max(last_t, 0)
                if bs1 > 0: busy1_acc += bs1
            if b2_end > last_t:
                bs2 = min(b2_end, cur_t) - max(last_t, 0)
                if bs2 > 0: busy2_acc += bs2
                
            last_t = cur_t
            
            if typ == 'A':
                st1 = rng.expovariate(mu)
                st2 = rng.expovariate(mu)
                job = {'id': cnt_A, 'arr_t': cur_t, 'st1': st1, 'st2': st2}
                
                if cur_t >= win_start:
                    cnt_A += 1
                    if n1 > 0 or b1_end > cur_t:
                        wait_cnt += 1
                        
                if b1_end <= cur_t:
                    b1_end = cur_t + st1
                    heapq.heappush(heap, (b1_end, 'S1', job))
                else:
                    q1.append(job)
                    
                nxt = cur_t + rng.expovariate(lam)
                heapq.heappush(heap, (nxt, 'A', None))
                
            elif typ == 'S1':
                job = data
                # Move to Q2 or start S2
                if b2_end <= cur_t:
                    b2_end = cur_t + job['st2']
                    heapq.heappush(heap, (b2_end, 'S2', job))
                else:
                    q2.append(job)
                    
                # Start next from Q1 if available
                if q1:
                    nj = q1.pop(0)
                    b1_end = cur_t + nj['st1']
                    heapq.heappush(heap, (b1_end, 'S1', nj))
                    
            elif typ == 'S2':
                job = data
                if cur_t >= win_start:
                    cnt_D += 1
                    w = cur_t - job['arr_t']
                    sum_W += w
                    
                # Start next from Q2 if available
                if q2:
                    nj = q2.pop(0)
                    b2_end = cur_t + nj['st2']
                    heapq.heappush(heap, (b2_end, 'S2', nj))
                    
        # End of simulation for this seed
        
        # Finalize integrals up to horizon if needed (loop breaks at cur_t > horizon, but last_t might be < horizon)
        # Actually, the loop processes events <= horizon. If an event is exactly horizon, it's processed.
        # Any time after last event until horizon needs to be accounted for if no more events.
        # But since arrivals are infinite, there will always be an event eventually unless horizon is huge and RNG fails? No.
        # However, if the last event was before horizon, we need to integrate the tail.
        if last_t < horizon:
            n1 = len(q1) + (1 if b1_end > last_t else 0)
            n2 = len(q2) + (1 if b2_end > last_t else 0)
            L_val = n1 + n2
            start_int = max(last_t, win_start)
            end_int = horizon
            if end_int > start_int:
                area_L += L_val * (end_int - start_int)
                
            if b1_end > last_t:
                bs1 = min(b1_end, horizon) - max(last_t, 0)
                if bs1 > 0: busy1_acc += bs1
            if b2_end > last_t:
                bs2 = min(b2_end, horizon) - max(last_t, 0)
                if bs2 > 0: busy2_acc += bs2

        avg_L = area_L / win_len if win_len > 0 else 0
        avg_W = sum_W / cnt_D if cnt_D > 0 else 0
        # Convert W to minutes
        avg_W_min = avg_W * 60.0
        
        busy_frac = (busy1_acc + busy2_acc) / (2 * win_len) if win_len > 0 else 0
        p_loss = 0.0 # No blocking/loss in this model description (infinite queue implied by "queue")
        p_wait = wait_cnt / cnt_A if cnt_A > 0 else 0
        
        all_L_area.append(avg_L)
        all_W_sum.append(avg_W_min)
        all_arr_count.append(cnt_A)
        all_dep_count.append(cnt_D)
        all_blk_count.append(cnt_B)
        all_busy1_time.append(busy1_acc)
        all_busy2_time.append(busy2_acc)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        
    final_L = sum(all_L_area) / seeds_used
    final_W = sum(all_W_sum) / seeds_used
    final_arr = sum(all_arr_count) / seeds_used
    final_dep = sum(all_dep_count) / seeds_used
    final_blk = sum(all_blk_count) / seeds_used
    final_busy_frac = sum([ (all_busy1_time[i] + all_busy2_time[i]) / (2 * win_len) if win_len>0 else 0 for i in range(seeds_used)]) / seeds_used
    final_util = final_busy_frac # Same as busy_frac here
    final_dep_rate = final_dep / win_len if win_len > 0 else 0
    final_lam_eff = final_dep_rate
    final_p_loss = sum(all_p_loss) / seeds_used
    final_p_wait = sum(all_p_wait) / seeds_used
    
    out = {
        "L": round(final_L, 6),
        "W": round(final_W, 6),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(final_arr, 6),
        "blk": round(final_blk, 6),
        "busy_frac": round(final_busy_frac, 6),
        "busy_util": round(final_util, 6),
        "dep": round(final_dep, 6),
        "dep_rate": round(final_dep_rate, 6),
        "lam_eff": round(final_lam_eff, 6),
        "p_loss": round(final_p_loss, 6),
        "p_wait": round(final_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L_area],
        "per_seed_W": [round(x, 6) for x in all_W_sum],
        "per_seed_busy_frac": [round((all_busy1_time[i]+all_busy2_time[i])/(2*win_len), 6) if win_len>0 else 0 for i in range(seeds_used)],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
