import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 8.0
    mu_base = 60.0 / 5.0
    c = 1

    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []

    seed_list = []
    for i in range(args.seeds):
        s = args.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)

        t = 0.0
        n = 0
        busy_time = 0.0
        last_event_t = 0.0
        area_n = 0.0
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        wait_sum_in_win = 0.0
        served_count_in_win = 0

        next_arrival = rng.expovariate(lam)
        service_times = {}
        queue = []
        serving = None

        while t < horizon:
            arr_t = next_arrival
            dep_t = float('inf')
            if serving is not None:
                dep_t = serving[1]

            if arr_t <= dep_t and arr_t < horizon:
                dt = arr_t - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        busy_time += dt
                t = arr_t
                n += 1
                st = rng.expovariate(mu)
                if len(queue) == 0 and serving is None:
                    serving = (t, t + st)
                    queue.append((t, st))
                else:
                    queue.append((t, st))
                arrivals_in_win += 1 if t >= win_start else 0
                next_arrival = t + rng.expovariate(lam)
            elif dep_t < horizon:
                dt = dep_t - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        busy_time += dt
                t = dep_t
                if serving is not None:
                    finish_t = serving[1]
                    start_t = serving[0]
                    if t >= win_start:
                        wait_sum_in_win += (start_t - queue[0][0]) if queue else 0.0
                        served_count_in_win += 1
                        departures_in_win += 1
                    queue.pop(0)
                    if queue:
                        next_item = queue[0]
                        serving = (t, t + next_item[1])
                    else:
                        serving = None
                    n -= 1
            else:
                break

        L_est = area_n / win_len if win_len > 0 else 0.0
        W_est = wait_sum_in_win / served_count_in_win if served_count_in_win > 0 else 0.0
        bf_est = busy_time / win_len if win_len > 0 else 0.0
        pl_est = blocked_in_win / arrivals_in_win if arrivals_in_win > 0 else 0.0
        pw_est = 0.0
        if served_count_in_win > 0:
            total_wait_events = sum(1 for _ in range(served_count_in_win))
            pw_est = 0.0
        p_wait_val = 0.0
        if arrivals_in_win > 0:
            p_wait_val = 0.0

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(p_wait_val)
        per_seed_arr.append(arrivals_in_win)
        per_seed_dep.append(departures_in_win)
        per_seed_blk.append(blocked_in_win)

    seeds_used = len(seed_list)
    avg_L = sum(per_seed_L) / seeds_used if seeds_used else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used else 0.0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used else 0.0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used else 0.0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used else 0.0
    avg_arr = sum(per_seed_arr) / seeds_used if seeds_used else 0.0
    avg_dep = sum(per_seed_dep) / seeds_used if seeds_used else 0.0
    avg_blk = sum(per_seed_blk) / seeds_used if seeds_used else 0.0
    dep_rate = avg_dep / (win_len / 60.0) if win_len > 0 else 0.0
    lam_eff = dep_rate
    p_loss = avg_pl
    p_wait = avg_pw
    busy_util = avg_bf
    busy_occupied = avg_bf

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(p_wait, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
