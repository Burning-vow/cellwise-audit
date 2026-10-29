import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 8.0
    mu_base = 12.0
    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        mu = mu_base * 1.1
    else:
        lam = lam_base
        mu = mu_base

    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_customers = 0

    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {}
        queue = []
        server_free_at = 0.0
        n_in_system = 0
        last_event_time = 0.0
        area_n = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        custs_in_window = 0
        time_in_sys_sum = 0.0

        while t < horizon:
            if not queue and (t >= server_free_at or next_arrival > horizon):
                break
            next_departure = float('inf')
            if queue:
                next_departure = server_free_at
            elif t < server_free_at:
                next_departure = server_free_at

            if next_arrival <= next_departure:
                dt = next_arrival - t
                if t < win_start:
                    pass
                else:
                    area_n += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_arrival
                st = rng.expovariate(mu)
                service_times[arr_count] = st
                if n_in_system == 0:
                    server_free_at = t + st
                    queue.append((arr_count, t))
                    n_in_system += 1
                    arr_count += 1
                else:
                    queue.append((arr_count, t))
                    n_in_system += 1
                    arr_count += 1
            else:
                dt = next_departure - t
                if t < win_start:
                    pass
                else:
                    area_n += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_departure
                if queue:
                    cid, arrival_t = queue.pop(0)
                    n_in_system -= 1
                    dep_count += 1
                    if arrival_t >= win_start:
                        time_in_sys_sum += (t - arrival_t)
                        wait_time_sum += max(0.0, t - arrival_t - service_times[cid])
                        custs_in_window += 1
                    if queue:
                        server_free_at = t + service_times[queue[0][0]]
                    else:
                        server_free_at = t
                else:
                    server_free_at = t

        if t < horizon:
            dt = horizon - t
            if t < win_start:
                pass
            else:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    busy_time += dt

        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = time_in_sys_sum / custs_in_window if custs_in_window > 0 else 0.0
        bf_est = busy_time / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = wait_time_sum / custs_in_window if custs_in_window > 0 else 0.0

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)

        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_time_in_sys += time_in_sys_sum
        total_busy_time += busy_time
        total_wait_time += wait_time_sum
        total_customers += custs_in_window

    avg_L = sum(per_seed_L) / len(per_seed_L) if per_seed_L else 0.0
    avg_W = sum(per_seed_W) / len(per_seed_W) if per_seed_W else 0.0
    avg_bf = sum(per_seed_busy_frac) / len(per_seed_busy_frac) if per_seed_busy_frac else 0.0
    avg_pl = sum(per_seed_p_loss) / len(per_seed_p_loss) if per_seed_p_loss else 0.0
    avg_pw = sum(per_seed_p_wait) / len(per_seed_p_wait) if per_seed_p_wait else 0.0

    arr_avg = total_arr / seeds_used if seeds_used > 0 else 0.0
    dep_avg = total_dep / seeds_used if seeds_used > 0 else 0.0
    blk_avg = total_blk / seeds_used if seeds_used > 0 else 0.0
    dep_rate = dep_avg / win_len * 60.0 if win_len > 0 else 0.0
    lam_eff = dep_avg / win_len * 60.0 if win_len > 0 else 0.0
    busy_util = avg_bf
    busy_occupied = avg_bf

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
