import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0
    mu_base = 60.0 / 6.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    elif a.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        t = 0.0
        N = 0
        next_arr = rng.expovariate(lam)
        service_times = {}
        next_dep = float('inf')
        
        area_N = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_W = 0
        
        while t < horizon:
            if next_arr <= next_dep:
                dt = next_arr - t
                if t >= win_start:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_arr
                N += 1
                count_arr += 1
                st = rng.expovariate(mu)
                service_times[N] = (t, st)
                if N == 1:
                    next_dep = t + st
            else:
                dt = next_dep - t
                if t >= win_start:
                    area_N += N * dt
                    if N > 0:
                        area_busy += dt
                t = next_dep
                if N > 0:
                    arr_t, _ = service_times.pop(N)
                    W_val = t - arr_t
                    if t >= win_start:
                        sum_W += W_val
                        count_W += 1
                    N -= 1
                    count_dep += 1
                    if N > 0:
                        next_dep = t + service_times[N][1]
                    else:
                        next_dep = float('inf')
        
        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = sum_W / count_W if count_W > 0 else 0.0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0.0
        p_wait_est = busy_frac_est
        
        arr_est = count_arr / seeds_used if seeds_used > 0 else 0.0
        dep_est = count_dep / seeds_used if seeds_used > 0 else 0.0
        blk_est = count_blk / seeds_used if seeds_used > 0 else 0.0
        
        busy_util_est = busy_frac_est
        busy_occ_est = busy_frac_est
        lam_eff_est = dep_est / win_len * 60.0 if win_len > 0 else 0.0
        p_loss_est = 0.0
        dep_rate_est = dep_est / win_len * 60.0 if win_len > 0 else 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_est)
        all_dep.append(dep_est)
        all_blk.append(blk_est)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        all_dep_rate.append(dep_rate_est)
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
    
    def mean(lst): return sum(lst)/len(lst) if lst else 0.0
    
    result = {
        "L": round(mean(all_L), 6),
        "W": round(mean(all_W), 6),
        "busy_frac": round(mean(all_busy_frac), 6),
        "p_wait": round(mean(all_p_wait), 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(mean(all_arr), 6),
        "blk": round(mean(all_blk), 6),
        "busy_util": round(mean(all_busy_util), 6),
        "dep": round(mean(all_dep), 6),
        "dep_rate": round(mean(all_dep_rate), 6),
        "lam_eff": round(mean(all_lam_eff), 6),
        "p_loss": round(mean(all_p_loss), 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
