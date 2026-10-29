import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 8.0
    mu_base = 60.0 / 6.0
    c = 1

    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        mu = mu_base * 1.1
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        service_times = {}
        server_free_time = 0.0
        num_in_system = 0
        last_event_time = 0.0
        area_L = 0.0
        total_wait_area = 0.0
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        busy_time_in_win = 0.0
        occupied_time_in_win = 0.0
        wait_count_in_win = 0
        loss_count_in_win = 0
        customer_id_counter = 0
        customers_waiting = 0
        customers_serving = 0

        while t < horizon:
            arr_t = next_arrival
            dep_t = float('inf')
            if queue or (customers_serving > 0 and server_free_time > t):
                dep_t = server_free_time

            if arr_t <= dep_t:
                dt = arr_t - t
                if t >= win_start:
                    area_L += num_in_system * dt
                    if num_in_system > 0:
                        busy_time_in_win += dt
                    if customers_serving > 0:
                        occupied_time_in_win += dt
                t = arr_t
                next_arrival = t + rng.expovariate(lam)
                cid = customer_id_counter
                customer_id_counter += 1
                svc = rng.expovariate(mu)
                service_times[cid] = svc
                if customers_serving < c:
                    customers_serving += 1
                    server_free_time = max(t, server_free_time) + svc
                    num_in_system += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                else:
                    queue.append(cid)
                    num_in_system += 1
                    customers_waiting += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                        blocked_in_win += 1
                        loss_count_in_win += 1
            else:
                dt = dep_t - t
                if t >= win_start:
                    area_L += num_in_system * dt
                    if num_in_system > 0:
                        busy_time_in_win += dt
                    if customers_serving > 0:
                        occupied_time_in_win += dt
                t = dep_t
                if queue:
                    next_cid = queue.pop(0)
                    customers_waiting -= 1
                    svc = service_times[next_cid]
                    server_free_time = t + svc
                    num_in_system -= 1
                    if t >= win_start:
                        departures_in_win += 1
                        total_wait_area += (t - (server_free_time - svc)) if False else 0
                else:
                    if customers_serving > 0:
                        customers_serving -= 1
                        num_in_system -= 1
                        if t >= win_start:
                            departures_in_win += 1

        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = (area_L / departures_in_win) if departures_in_win > 0 else 0.0
        busy_frac_est = busy_time_in_win / win_len if win_len > 0 else 0.0
        p_wait_est = (blocked_in_win / arrivals_in_win) if arrivals_in_win > 0 else 0.0
        busy_util_est = busy_time_in_win / (win_len * c) if win_len > 0 else 0.0
        busy_occupied_est = occupied_time_in_win / win_len if win_len > 0 else 0.0
        dep_rate_est = departures_in_win / win_len if win_len > 0 else 0.0
        lam_eff_est = dep_rate_est
        p_loss_est = blocked_in_win / arrivals_in_win if arrivals_in_win > 0 else 0.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals_in_win)
        all_dep.append(departures_in_win)
        all_blk.append(blocked_in_win)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occupied_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)

    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
    avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0.0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
