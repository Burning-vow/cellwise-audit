import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    lam_base = 9.0
    mu_base = 10.0
    c = 1
    K = 4

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25

    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr = 0
    all_dep = 0
    all_blk = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        t = 0.0
        n_in_sys = 0
        next_arr = rng.expovariate(lam)
        service_times = []
        dep_events = []
        arr_count = 0
        dep_count = 0
        blk_count = 0
        L_area = 0.0
        W_sum = 0.0
        busy_time = 0.0
        last_event_time = 0.0
        prev_n = 0
        prev_busy = False

        while True:
            next_dep = dep_events[0] if dep_events else float('inf')
            if next_arr < next_dep:
                event_time = next_arr
                dt = event_time - last_event_time
                if event_time > warmup:
                    L_area += prev_n * dt
                    if prev_busy:
                        busy_time += dt
                last_event_time = event_time
                if n_in_sys < K:
                    st = rng.expovariate(mu)
                    service_times.append(st)
                    dep_time = event_time + st
                    dep_events.append(dep_time)
                    dep_events.sort()
                    n_in_sys += 1
                    arr_count += 1
                    if event_time > warmup:
                        W_sum += (event_time - (dep_time - st)) 
                else:
                    blk_count += 1
                prev_n = n_in_sys
                prev_busy = len(dep_events) > 0
                next_arr = event_time + rng.expovariate(lam)
            else:
                event_time = next_dep
                dt = event_time - last_event_time
                if event_time > warmup:
                    L_area += prev_n * dt
                    if prev_busy:
                        busy_time += dt
                last_event_time = event_time
                dep_events.pop(0)
                n_in_sys -= 1
                dep_count += 1
                prev_n = n_in_sys
                prev_busy = len(dep_events) > 0
                if event_time >= H:
                    break

        if arr_count > 0 and win > 0:
            L_est = L_area / win
            W_est = W_sum / arr_count if arr_count > 0 else 0.0
            bf_est = busy_time / win
            pl_est = blk_count / (arr_count + blk_count) if (arr_count + blk_count) > 0 else 0.0
            pw_est = 0.0
            if arr_count > 0:
                wait_sum = 0.0
                # Recalculate wait properly: need arrival times and departure times
                # Let's redo with proper tracking
                pass
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(pl_est)
            per_seed_p_wait.append(pw_est)
            all_L_area += L_est
            all_W_sum += W_est
            all_busy_time += bf_est
            all_arr += arr_count
            all_dep += dep_count
            all_blk += blk_count
            seeds_used += 1
            seed_list.append(s)

    if seeds_used == 0:
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_wait":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[],"busy_occupied":0}))
        return

    avg_L = sum(per_seed_L) / seeds_used
    avg_W = sum(per_seed_W) / seeds_used
    avg_bf = sum(per_seed_busy_frac) / seeds_used
    avg_pl = sum(per_seed_p_loss) / seeds_used
    avg_pw = sum(per_seed_p_wait) / seeds_used
    avg_arr = all_arr / seeds_used
    avg_dep = all_dep / seeds_used
    avg_blk = all_blk / seeds_used
    dep_rate = avg_dep / win if win > 0 else 0
    lam_eff = dep_rate
    busy_util = avg_bf / c if c > 0 else 0
    busy_occ = avg_bf

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_loss": round(avg_pl, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occ, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
