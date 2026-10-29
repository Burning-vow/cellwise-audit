import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 7.0 / 60.0  # per minute
    mu_base = 1.0 / 5.0    # per minute
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.1
    elif a.pert == 'mu_up':
        mu = mu_base * 1.1
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    all_p_loss = []
    all_lam_eff = []
    all_dep_rate = []
    seed_list = []
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        t = 0.0
        N = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        area_N = 0.0
        area_busy = 0.0
        last_event_time = 0.0
        customers_in_system = []  # list of (arrival_time, service_duration)
        
        while t < horizon_min:
            if next_arr <= next_dep and next_arr < horizon_min:
                dt = next_arr - t
                if t >= warmup_end:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_arr
                arr_count += 1
                svc_dur = rng.expovariate(mu)
                if N == 0:
                    N = 1
                    next_dep = t + svc_dur
                    customers_in_system.append((t, svc_dur))
                else:
                    N += 1
                    customers_in_system.append((t, svc_dur))
                next_arr = t + rng.expovariate(lam)
            elif next_dep < horizon_min:
                dt = next_dep - t
                if t >= warmup_end:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_dep
                dep_count += 1
                if len(customers_in_system) > 0:
                    cust = customers_in_system.pop(0)
                    wait_time = t - cust[0]
                    if t >= warmup_end:
                        wait_sum += wait_time
                N -= 1
                if N > 0:
                    next_cust = customers_in_system[0]
                    remaining_svc = next_cust[1] - (t - next_cust[0])
                    if remaining_svc < 0:
                        remaining_svc = 0.0
                    next_dep = t + remaining_svc
                else:
                    next_dep = float('inf')
            else:
                break
                
        win_len = horizon_min - warmup_end
        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = wait_sum / dep_count if dep_count > 0 else 0.0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0.0
        p_wait_est = 0.0
        if dep_count > 0:
            # Approximate p_wait as fraction of time system was non-empty during window? 
            # Or based on arrivals finding server busy. Let's use time-average of indicator(N>0) which is busy_frac.
            # But standard definition often uses arrival-based. Given constraints, let's stick to time-average proxy or compute properly.
            # Actually, for M/M/1, P(wait) = rho. Let's estimate from data: count arrivals that found N>0.
            pass
            
        # Recalculate p_wait more accurately by tracking arrivals
        # We need to re-simulate or track during simulation. Let's modify loop slightly mentally but code needs to be single pass.
        # I will add a counter for arrivals that find server busy.
        
        # Re-running logic with added counters would require restructuring. 
        # Instead, let's approximate p_wait using the theoretical relation or simple ratio if possible.
        # Better: Track `arrivals_finding_busy` inside the loop.
        
        # Since I cannot easily edit the loop structure without rewriting, I'll assume the previous loop missed it.
        # Let's rewrite the inner loop part carefully in the final code block.
        
        # For now, placeholder calculations based on what we have.
        # Note: The prompt requires specific keys. I must ensure they are present.
        
        # Let's refine the simulation loop in the actual output to include `arrivals_finding_busy`.
        
        # Placeholder values to satisfy structure before finalizing logic in thought process:
        # I will implement the full correct logic in the code below.
        
        seed_list.append(s)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        # Will fix p_wait in final code
        all_p_wait.append(0.0) 
        all_arr.append(arr_count)
        all_blk.append(blk_count)
        all_dep.append(dep_count)
        all_busy_util.append(busy_frac_est) # E[min(N,1)]/1 is same as busy_frac for c=1
        all_busy_occupied.append(busy_frac_est) # 1-pi0 is same as busy_frac for c=1
        all_p_loss.append(0.0)
        all_lam_eff.append(arr_count / horizon_min * 60.0 if horizon_min > 0 else 0.0)
        all_dep_rate.append(dep_count / horizon_min * 60.0 if horizon_min > 0 else 0.0)

    # The above loop had a flaw in p_wait calculation. I will provide the corrected complete code.
    
    # Resetting to write the clean, correct version directly.
    pass

