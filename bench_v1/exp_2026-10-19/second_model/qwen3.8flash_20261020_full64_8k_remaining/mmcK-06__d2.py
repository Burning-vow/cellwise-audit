import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    c = 3
    K = 4
    
    if a.pert == 'lam_up': lam = lam_base * 1.2
    elif a.pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif a.pert == 'c_up': c = 4; K = 5; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    H = a.horizon
    warmup_frac = 0.25
    win_start = H * warmup_frac
    win_len = H - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_blk = 0
    total_dep = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr_t = rng.expovariate(lam)
        services = []
        arr_times = {}
        dep_count = 0
        blk_count = 0
        arr_count = 0
        busy_time = 0.0
        last_event_t = 0.0
        last_n = 0
        L_integral = 0.0
        W_sum = 0.0
        
        while t < H:
            if not services and next_arr_t >= H:
                break
            if services and (not next_arr_t or services[0][0] <= next_arr_t):
                event_t, cust_id = services.pop(0)
                if event_t > H: break
                dt = event_t - last_event_t
                if last_event_t < win_start:
                    pass
                else:
                    L_integral += last_n * dt
                    if last_n > 0:
                        busy_time += dt
                
                n -= 1
                if event_t >= win_start:
                    dep_count += 1
                    w = event_t - arr_times[cust_id]
                    W_sum += w
                last_event_t = event_t
                last_n = n
                t = event_t
            else:
                event_t = next_arr_t
                if event_t > H: break
                dt = event_t - last_event_t
                if last_event_t < win_start:
                    pass
                else:
                    L_integral += last_n * dt
                    if last_n > 0:
                        busy_time += dt
                
                if n < K:
                    n += 1
                    dur = rng.expovariate(mu)
                    svc_end = event_t + dur
                    cid = id(rng) # dummy unique id
                    services.append((svc_end, cid))
                    arr_times[cid] = event_t
                    if event_t >= win_start:
                        arr_count += 1
                else:
                    if event_t >= win_start:
                        blk_count += 1
                
                next_arr_t = event_t + rng.expovariate(lam)
                last_event_t = event_t
                last_n = n
                t = event_t
        
        if last_event_t < H:
            dt = H - last_event_t
            if last_event_t < win_start:
                pass
            else:
                L_integral += last_n * dt
                if last_n > 0:
                    busy_time += dt
        
        avg_L = L_integral / win_len if win_len > 0 else 0
        avg_W = W_sum / dep_count if dep_count > 0 else 0
        bf = busy_time / win_len if win_len > 0 else 0
        pl = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0
        pw = (dep_count - arr_count + blk_count) / dep_count if dep_count > 0 else 0 
        # Actually p_wait is prob that an arriving customer waits? Or fraction of time system has queue?
        # Standard definition: P(wait) = probability that an arrival finds all servers busy.
        # In M/M/c/K, P(wait) = sum_{n=c}^{K-1} pi_n.
        # Let's approximate from simulation: count arrivals that found n>=c.
        # We didn't track that explicitly. Let's re-run logic or estimate.
        # Given constraints, let's use Little's Law consistency check or simple ratio.
        # But we need to output it. Let's assume p_wait is fraction of accepted customers who waited.
        # Accepted = arr_count. Waited = those who arrived when n>=c.
        # We missed tracking "waited" flag. 
        # Correction: In the loop, when adding service, if n_before_add >= c, they wait.
        # I will add a counter for waited arrivals.
        
        # Re-simulate quickly with waited counter? No, too long.
        # Let's infer: If n was >= c at arrival, they wait.
        # I'll modify the loop above mentally to include `waited_count`.
        # Since I can't edit previous code block easily in thought, I will rewrite the inner loop part in final code.
        
        seeds_used.append(seed)
        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W)
        per_seed_busy_frac.append(bf)
        per_seed_p_loss.append(pl)
        # Placeholder for p_wait, will fix in code
        per_seed_p_wait.append(0.0) 
        total_arr += arr_count
        total_blk += blk_count
        total_dep += dep_count

    # The above logic missed p_wait calculation properly. 
    # I will rewrite the simulation loop to capture waited_count.
    
    # Reset accumulators
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_waited = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr_t = rng.expovariate(lam)
        services = []
        arr_times = {}
        dep_count = 0
        blk_count = 0
        arr_count = 0
        waited_count = 0
        busy_time = 0.0
        last_event_t = 0.0
        last_n = 0
        L_integral = 0.0
        W_sum = 0.0
        
        while t < H:
            if not services and next_arr_t >= H:
                break
            if services and (next_arr_t is None or services[0][0] <= next_arr_t):
                event_t, cust_id = services.pop(0)
                if event_t > H: break
                dt = event_t - last_event_t
                if last_event_t >= win_start:
                    L_integral += last_n * dt
                    if last_n > 0:
                        busy_time += dt
                
                n -= 1
                if event_t >= win_start:
                    dep_count += 1
                    w = event_t - arr_times[cust_id]
                    W_sum += w
                last_event_t = event_t
                last_n = n
                t = event_t
            else:
                event_t = next_arr_t
                if event_t > H: break
                dt = event_t - last_event_t
                if last_event_t >= win_start:
                    L_integral += last_n * dt
                    if last_n > 0:
                        busy_time += dt
                
                if n < K:
                    if n >= c:
                        if event_t >= win_start:
                            waited_count += 1
                    n += 1
                    dur = rng.expovariate(mu)
                    svc_end = event_t + dur
                    cid = str(i) + "_" + str(arr_count) + "_" + str(blk_count) # Unique enough
                    services.append((svc_end, cid))
                    arr_times[cid] = event_t
                    if event_t >= win_start:
                        arr_count += 1
                else:
                    if event_t >= win_start:
                        blk_count += 1
                
                next_arr_t = event_t + rng.expovariate(lam)
                last_event_t = event_t
                last_n = n
                t = event_t
        
        if last_event_t < H:
            dt = H - last_event_t
            if last_event_t >= win_start:
                L_integral += last_n * dt
                if last_n > 0:
                    busy_time += dt
        
        avg_L = L_integral / win_len if win_len > 0 else 0
        avg_W = W_sum / dep_count if dep_count > 0 else 0
        bf = busy_time / win_len if win_len > 0 else 0
        pl = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0
        pw = waited_count / arr_count if arr_count > 0 else 0
        
        seeds_used.append(seed)
        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W)
        per_seed_busy_frac.append(bf)
        per_seed_p_loss.append(pl)
        per_seed_p_wait.append(pw)
        total_arr += arr_count
        total_blk += blk_count
        total_dep += dep_count
        total_waited += waited_count

    N_seeds = len(seeds_used)
    mean_L = sum(per_seed_L)/N_seeds if N_seeds else 0
    mean_W = sum(per_seed_W)/N_seeds if N_seeds else 0
    mean_bf = sum(per_seed_busy_frac)/N_seeds if N_seeds else 0
    mean_pl = sum(per_seed_p_loss)/N_seeds if N_seeds else 0
    mean_pw = sum(per_seed_p_wait)/N_seeds if N_seeds else 0
    
    avg_arr_per_seed = total_arr / N_seeds if N_seeds else 0
    avg_blk_per_seed = total_blk / N_seeds if N_seeds else 0
    avg_dep_per_seed = total_dep / N_seeds if N_seeds else 0
    
    dep_rate = avg_dep_per_seed / win_len if win_len > 0 else 0
    
    # busy_util = E[min(N,c)]/c
    # Approximate from mean_L? No, need integral of min(n,c).
    # We didn't track that integral. 
    # However, for M/M/c/K, utilization rho = lam_eff / mu.
    # lam_eff = dep_rate.
    # busy_util approx = dep_rate / (c * mu) ? No, that's server utilization.
    # E[min(N,c)]/c is exactly the average number of busy servers divided by c.
    # Average number of busy servers = dep_rate / mu (Little's law on servers).
    # So busy_util = (dep_rate / mu) / c.
    busy_util = (dep_rate / mu) / c if c > 0 else 0
    
    out = {
        "L": mean_L,
        "W": mean_W,
        "busy_frac": mean_bf,
        "p_loss": mean_pl,
        "runtime_units": "hour",
        "seed_list": seeds_used,
        "seeds_used": N_seeds,
        "time_unit": "hour",
        "win": win_len,
        "arr": avg_arr_per_seed,
        "blk": avg_blk_per_seed,
        "busy_util": busy_util,
        "dep": avg_dep_per_seed,
        "dep_rate": dep_rate,
        "lam_eff": dep_rate,
        "p_wait": mean_pw,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": mean_bf
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
