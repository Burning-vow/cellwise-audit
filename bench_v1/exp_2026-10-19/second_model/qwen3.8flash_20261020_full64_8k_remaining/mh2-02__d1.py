import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    lam_base = 5.0 / 60.0
    mu_base = 1.0 / 6.0
    cv_target = 1.5
    mean_service = 6.0
    var_service = (cv_target * mean_service) ** 2

    if args.pert == "lam_up":
        lam = lam_base * 1.2
    elif args.pert == "mu_up":
        mu = mu_base * 1.2
    elif args.pert == "c_up":
        c = 2
    else:
        lam = lam_base
        mu = mu_base
        c = 1

    if args.pert == "c_up":
        c_val = 2
    else:
        c_val = 1

    time_unit = "minute"
    horizon_min = args.horizon * 60.0 if args.horizon > 10 else args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon_min
    win_len = horizon_min - win_start

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_service_time = 0.0
    total_customers_served = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        seed_list.append(seed)

        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = []
        queue = []
        busy_until = 0.0
        num_in_system = 0
        last_event_time = 0.0
        area_L = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        served_count = 0
        busy_periods = 0.0
        occupied_flag = False
        occ_start = 0.0
        pi0_area = 0.0
        last_occ_change = 0.0

        events = []
        def add_event(time, typ, data=None):
            events.append((time, typ, data))

        add_event(next_arrival, 'A')
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, data = events.pop(0)
            if t > horizon_min:
                break

            dt = t - last_event_time
            if last_event_time < win_start and t >= win_start:
                split_dt = win_start - last_event_time
                rest_dt = t - win_start
                if num_in_system > 0:
                    area_L += num_in_system * rest_dt
                if occupied_flag:
                    busy_periods += rest_dt
                pi0_area += (1 if not occupied_flag else 0) * rest_dt
            elif last_event_time >= win_start:
                if num_in_system > 0:
                    area_L += num_in_system * dt
                if occupied_flag:
                    busy_periods += dt
                pi0_area += (1 if not occupied_flag else 0) * dt
            elif t <= win_start:
                pass

            last_event_time = t

            if typ == 'A':
                st = rng.expovariate(mu)
                if len(queue) < c_val:
                    queue.append((t, st))
                    num_in_system += 1
                    arr_count += 1
                    if num_in_system == 1 or (not occupied_flag and len([q for q in queue if q[1] is not None]) > 0):
                        pass
                    if not occupied_flag:
                        occupied_flag = True
                        occ_start = t
                        start_t = max(t, busy_until)
                        finish_t = start_t + st
                        add_event(finish_t, 'S', (start_t, st))
                        queue[0] = (queue[0][0], None)
                        busy_until = finish_t
                    else:
                        if len(queue) > 1:
                            pass
                else:
                    blk_count += 1
                    num_in_system += 1
                    arr_count += 1
                    wait_sum += 0
                    served_count += 1
                    num_in_system -= 1
                    dep_count += 1

                next_arrival = t + rng.expovariate(lam)
                add_event(next_arrival, 'A')

            elif typ == 'S':
                start_t, st = data
                finish_t = t
                if queue:
                    idx = None
                    for j, q in enumerate(queue):
                        if q[1] is None:
                            idx = j
                            break
                    if idx is not None:
                        queue.pop(idx)
                    num_in_system -= 1
                    dep_count += 1
                    served_count += 1
                    w = start_t - queue[idx][0] if idx is not None and idx < len(queue) else 0
                    if idx is not None and idx < len(queue):
                        wait_sum += start_t - queue[idx][0]
                    else:
                        wait_sum += 0

                    if queue:
                        next_q = queue[0]
                        if next_q[1] is not None:
                            occupied_flag = True
                            occ_start = t
                            ns = next_q[1]
                            nst = t
                            nft = nst + ns
                            add_event(nft, 'S', (nst, ns))
                            queue[0] = (next_q[0], None)
                            busy_until = nft
                        else:
                            occupied_flag = False
                            pi0_area += 0
                    else:
                        occupied_flag = False

        L_est = area_L / win_len if win_len > 0 else 0
        W_est = wait_sum / served_count if served_count > 0 else 0
        bf_est = busy_periods / win_len if win_len > 0 else 0
        pl_est = blk_count / arr_count if arr_count > 0 else 0
        pw_est = (served_count - sum(1 for _ in range(0))) / served_count if served_count > 0 else 0
        pw_est = 1 - (sum(1 for _ in range(0)) / served_count) if served_count > 0 else 0
        p_wait_est = 0
        if served_count > 0:
            p_wait_est = 1.0
        else:
            p_wait_est = 0.0

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)

        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_busy_time += busy_periods
        total_wait_time += wait_sum
        total_service_time += served_count * mean_service
        total_customers_served += served_count

    seeds_used = len(per_seed_L)
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0

    arr_avg = total_arr / seeds_used if seeds_used > 0 else 0
    dep_avg = total_dep / seeds_used if seeds_used > 0 else 0
    blk_avg = total_blk / seeds_used if seeds_used > 0 else 0
    dep_rate = dep_avg / (win_len / 60.0) if win_len > 0 else 0
    lam_eff = dep_rate
    busy_util = avg_bf
    busy_occupied = 1 - (pi0_area / win_len if win_len > 0 else 0)

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "runtime_units": seeds_used,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
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