# Corrected implementation follows:
import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_per_min = 7.0 / 60.0
    mu_per_min = 1.0 / 5.0

    if args.pert == 'lam_up':
        lam = lam_per_min * 1.1
        mu = mu_per_min
    elif args.pert == 'mu_up':
        lam = lam_per_min
        mu = mu_per_min * 1.1
    elif args.pert == 'c_up':
        lam = lam_per_min
        mu = mu_per_min
    else:
        lam = lam_per_min
        mu = mu_per_min

    H = args.horizon
    warmup_end = H * 0.75

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    results_busy_util = []
    results_busy_occ = []
    results_p_loss = []
    results_lam_eff = []
    results_dep_rate = []
    used_seeds = []

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        N = 0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        total_arrivals = 0
        total_departures = 0
        total_blocked = 0
        total_wait_time = 0.0
        area_N = 0.0
        area_busy = 0.0
        arrivals_finding_busy = 0
        
        queue = [] # List of tuples (arrival_time, service_time)

        while t < H:
            if next_arrival <= next_departure and next_arrival < H:
                dt = next_arrival - t
                if t >= warmup_end:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_arrival
                total_arrivals += 1
                svc_time = rng.expovariate(mu)
                
                if N == 0:
                    N = 1
                    next_departure = t + svc_time
                    queue.append((t, svc_time))
                else:
                    N += 1
                    arrivals_finding_busy += 1
                    queue.append((t, svc_time))
                    
                next_arrival = t + rng.expovariate(lam)
                
            elif next_departure < H:
                dt = next_departure - t
                if t >= warmup_end:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_departure
                total_departures += 1
                
                if queue:
                    arr_t, svc_t = queue.pop(0)
                    w = t - arr_t
                    if t >= warmup_end:
                        total_wait_time += w
                        
                N -= 1
                if N > 0:
                    next_arr_t, next_svc_t = queue[0]
                    elapsed_on_current = t - next_arr_t
                    remaining_svc = next_svc_t - elapsed_on_current
                    if remaining_svc < 0:
                        remaining_svc = 0.0
                    next_departure = t + remaining_svc
                else:
                    next_departure = float('inf')
            else:
                break

        win_len = H - warmup_end
        L_val = area_N / win_len if win_len > 0 else 0.0
        W_val = total_wait_time / total_departures if total_departures > 0 else 0.0
        bf_val = area_busy / win_len if win_len > 0 else 0.0
        pw_val = arrivals_finding_busy / total_arrivals if total_arrivals > 0 else 0.0
        
        used_seeds.append(seed)
        results_L.append(L_val)
        results_W.append(W_val)
        results_busy_frac.append(bf_val)
        results_p_wait.append(pw_val)
        results_arr.append(total_arrivals)
        results_blk.append(total_blocked)
        results_dep.append(total_departures)
        results_busy_util.append(bf_val)
        results_busy_occ.append(bf_val)
        results_p_loss.append(0.0)
        results_lam_eff.append(total_arrivals / H * 60.0 if H > 0 else 0.0)
        results_dep_rate.append(total_departures / H * 60.0 if H > 0 else 0.0)

    n_seeds = len(used_seeds)
    avg_L = sum(results_L) / n_seeds if n_seeds > 0 else 0.0
    avg_W = sum(results_W) / n_seeds if n_seeds > 0 else 0.0
    avg_bf = sum(results_busy_frac) / n_seeds if n_seeds > 0 else 0.0
    avg_pw = sum(results_p_wait) / n_seeds if n_seeds > 0 else 0.0
    avg_arr = sum(results_arr) / n_seeds if n_seeds > 0 else 0.0
    avg_blk = sum(results_blk) / n_seeds if n_seeds > 0 else 0.0
    avg_dep = sum(results_dep) / n_seeds if n_seeds > 0 else 0.0
    avg_bu = sum(results_busy_util) / n_seeds if n_seeds > 0 else 0.0
    avg_bo = sum(results_busy_occ) / n_seeds if n_seeds > 0 else 0.0
    avg_pl = sum(results_p_loss) / n_seeds if n_seeds > 0 else 0.0
    avg_le = sum(results_lam_eff) / n_seeds if n_seeds > 0 else 0.0
    avg_dr = sum(results_dep_rate) / n_seeds if n_seeds > 0 else 0.0

    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "minute",
        "seed_list": used_seeds,
        "seeds_used": n_seeds,
        "time_unit": "minute",
        "win": round(H - warmup_end, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dr, 6),
        "lam_eff": round(avg_le, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in results_L],
        "per_seed_W": [round(x, 6) for x in results_W],
        "per_seed_busy_frac": [round(x, 6) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in results_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
