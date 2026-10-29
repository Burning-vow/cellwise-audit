import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base, mu_base = 3.0, 10.0
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        busy_time = 0.0
        wait_time_sum = 0.0
        n_customers_served = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        while t < horizon:
            if not queue and (service_end is None or t >= service_end):
                if next_arr <= horizon:
                    t = max(t, next_arr)
                    if t >= win_start:
                        arr_count += 1
                    queue.append((t, rng.expovariate(mu_base)))
                    next_arr = t + rng.expovariate(lam_base)
                else:
                    break
            else:
                if service_end is not None and service_end > t:
                    dt = min(service_end, next_arr if next_arr < horizon else horizon) - t
                    if t >= win_start:
                        busy_time += dt
                    t += dt
                    if service_end is not None and abs(t - service_end) < 1e-9:
                        cust = queue.pop(0)
                        if t >= win_start:
                            dep_count += 1
                            wait_time_sum += (service_end - cust[0])
                            n_customers_served += 1
                        service_end = None
                        if queue:
                            service_end = t + queue[0][1]
                elif queue:
                    cust = queue.pop(0)
                    service_end = t + cust[1]
                    if t >= win_start:
                        pass
                else:
                    if next_arr <= horizon:
                        t = next_arr
                        if t >= win_start:
                            arr_count += 1
                        queue.append((t, rng.expovariate(mu_base)))
                        next_arr = t + rng.expovariate(lam_base)
                    else:
                        break
        
        L_val = (busy_time / win_len) if win_len > 0 else 0
        W_val = (wait_time_sum / n_customers_served) if n_customers_served > 0 else 0
        bf_val = (busy_time / win_len) if win_len > 0 else 0
        pl_val = (blk_count / arr_count) if arr_count > 0 else 0
        pw_val = ((arr_count - blk_count - n_customers_served) / arr_count) if arr_count > 0 else 0
        
        per_seed_L.append(L_val)
        per_seed_W.append(W_val)
        per_seed_busy_frac.append(bf_val)
        per_seed_p_loss.append(pl_val)
        per_seed_p_wait.append(pw_val)
        
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
    
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0
    
    mean_arr = total_arr / seeds_used if seeds_used > 0 else 0
    mean_dep = total_dep / seeds_used if seeds_used > 0 else 0
    mean_blk = total_blk / seeds_used if seeds_used > 0 else 0
    dep_rate = mean_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(mean_arr, 6),
        "blk": round(mean_blk, 6),
        "busy_util": round(avg_bf, 6),
        "dep": round(mean_dep, 6),
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
    print(json.dumps(result))

if __name__ == "__main__":
    main()
