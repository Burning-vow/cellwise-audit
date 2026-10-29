import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0
    mu1_base = 8.0
    mu2_base = 10.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
        mu1 = mu1_base
        mu2 = mu2_base
    elif pert == 'mu_up':
        lam = lam_base
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
        
    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_arr_count = 0
    all_dep_count = 0
    all_blk_count = 0
    all_busy1_time = 0.0
    all_busy2_time = 0.0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        queue1 = []
        queue2 = []
        server1_free_at = 0.0
        server2_free_at = 0.0
        last_event_time = 0.0
        current_L1 = 0
        current_L2 = 0
        L_area = 0.0
        W_sum = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        busy1_time = 0.0
        busy2_time = 0.0
        
        # Next arrival time
        next_arrival = -rng.expovariate(lam)
        
        while t < H:
            # Determine next event time
            events = []
            if next_arrival > t:
                events.append(('arr', next_arrival))
            if server1_free_at > t and len(queue1) > 0:
                events.append(('dep1', server1_free_at))
            if server2_free_at > t and len(queue2) > 0:
                events.append(('dep2', server2_free_at))
            
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Integrate area before changing state
            dt = etime - last_event_time
            if last_event_time >= warmup_end:
                L_area += (current_L1 + current_L2) * dt
            
            t = etime
            last_event_time = t
            
            if etype == 'arr':
                if t >= warmup_end:
                    arr_count += 1
                # Generate service times now
                s1 = rng.expovariate(mu1)
                s2 = rng.expovariate(mu2)
                job = {'arrival_time': t, 's1': s1, 's2': s2}
                
                if server1_free_at <= t:
                    server1_free_at = t + s1
                    if t >= warmup_end:
                        busy1_time += s1
                    current_L1 += 1
                else:
                    queue1.append(job)
                    current_L1 += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif etype == 'dep1':
                if queue1:
                    job = queue1.pop(0)
                    current_L1 -= 1
                    if server1_free_at <= t:
                         pass # Should be handled by logic above, but just in case
                    # Start service on server 1? No, this is completion of service on server 1.
                    # The job was being served or waiting. 
                    # If it was waiting, we need to start serving the next one from queue1 if any.
                    # But wait, my logic above: when arrival happens, if server free, set free_at.
                    # When dep1 happens, it means a job finished on server 1.
                    
                    # Actually, let's restructure slightly for clarity within constraints.
                    # In standard DES:
                    # Arrival: if server idle, start service immediately. Else join queue.
                    # Departure: remove from system (server). If queue non-empty, pop head and start service.
                    
                    # Let's trace carefully.
                    # On Arr: if server1_free_at <= t: server1_free_at = t+s1; L1++; busy+=s1. Else: queue1.append; L1++.
                    # On Dep1: This implies a job finished. Which job? The one that caused server1_free_at to be t.
                    # We need to know which job it was to calculate W later? Or just track flow.
                    # To calculate W, we need departure time from system 2.
                    
                    # Correction: I need to track individual jobs through both stages.
                    # Simpler approach:
                    # Queue1 holds jobs waiting for Server1.
                    # Server1 processes one job at a time.
                    # When Server1 finishes, job moves to Queue2 (waiting for Server2).
                    # When Server2 finishes, job leaves system.
                    
                    # Let's restart the loop logic mentally to ensure correctness with single-pass integration.
                    pass 
                
                # Re-implementing the core loop more robustly inside the function scope without classes
                # Resetting variables for the inner simulation block to avoid confusion
                pass

        # Since complex state management is hard in one flat function without classes, 
        # I will implement a simplified but correct discrete event loop using lists as queues.
        
        # Reset for actual implementation below
        rng = random.Random(seed)
        t = 0.0
        q1 = [] # Jobs waiting for S1
        q2 = [] # Jobs waiting for S2
        s1_busy_until = 0.0
        s2_busy_until = 0.0
        last_t = 0.0
        n_in_sys = 0
        area_L = 0.0
        sum_W = 0.0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        time_s1_busy = 0.0
        time_s2_busy = 0.0
        
        next_arr = rng.expovariate(lam)
        
        while t < H:
            # Find next event
            candidates = []
            if next_arr > t: candidates.append((next_arr, 'A'))
            if s1_busy_until > t and len(q1) > 0: candidates.append((s1_busy_until, 'D1'))
            if s2_busy_until > t and len(q2) > 0: candidates.append((s2_busy_until, 'D2'))
            
            if not candidates: break
            candidates.sort()
            nt, ne = candidates[0]
            
            # Integrate
            dt = nt - last_t
            if last_t >= warmup_end:
                area_L += n_in_sys * dt
            last_t = nt
            t = nt
            
            if ne == 'A':
                if t >= warmup_end: cnt_arr += 1
                # Create job
                j = {
                    't0': t,
                    's1': rng.expovariate(mu1),
                    's2': rng.expovariate(mu2)
                }
                if s1_busy_until <= t:
                    s1_busy_until = t + j['s1']
                    if t >= warmup_end: time_s1_busy += j['s1']
                    n_in_sys += 1
                else:
                    q1.append(j)
                    n_in_sys += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ne == 'D1':
                # Job finishes S1
                # Who finished? The one that started. 
                # Logic: If q1 has items, the one currently being served isn't in q1.
                # My previous logic: if server free, don't add to q1. So q1 only contains WAITING jobs.
                # The job being served is implicit.
                # When D1 occurs, the job that was being served on S1 is done.
                # Move it to Q2.
                # But how do I get its data? 
                # I need to store the job currently in service.
                # Let's use a variable `job_in_s1`.
                pass

        # Final attempt with explicit job tracking
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        job_s1 = None
        job_s2 = None
        s1_free = 0.0
        s2_free = 0.0
        last_t = 0.0
        n_in_sys = 0
        area_L = 0.0
        sum_W = 0.0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        b1_t = 0.0
        b2_t = 0.0
        
        next_arr = rng.expovariate(lam)
        
        while t < H:
            evts = []
            if next_arr > t: evts.append((next_arr, 'A'))
            if job_s1 is not None and s1_free > t: evts.append((s1_free, 'D1'))
            if job_s2 is not None and s2_free > t: evts.append((s2_free, 'D2'))
            
            if not evts: break
            evts.sort()
            nt, ne = evts[0]
            
            dt = nt - last_t
            if last_t >= warmup_end:
                area_L += n_in_sys * dt
            last_t = nt
            t = nt
            
            if ne == 'A':
                if t >= warmup_end: cnt_arr += 1
                j = {'t0': t, 's1': rng.expovariate(mu1), 's2': rng.expovariate(mu2)}
                if job_s1 is None:
                    job_s1 = j
                    s1_free = t + j['s1']
                    if t >= warmup_end: b1_t += j['s1']
                    n_in_sys += 1
                else:
                    q1.append(j)
                    n_in_sys += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ne == 'D1':
                j = job_s1
                job_s1 = None
                if q1:
                    nj = q1.pop(0)
                    job_s1 = nj
                    s1_free = t + nj['s1']
                    if t >= warmup_end: b1_t += nj['s1']
                if job_s2 is None:
                    job_s2 = j
                    s2_free = t + j['s2']
                    if t >= warmup_end: b2_t += j['s2']
                else:
                    q2.append(j)
                    
            elif ne == 'D2':
                j = job_s2
                job_s2 = None
                w = t - j['t0']
                if t >= warmup_end:
                    sum_W += w
                    cnt_dep += 1
                if q2:
                    nj = q2.pop(0)
                    job_s2 = nj
                    s2_free = t + nj['s2']
                    if t >= warmup_end: b2_t += nj['s2']
                n_in_sys -= 1

        L_est = area_L / win if win > 0 else 0
        W_est = sum_W / cnt_dep if cnt_dep > 0 else 0
        bf1 = b1_t / win if win > 0 else 0
        bf2 = b2_t / win if win > 0 else 0
        avg_bf = (bf1 + bf2) / 2
        p_loss = cnt_blk / cnt_arr if cnt_arr > 0 else 0
        p_wait = (cnt_arr - cnt_dep) / cnt_arr if cnt_arr > 0 else 0 # Approximation for blocking/waiting loss
        
        all_L_area += area_L
        all_W_sum += sum_W
        all_arr_count += cnt_arr
        all_dep_count += cnt_dep
        all_blk_count += cnt_blk
        all_busy1_time += b1_t
        all_busy2_time += b2_t
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(avg_bf)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    final_L = all_L_area / (N * win) if N*win > 0 else 0
    final_W = all_W_sum / all_dep_count if all_dep_count > 0 else 0
    final_arr = all_arr_count / N
    final_dep = all_dep_count / N
    final_blk = all_blk_count / N
    final_busy_frac = ((all_busy1_time + all_busy2_time) / 2) / (N * win) if N*win > 0 else 0
    final_util = final_busy_frac
    final_dep_rate = final_dep / H if H > 0 else 0
    final_lam_eff = final_dep_rate
    final_p_loss = final_blk / final_arr if final_arr > 0 else 0
    final_p_wait = (final_arr - final_dep) / final_arr if final_arr > 0 else 0

    res = {
        "L": round(final_L, 4),
        "W": round(final_W, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(final_arr, 4),
        "blk": round(final_blk, 4),
        "busy_frac": round(final_busy_frac, 4),
        "busy_util": round(final_util, 4),
        "dep": round(final_dep, 4),
        "dep_rate": round(final_dep_rate, 4),
        "lam_eff": round(final_lam_eff, 4),
        "p_loss": round(final_p_loss, 4),
        "p_wait": round(final_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
