import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert
    
    lam_base = 4.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0    # per minute
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_win = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {}
        queue = []
        server_free_time = 0.0
        num_in_system = 0
        total_time = 0.0
        weighted_sum_N = 0.0
        arrivals_count = 0
        departures_count = 0
        blocked_count = 0
        wait_events = 0
        busy_periods = 0.0
        last_event_time = 0.0
        
        warmup_end = H * 0.75
        stats_window_len = H - warmup_end
        
        while t < H:
            if not queue and t >= server_free_time:
                if next_arrival <= H:
                    dt = next_arrival - t
                    if dt > 0:
                        weighted_sum_N += num_in_system * dt
                        busy_periods += (min(num_in_system, 1)) * dt if num_in_system > 0 else 0
                        t = next_arrival
                        last_event_time = t
                        st = rng.expovariate(mu)
                        service_times[t] = st
                        queue.append(t)
                        num_in_system += 1
                        arrivals_count += 1
                        if t >= warmup_end:
                            pass 
                        next_arrival = t + rng.expovariate(lam)
                    else:
                        t = next_arrival
                        st = rng.expovariate(mu)
                        service_times[t] = st
                        queue.append(t)
                        num_in_system += 1
                        arrivals_count += 1
                        next_arrival = t + rng.expovariate(lam)
                else:
                    break
            else:
                if queue:
                    arr_t = queue[0]
                    start_serv = max(arr_t, server_free_time)
                    end_serv = start_serv + service_times[arr_t]
                    
                    if end_serv <= H:
                        dt = end_serv - t
                        if dt > 0:
                            weighted_sum_N += num_in_system * dt
                            busy_periods += min(num_in_system, 1) * dt
                            t = end_serv
                            last_event_time = t
                            queue.pop(0)
                            num_in_system -= 1
                            departures_count += 1
                            server_free_time = end_serv
                            if arr_t >= warmup_end or t >= warmup_end:
                                pass
                    else:
                        dt = H - t
                        if dt > 0:
                            weighted_sum_N += num_in_system * dt
                            busy_periods += min(num_in_system, 1) * dt
                            t = H
                        break
                else:
                    if next_arrival <= H:
                        dt = next_arrival - t
                        if dt > 0:
                            weighted_sum_N += num_in_system * dt
                            busy_periods += min(num_in_system, 1) * dt
                            t = next_arrival
                            last_event_time = t
                            st = rng.expovariate(mu)
                            service_times[t] = st
                            queue.append(t)
                            num_in_system += 1
                            arrivals_count += 1
                            next_arrival = t + rng.expovariate(lam)
                        else:
                            t = next_arrival
                            st = rng.expovariate(mu)
                            service_times[t] = st
                            queue.append(t)
                            num_in_system += 1
                            arrivals_count += 1
                            next_arrival = t + rng.expovariate(lam)
                    else:
                        dt = H - t
                        if dt > 0:
                            weighted_sum_N += num_in_system * dt
                            busy_periods += min(num_in_system, 1) * dt
                            t = H
                        break
        
        L_est = weighted_sum_N / H if H > 0 else 0
        W_est = L_est / (arrivals_count / H) if arrivals_count > 0 else 0
        busy_frac_est = busy_periods / H if H > 0 else 0
        p_wait_est = 0.0 
        for q_t in queue:
             if q_t < H:
                 p_wait_est += 1
        p_wait_est = p_wait_est / arrivals_count if arrivals_count > 0 else 0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals_count)
        all_blk.append(blocked_count)
        all_dep.append(departures_count)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(departures_count / H * 60.0)
        all_lam_eff.append(arrivals_count / H * 60.0)
        all_p_loss.append(0.0)
        all_win.append(H)

    avg_L = sum(all_L) / N
    avg_W = sum(all_W) / N
    avg_busy_frac = sum(all_busy_frac) / N
    avg_p_wait = sum(all_p_wait) / N
    avg_arr = sum(all_arr) / N
    avg_blk = sum(all_blk) / N
    avg_dep = sum(all_dep) / N
    avg_busy_util = sum(all_busy_util) / N
    avg_dep_rate = sum(all_dep_rate) / N
    avg_lam_eff = sum(all_lam_eff) / N
    avg_p_loss = sum(all_p_loss) / N
    avg_win = sum(all_win) / N
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "minutes",
        "seed_list": [S+i for i in range(N)],
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(avg_win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
