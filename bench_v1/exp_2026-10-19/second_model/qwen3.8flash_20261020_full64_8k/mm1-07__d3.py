import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 8.0
    mu_base = 10.0
    c = 1
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start

    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        c = 2
    else:
        lam = lam_base
        mu = mu_base

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

    for s_idx in range(seeds_used):
        rng = random.Random(seed_list[s_idx])
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = None
        n_in_sys = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_area = 0.0
        sys_time_sum = 0.0
        busy_time = 0.0
        last_event_t = 0.0
        prev_n = 0
        area_L = 0.0
        area_busy = 0.0
        area_occ = 0.0
        events = []

        while t < horizon:
            if next_arr is not None and (service_end is None or next_arr <= service_end):
                t_new = next_arr
                dt = t_new - t
                if t >= win_start:
                    area_L += prev_n * dt
                    area_busy += min(prev_n, c) * dt
                    area_occ += (1 if prev_n > 0 else 0) * dt
                t = t_new
                if len(queue) + (1 if service_end is not None else 0) < c:
                    svc_time = rng.expovariate(mu)
                    queue.append((t, svc_time))
                    arr_count += 1
                    if service_end is None:
                        cust = queue.pop(0)
                        service_end = t + cust[1]
                        n_in_sys = 1
                        prev_n = 1
                    else:
                        n_in_sys += 1
                        prev_n = n_in_sys
                    next_arr = t + rng.expovariate(lam)
                else:
                    blk_count += 1
                    next_arr = t + rng.expovariate(lam)
            else:
                t_new = service_end
                dt = t_new - t
                if t >= win_start:
                    area_L += prev_n * dt
                    area_busy += min(prev_n, c) * dt
                    area_occ += (1 if prev_n > 0 else 0) * dt
                t = t_new
                if queue:
                    cust = queue.pop(0)
                    service_end = t + cust[1]
                    n_in_sys -= 1
                    prev_n = n_in_sys
                    dep_count += 1
                else:
                    service_end = None
                    n_in_sys = 0
                    prev_n = 0
                    dep_count += 1

        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = (area_L / dep_count) if dep_count > 0 else 0.0
        busy_frac_est = area_busy / win_len if win_len > 0 else 0.0
        p_wait_est = (arr_count - dep_count) / arr_count if arr_count > 0 else 0.0
        busy_util_est = area_busy / (win_len * c) if win_len > 0 else 0.0
        busy_occ_est = area_occ / win_len if win_len > 0 else 0.0
        dep_rate_est = dep_count / win_len if win_len > 0 else 0.0
        lam_eff_est = dep_count / win_len if win_len > 0 else 0.0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)

    avg = lambda x: sum(x)/len(x) if x else 0.0
    result = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_wait": avg(all_p_wait),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win_len,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_loss": avg(all_p_loss),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
