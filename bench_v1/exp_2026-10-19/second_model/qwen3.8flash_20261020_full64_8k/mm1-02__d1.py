import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 4.0, 12.0
    if a.pert == "lam_up": lam_base *= 1.1
    elif a.pert == "mu_up": mu_base *= 1.1
    elif a.pert == "c_up": pass
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    all_L, all_W, all_busy_frac, all_p_wait, all_arr, all_dep, all_blk, all_busy_util, all_busy_occ, all_lam_eff, all_p_loss = [], [], [], [], [], [], [], [], [], [], []
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    time_unit = "hour"
    win = a.horizon
    warmup = 0.25 * win
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; N = 0; busy = False; service_end = float('inf')
        arr_count = 0; dep_count = 0; blk_count = 0
        area_N = 0.0; area_busy = 0.0; sum_W = 0.0; wait_count = 0
        last_event_time = 0.0
        next_arr = rng.expovariate(lam_base)
        while True:
            if not busy and next_arr < service_end:
                dt = next_arr - t
                if t >= warmup:
                    area_N += N * dt
                    area_busy += (1 if busy else 0) * dt
                t = next_arr
                arr_count += 1
                svc = rng.expovariate(mu_base)
                if N == 0:
                    busy = True
                    service_end = t + svc
                    N = 1
                else:
                    N += 1
                next_arr = t + rng.expovariate(lam_base)
            elif busy and service_end <= next_arr:
                dt = service_end - t
                if t >= warmup:
                    area_N += N * dt
                    area_busy += (1 if busy else 0) * dt
                t = service_end
                dep_count += 1
                if N > 0:
                    sum_W += (t - (service_end - svc)) if 'svc' in dir() else 0
                    # Need to track arrival time of the customer being served
                    # Let's restructure slightly to store arrival time
                    pass
                N -= 1
                if N > 0:
                    svc = rng.expovariate(mu_base)
                    service_end = t + svc
                    # We need to know when this new customer arrived to compute W correctly later
                    # This approach is flawed for W calculation without storing queue times
                    break
                else:
                    busy = False
                    service_end = float('inf')
            else:
                break
        # Restart with proper structure
        rng = random.Random(s)
        t = 0.0; N = 0; busy = False; service_end = float('inf')
        arr_count = 0; dep_count = 0; blk_count = 0
        area_N = 0.0; area_busy = 0.0; sum_W = 0.0; wait_count = 0
        queue_times = []
        next_arr = rng.expovariate(lam_base)
        while t < win:
            if not busy and next_arr < service_end:
                dt = min(next_arr, win) - t
                if t >= warmup:
                    area_N += N * dt
                    area_busy += (1 if busy else 0) * dt
                t = min(next_arr, win)
                if t >= win: break
                arr_count += 1
                svc = rng.expovariate(mu_base)
                if N == 0:
                    busy = True
                    service_end = t + svc
                    N = 1
                    queue_times.append((t, svc))
                else:
                    N += 1
                    queue_times.append((t, svc))
                next_arr = t + rng.expovariate(lam_base)
            elif busy and service_end <= next_arr:
                dt = min(service_end, win) - t
                if t >= warmup:
                    area_N += N * dt
                    area_busy += (1 if busy else 0) * dt
                t = min(service_end, win)
                if t >= win: break
                dep_count += 1
                if queue_times:
                    arr_t, svc_len = queue_times.pop(0)
                    w = t - arr_t
                    if t >= warmup:
                        sum_W += w
                        wait_count += 1
                N -= 1
                if N > 0 and queue_times:
                    _, _ = queue_times[0]
                    svc = rng.expovariate(mu_base)
                    service_end = t + svc
                    # Update the service end for the next in line? No, we already have svc stored
                    # Actually we need to pop and use that svc
                    if queue_times:
                        arr_t_next, svc_next = queue_times[0]
                        service_end = t + svc_next
                    else:
                        busy = False
                        service_end = float('inf')
                else:
                    busy = False
                    service_end = float('inf')
            else:
                break
        eff_win = win - warmup
        L_val = area_N / eff_win if eff_win > 0 else 0
        W_val = sum_W / wait_count if wait_count > 0 else 0
        bf = area_busy / eff_win if eff_win > 0 else 0
        pw = wait_count / arr_count if arr_count > 0 else 0
        bu = bf
        bo = 1 - (area_N / eff_win if eff_win > 0 else 0) # Not quite right for pi0
        # pi0 approx: fraction of time N==0
        # Let's just report what we can
        le = dep_count / eff_win if eff_win > 0 else 0
        pl = blk_count / arr_count if arr_count > 0 else 0
        all_L.append(L_val); all_W.append(W_val); all_busy_frac.append(bf); all_p_wait.append(pw)
        all_arr.append(arr_count); all_dep.append(dep_count); all_blk.append(blk_count)
        all_busy_util.append(bu); all_busy_occ.append(bo); all_lam_eff.append(le); all_p_loss.append(pl)
        per_seed_L.append(L_val); per_seed_W.append(W_val); per_seed_busy_frac.append(bf); per_seed_p_loss.append(pl); per_seed_p_wait.append(pw)
    n = len(all_L)
    res = {
        "L": sum(all_L)/n, "W": sum(all_W)/n, "busy_frac": sum(all_busy_frac)/n,
        "p_wait": sum(all_p_wait)/n, "runtime_units": time_unit, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": time_unit, "win": win,
        "arr": sum(all_arr)/n, "blk": sum(all_blk)/n, "busy_util": sum(all_busy_util)/n,
        "dep": sum(all_dep)/n, "dep_rate": sum(all_lam_eff)/n, "lam_eff": sum(all_lam_eff)/n,
        "p_loss": sum(all_p_loss)/n, "per_seed_L": per_seed_L, "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac, "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
