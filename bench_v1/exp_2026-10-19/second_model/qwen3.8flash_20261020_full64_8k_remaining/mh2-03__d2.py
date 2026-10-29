import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base, mu_base, c_base = 3.0, 10.0, 1.0
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': c_base += 1
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        busy_time = 0.0
        last_event_t = 0.0
        n_in_sys = 0
        area_L = 0.0
        wait_area = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        while t < horizon:
            if next_arr is not None and (service_end is None or next_arr <= service_end):
                dt = next_arr - t
                if t >= win_start:
                    area_L += n_in_sys * dt
                    if n_in_sys > 0:
                        wait_area += (n_in_sys - 1) * dt
                    busy_time += min(n_in_sys, c_base) * dt
                t = next_arr
                arr_count += 1
                if len(queue) + (1 if service_end is not None else 0) < c_base:
                    dur = rng.expovariate(mu_base)
                    if service_end is None:
                        service_end = t + dur
                        n_in_sys += 1
                    else:
                        queue.append(dur)
                        n_in_sys += 1
                else:
                    blk_count += 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                dt = service_end - t
                if t >= win_start:
                    area_L += n_in_sys * dt
                    if n_in_sys > 0:
                        wait_area += (n_in_sys - 1) * dt
                    busy_time += min(n_in_sys, c_base) * dt
                t = service_end
                dep_count += 1
                n_in_sys -= 1
                if queue:
                    dur = queue.pop(0)
                    service_end = t + dur
                    n_in_sys += 1
                else:
                    service_end = None
        
        if t < horizon:
            dt = horizon - t
            if t >= win_start:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    wait_area += (n_in_sys - 1) * dt
                busy_time += min(n_in_sys, c_base) * dt
        
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = wait_area / dep_count if dep_count > 0 else 0
        bf_est = busy_time / win_len if win_len > 0 else 0
        pl_est = blk_count / arr_count if arr_count > 0 else 0
        pw_est = (dep_count - blk_count) / dep_count if dep_count > 0 else 0
        
        seeds_used.append(seed)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est * 60)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
    
    N = len(seeds_used)
    avg_L = sum(per_seed_L) / N if N else 0
    avg_W = sum(per_seed_W) / N if N else 0
    avg_bf = sum(per_seed_busy_frac) / N if N else 0
    avg_pl = sum(per_seed_p_loss) / N if N else 0
    avg_pw = sum(per_seed_p_wait) / N if N else 0
    avg_arr = total_arr / N if N else 0
    avg_dep = total_dep / N if N else 0
    avg_blk = total_blk / N if N else 0
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bf, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
