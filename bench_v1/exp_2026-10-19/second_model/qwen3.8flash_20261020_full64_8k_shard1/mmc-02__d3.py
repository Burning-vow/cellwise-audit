import argparse, json, random, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 6.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = "hour"
    horizon_hours = H if time_unit == "hour" else (H / 60.0 if time_unit == "minute" else H / 3600.0)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    warmup_frac = 0.25
    win_start = warmup_frac * horizon_hours
    win_len = horizon_hours - win_start
    
    for i in range(N_seeds):
        rng = random.Random(seed_start + i)
        
        events = []
        t = 0.0
        n_in_system = 0
        busy_servers = 0
        
        next_arrival_time = rng.expovariate(lam)
        arrivals = 0
        departures = 0
        blocked = 0
        
        area_n = 0.0
        area_min_nc = 0.0
        last_event_time = 0.0
        
        waiting_times_sum = 0.0
        service_completed_count = 0
        
        queue = []
        server_free_times = [0.0] * c
        
        while True:
            next_departure = min(server_free_times) if any(s > t for s in server_free_times) else float('inf')
            
            if next_arrival_time <= next_departure and next_arrival_time < horizon_hours:
                dt = next_arrival_time - last_event_time
                if last_event_time >= win_start:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                elif next_arrival_time > win_start:
                    overlap = next_arrival_time - max(last_event_time, win_start)
                    area_n += n_in_system * overlap
                    area_min_nc += min(n_in_system, c) * overlap
                
                t = next_arrival_time
                last_event_time = t
                arrivals += 1
                
                if n_in_system < c:
                    idx = server_free_times.index(min(server_free_times))
                    svc_time = rng.expovariate(mu)
                    server_free_times[idx] = t + svc_time
                    n_in_system += 1
                    queue.append((t, t + svc_time, svc_time))
                else:
                    if len(queue) < 10000:
                        svc_time = rng.expovariate(mu)
                        queue.append((t, None, svc_time))
                        n_in_system += 1
                    else:
                        blocked += 1
                
                next_arrival_time = t + rng.expovariate(lam)
                
            elif next_departure < horizon_hours and next_departure != float('inf'):
                dt = next_departure - last_event_time
                if last_event_time >= win_start:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                elif next_departure > win_start:
                    overlap = next_departure - max(last_event_time, win_start)
                    area_n += n_in_system * overlap
                    area_min_nc += min(n_in_system, c) * overlap
                
                t = next_departure
                last_event_time = t
                
                completed_idx = -1
                for j in range(c):
                    if abs(server_free_times[j] - t) < 1e-9:
                        completed_idx = j
                        break
                
                if completed_idx >= 0:
                    for k, item in enumerate(queue):
                        if item[1] is not None and abs(item[1] - t) < 1e-9:
                            wait_plus_service = t - item[0]
                            if item[0] >= win_start:
                                waiting_times_sum += wait_plus_service
                                service_completed_count += 1
                            queue.pop(k)
                            break
                    
                    n_in_system -= 1
                    departures += 1
                    
                    if queue:
                        first_item = queue[0]
                        if first_item[1] is None:
                            svc_time = first_item[2]
                            start_time = t
                            end_time = t + svc_time
                            queue[0] = (first_item[0], end_time, svc_time)
                            server_free_times[completed_idx] = end_time
                            n_in_system += 1
                        else:
                            server_free_times[completed_idx] = t
                    else:
                        server_free_times[completed_idx] = t
            else:
                dt = horizon_hours - last_event_time
                if last_event_time >= win_start:
                    area_n += n_in_system * dt
                    area_min_nc += min(n_in_system, c) * dt
                elif horizon_hours > win_start:
                    overlap = horizon_hours - max(last_event_time, win_start)
                    area_n += n_in_system * overlap
                    area_min_nc += min(n_in_system, c) * overlap
                break
        
        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = (waiting_times_sum / service_completed_count * 60.0) if service_completed_count > 0 else 0.0
        busy_frac_est = area_min_nc / (win_len * c) if win_len > 0 else 0.0
        p_wait_est = 0.0
        
        arr_in_win = 0
        dep_in_win = 0
        blk_in_win = 0
        
        rng2 = random.Random(seed_start + i)
        t2 = 0.0
        n2 = 0
        sf2 = [0.0] * c
        q2 = []
        na2 = rng2.expovariate(lam)
        a_cnt = 0
        d_cnt = 0
        b_cnt = 0
        w_sum = 0.0
        sc_cnt = 0
        le2 = 0.0
        an2 = 0.0
        amn2 = 0.0
        
        while True:
            nd2 = min(sf2) if any(s > t2 for s in sf2) else float('inf')
            if na2 <= nd2 and na2 < horizon_hours:
                dt2 = na2 - le2
                if le2 >= win_start:
                    an2 += n2 * dt2
                    amn2 += min(n2, c) * dt2
                elif na2 > win_start:
                    ov = na2 - max(le2, win_start)
                    an2 += n2 * ov
                    amn2 += min(n2, c) * ov
                t2 = na2
                le2 = t2
                a_cnt += 1
                if n2 < c:
                    idx2 = sf2.index(min(sf2))
                    st2 = rng2.expovariate(mu)
                    sf2[idx2] = t2 + st2
                    n2 += 1
                    q2.append((t2, t2 + st2, st2))
                else:
                    if len(q2) < 10000:
                        st2 = rng2.expovariate(mu)
                        q2.append((t2, None, st2))
                        n2 += 1
                    else:
                        b_cnt += 1
                na2 = t2 + rng2.expovariate(lam)
            elif nd2 < horizon_hours and nd2 != float('inf'):
                dt2 = nd2 - le2
                if le2 >= win_start:
                    an2 += n2 * dt2
                    amn2 += min(n2, c) * dt2
                elif nd2 > win_start:
                    ov = nd2 - max(le2, win_start)
                    an2 += n2 * ov
                    amn2 += min(n2, c) * ov
                t2 = nd2
                le2 = t2
                ci2 = -1
                for j2 in range(c):
                    if abs(sf2[j2] - t2) < 1e-9:
                        ci2 = j2
                        break
                if ci2 >= 0:
                    for k2, it2 in enumerate(q2):
                        if it2[1] is not None and abs(it2[1] - t2) < 1e-9:
                            wt2 = t2 - it2[0]
                            if it2[0] >= win_start:
                                w_sum += wt2
                                sc_cnt += 1
                            q2.pop(k2)
                            break
                    n2 -= 1
                    d_cnt += 1
                    if q2:
                        fi2 = q2[0]
                        if fi2[1] is None:
                            sv2 = fi2[2]
                            et2 = t2 + sv2
                            q2[0] = (fi2[0], et2, sv2)
                            sf2[ci2] = et2
                            n2 += 1
                        else:
                            sf2[ci2] = t2
                    else:
                        sf2[ci2] = t2
            else:
                dt2 = horizon_hours - le2
                if le2 >= win_start:
                    an2 += n2 * dt2
                    amn2 += min(n2, c) * dt2
                elif horizon_hours > win_start:
                    ov = horizon_hours - max(le2, win_start)
                    an2 += n2 * ov
                    amn2 += min(n2, c) * ov
                break
        
        L_i = an2 / win_len if win_len > 0 else 0.0
        W_i = (w_sum / sc_cnt * 60.0) if sc_cnt > 0 else 0.0
        bf_i = amn2 / (win_len * c) if win_len > 0 else 0.0
        pl_i = b_cnt / a_cnt if a_cnt > 0 else 0.0
        pw_i = 0.0
        
        per_seed_L.append(L_i)
        per_seed_W.append(W_i)
        per_seed_busy_frac.append(bf_i)
        per_seed_p_loss.append(pl_i)
        per_seed_p_wait.append(pw_i)
        
        all_L.append(L_i)
        all_W.append(W_i)
        all_busy_frac.append(bf_i)
        all_p_wait.append(pw_i)
        all_arr.append(a_cnt)
        all_dep.append(d_cnt)
        all_blk.append(b_cnt)
        all_busy_util.append(bf_i)
        dr = d_cnt / win_len if win_len > 0 else 0.0
        all_dep_rate.append(dr)
        le = a_cnt / win_len if win_len > 0 else 0.0
        all_lam_eff.append(le)
        all_p_loss.append(pl_i)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_bf = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_pw = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    avg_bu = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
    avg_dr = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0
    avg_le = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
    avg_pl = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": time_unit,
        "seed_list": list(range(seed_start, seed_start + N_seeds)),
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dr, 6),
        "lam_eff": round(avg_le, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
