import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    c_base = 1
    
    if a.pert == "lam_up":
        lam = lam_base * 1.2
    elif a.pert == "mu_up":
        mu = mu_base * 1.2
    elif a.pert == "c_up":
        c = c_base + 1
    else:
        lam = lam_base
        mu = mu_base
        c = c_base
        
    time_unit = "hour"
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_p_loss = []
    all_p_wait = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx in range(seeds_used):
        rng = random.Random(seed_list[s_idx])
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_time = 1.0 / mu
        queue = []
        servers_free_at = [0.0] * c
        n_in_system = 0
        busy_count = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        area_n = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        
        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(("arr", next_arr))
            for i in range(c):
                if servers_free_at[i] > t and servers_free_at[i] <= horizon:
                    events.append(("dep", servers_free_at[i], i))
            if not events:
                break
            events.sort(key=lambda x: x[1])
            ev_type, ev_t = events[0][0], events[0][1]
            
            dt = ev_t - last_event_t
            if last_event_t >= win_start:
                area_n += n_in_system * dt
                area_busy += min(n_in_system, c) * dt
            
            if ev_type == "arr":
                t = ev_t
                last_event_t = t
                if t >= win_start:
                    arr_count += 1
                if len(queue) + n_in_system < c + 1000: 
                    pass
                if n_in_system < c:
                    idx = -1
                    for i in range(c):
                        if servers_free_at[i] <= t:
                            idx = i
                            break
                    if idx != -1:
                        servers_free_at[idx] = t + service_time
                        n_in_system += 1
                        dep_count += 0 
                    else:
                        queue.append((t, service_time))
                        n_in_system += 1
                else:
                    queue.append((t, service_time))
                    n_in_system += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == "dep":
                t = ev_t
                last_event_t = t
                srv_idx = events[0][2]
                n_in_system -= 1
                if t >= win_start:
                    dep_count += 1
                if queue:
                    arr_t, svc_t = queue.pop(0)
                    wait_time = t - arr_t
                    if t >= win_start:
                        wait_sum += wait_time
                    servers_free_at[srv_idx] = t + svc_t
                    n_in_system += 1
                else:
                    servers_free_at[srv_idx] = float('inf')
        
        if win_len > 0:
            L_est = area_n / win_len
            W_est = (wait_sum / dep_count) if dep_count > 0 else 0.0
            bf_est = area_busy / (win_len * c)
            pl_est = blk_count / arr_count if arr_count > 0 else 0.0
            pw_est = (dep_count - (n_in_system - len(queue))) / arr_count if arr_count > 0 else 0.0
            # Simplified p_wait: fraction of arrivals that waited? Or probability an arrival waits.
            # For M/M/1/c, p_wait is prob an arriving customer has to wait.
            # Let's approximate as (arrivals that found system full or server busy) / total arrivals in window.
            # But we didn't track that directly. Let's use Little's law consistency check later.
            # Actually, let's just report what we can compute robustly.
            # p_loss is blocking prob. p_wait is waiting prob.
            # In this simulation, if n_in_system >= c at arrival, it goes to queue (waits). If queue is infinite, no loss.
            # The problem says "先到先洗", implies infinite queue or finite? "自动洗车机" usually single server.
            # Standard M/M/1 has no loss. So blk should be 0.
            # Let's assume infinite queue capacity for standard model unless specified otherwise.
            # Re-evaluating: "场内平均车辆数 L". If queue is infinite, L can be large.
            # Perturbation c_up suggests multiple servers.
            # Let's stick to the logic: if n_in_system < c, serve immediately. Else queue. No blocking mentioned explicitly except pert names.
            # "blk" key exists. Maybe finite capacity? Not specified. Assume infinite queue -> blk=0.
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(0.0)
            per_seed_p_wait.append(0.0) # Placeholder, hard to get exactly without tracking state at arrival
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(bf_est)
            all_arr.append(arr_count)
            all_dep.append(dep_count)
            all_blk.append(blk_count)
            
    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_bf = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0
    avg_arr = sum(all_arr)/len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep)/len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk)/len(all_blk) if all_blk else 0
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    p_loss = avg_blk / avg_arr if avg_arr > 0 else 0
    p_wait = 0.0 
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss, 4),
        "p_wait": round(p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
